"""P1 (analysis/scaling/README): where a searched decision's time goes. cProfile over `act` on 10 decision points per
agent (fresh agent per point, search seed SEED + k), then every function's own time is attributed to the nearest
caller that belongs to a block (gprof-style: split by the own time on each caller edge). Blocks: state copy,
determinization, rules step, legal moves, net encoding, net forward, MCTS bookkeeping, linear evaluation, other.
Also times the same decisions without the profiler. Condition: the opponent's deck list is known (order and hand not).
Run from (and with PYTHONPATH =) the checkout.

    python3 p1_profile.py --rec REC --seed 73800000 --n 10 --spec SPEC --label NAME --out p1_NAME.json
"""
import argparse, cProfile, json, pstats, sys, time
from collections import defaultdict
sys.path.insert(0, "/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d5")
from d5_agree import decisions

BLOCKS = ["state copy", "determinization", "rules step", "legal moves", "net encoding", "net forward",
          "MCTS bookkeeping", "linear evaluation", "other"]


def entry(fn):
    """The block a function opens, or None (it takes its callers' block)."""
    path, _, name = fn
    p = path.replace("\\", "/")
    if p.endswith("svsim/core/state.py") and name in ("clone", "copy"):
        return "state copy"
    if p.endswith("svsim/core/view.py") and name in ("determinize",):
        return "determinization"
    if p.endswith("svsim/core/engine.py") and name == "apply":
        return "rules step"
    if p.endswith("svsim/search/mcts.py") and name == "_step":
        return "rules step"
    if p.endswith("svsim/core/engine.py") and name == "legal_actions":
        return "legal moves"
    if p.endswith("svsim/learn/tokens.py"):
        return "net encoding"
    if p.endswith("svsim/learn/setnet.py"):
        return "net forward"
    if p.endswith("svsim/search/mcts.py"):
        return "MCTS bookkeeping"
    if p.endswith(("svsim/learn/phased.py", "svsim/learn/model.py")) or (p.endswith("svsim/search/evaluate.py") and name != "after_end_of_turn"):
        return "linear evaluation"
    return None


def attribute(stats):
    st = stats.stats
    ctx = {}
    for fn in st:
        e = entry(fn)
        ctx[fn] = {e: 1.0} if e else {"other": 1.0}
    for _ in range(200):
        changed = 0.0
        for fn, (cc, nc, tt, ct, callers) in st.items():
            if entry(fn):
                continue
            w = {}
            tot = 0.0
            for g, edge in callers.items():
                if g not in ctx:
                    continue
                x = edge[2] if edge[2] > 0 else 1e-12 * edge[1]
                tot += x
                for b, v in ctx[g].items():
                    w[b] = w.get(b, 0.0) + x * v
            if tot <= 0:
                continue
            new = {b: v / tot for b, v in w.items()}
            changed += sum(abs(new.get(b, 0) - ctx[fn].get(b, 0)) for b in set(new) | set(ctx[fn]))
            ctx[fn] = new
        if changed < 1e-9:
            break
    blocks = defaultdict(float)
    top = defaultdict(list)
    for fn, (cc, nc, tt, ct, callers) in st.items():
        for b, v in ctx[fn].items():
            if v * tt > 0:
                blocks[b] += v * tt
                top[b].append((v * tt, nc, f"{fn[0].split('svsim/')[-1] if 'svsim/' in fn[0] else fn[0].split('/')[-1]}:{fn[1]}({fn[2]})"))
    # "other" by module: every svsim function stands for its own file, anything else takes its callers' files
    def mod(fn):
        return fn[0].split("svsim/")[-1] if "svsim/" in fn[0] else None
    mctx = {fn: ({mod(fn): 1.0} if mod(fn) else {"(builtin)": 1.0}) for fn in st}
    for _ in range(200):
        for fn, (cc, nc, tt, ct, callers) in st.items():
            if mod(fn):
                continue
            w, tot = {}, 0.0
            for g, edge in callers.items():
                x = edge[2] if edge[2] > 0 else 1e-12 * edge[1]
                tot += x
                for m, v in mctx[g].items():
                    w[m] = w.get(m, 0.0) + x * v
            if tot > 0:
                mctx[fn] = {m: v / tot for m, v in w.items()}
    other_mod = defaultdict(float)
    for fn, (cc, nc, tt, ct, callers) in st.items():
        o = ctx[fn].get("other", 0.0) * tt
        for m, v in mctx[fn].items():
            other_mod[m] += o * v
    total = sum(blocks.values())
    out = {"_other_by_module": {m: round(t / total, 4) for m, t in sorted(other_mod.items(), key=lambda kv: -kv[1])[:8]}}
    for b in BLOCKS:
        t = blocks.get(b, 0.0)
        out[b] = {"seconds": round(t, 4), "share": round(t / total, 4) if total else 0,
                  "top": [{"fn": name, "seconds": round(s, 4), "calls": n} for s, n, name in sorted(top[b], reverse=True)[:5]]}
    return total, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    dec = decisions(args.rec, args.seed, args.n)
    plain = []
    for k, (g, i, state) in enumerate(dec):                   # unprofiled timing first (also warms caches)
        s = state.clone(); legal = legal_actions(s)
        a = make_agent(args.spec, args.seed + k)
        t0 = time.process_time(); a.act(s, legal); plain.append(time.process_time() - t0)
    prof = cProfile.Profile()
    for k, (g, i, state) in enumerate(dec):
        s = state.clone(); legal = legal_actions(s)
        a = make_agent(args.spec, args.seed + k)
        prof.enable(); a.act(s, legal); prof.disable()
    total, blocks = attribute(pstats.Stats(prof))
    sim = sum(blocks[b]["share"] for b in ("state copy", "determinization", "rules step", "legal moves"))
    rep = {"label": args.label, "spec": args.spec, "rec": args.rec, "seed": args.seed,
           "points": [(g, i) for g, i, _ in dec], "plain_cpu_s": [round(x, 4) for x in plain],
           "plain_ms_per_decision": round(1000 * sum(plain) / len(plain), 1), "profiled_s": round(total, 3),
           "simulator_share": round(sim, 4), "blocks": blocks, "condition": "对手卡表已知（牌序、手牌未知）"}
    json.dump(rep, open(args.out, "w"), indent=1, ensure_ascii=False)
    print(args.label, "plain ms/decision", rep["plain_ms_per_decision"], "simulator share", rep["simulator_share"])
    for b in BLOCKS:
        print(f"  {b:18s} {100 * blocks[b]['share']:5.1f}%  " + "; ".join(f"{t['fn']} {t['seconds']:.3f}s x{t['calls']}" for t in blocks[b]["top"][:3]))
    print("  other by module:", blocks["_other_by_module"])


if __name__ == "__main__":
    main()
