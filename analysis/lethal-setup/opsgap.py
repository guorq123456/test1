"""Do the new evaluators play Salem's positions more like him (README-opsgap.md)? On the ranking set's 33 starts, three
settings at the max budget each play the turn on 8 seeds; every turn end (and Salem's) is scored by M4's G_end
(default direction, mcts:100 both sides, K = 32, one seed set per start), identical ends scored once.
Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host opsgap run <stage-0 dir> --out opsgap/rows.jsonl --workers 3
    python opsgap.py read opsgap/rows.jsonl --out opsgap/read.txt
"""
import argparse
import json
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))
import setup_prob as SP          # noqa: E402
import turn_level as TL          # noqa: E402

SETTINGS = (("installed", "mcts:1043+plan+learned+phased"),
            ("kc", "mcts:997+plan+learned+phased=cand-kc-ramp-ramp"),
            ("nl", "mcts:913+plan+learned+phased=cand-nl-ramp-ramp"))
PLAYOUT = "mcts:100+plan+learned+phased"
TURN_BANK, END_BANK, SEEDS, K = 67900000, 67950000, 8, 32
PUZZLES = (329, 455, 518, 445)


def _starts():
    rows = SP._lines(os.path.join(HERE, "ranking", "rows.jsonl"))
    return [r for r in rows if abs(r["g_salem"] - r["g_bot"]) >= 0.10 - 1e-12]


def _turn(job):
    from svsim.core.engine import apply, legal_actions
    from svsim.search.lethal import state_key
    from svsim.tools.arena import make_agent
    k, st_row, name, spec, seed = job
    state, _ = TL._start_state(st_row)
    me, s, agent, n = state.active, state.clone(), make_agent(spec, seed), 0
    while not s.over and s.active == me and n < 300:
        apply(s, agent.act(s, legal_actions(s)))
        n += 1
    return k, name, seed, state_key(s), s


def _gend(job):
    from svsim.search.foresight import direction_rollout
    k, key, end, seed, kk = job
    out = direction_rollout(end, direction="default", k=kk, seed=seed, opp_spec=PLAYOUT, our_spec=PLAYOUT)["default"]
    return k, key, out["samples"]


def run(args):
    from multiprocessing import Pool
    import direction
    from svsim.search.lethal import state_key
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    TL.REC.update(recs)
    starts = _starts()
    st_rows = {st["k"]: st for st in direction._m3_starts(args.step0)[0]}
    only = set(args.ks) if args.ks else None
    starts = [r for r in starts if only is None or r["k"] in only]
    seeds = args.seeds or SEEDS
    turn_bank, end_bank, kk = (99800000, 99850000, 4) if args.smoke else (TURN_BANK, END_BANK, K)
    jobs = [(r["k"], st_rows[r["k"]], name, spec, turn_bank + 100 * r["i"] + j)
            for r in starts for name, spec in SETTINGS for j in range(seeds)]
    with Pool(args.workers, initializer=SP._init, initargs=(recs,)) as pool:
        turns = pool.map(_turn, jobs, chunksize=1)
        # state_key gives frozensets (no JSON, and their printed order depends on the process's hash seed): each
        # start's distinct turn ends get numbers here, by equality in this process
        ends, ids, rows = {}, {}, []

        def number(k, key, end):
            if (k, key) not in ids:
                ids[(k, key)] = sum(1 for kk_ in ids if kk_[0] == k)
                ends[(k, ids[(k, key)])] = end
            return ids[(k, key)]
        for r in starts:
            state, rec = TL._start_state(st_rows[r["k"]])
            status, salem_end = SP.turn_end(state, TL._salem_turn(rec, st_rows[r["k"]]["at"]))
            rows.append({"turn": True, "k": r["k"], "setting": "salem", "seed": None,
                         "key": number(r["k"], state_key(salem_end), salem_end)})
        for k, name, seed, key, end in turns:
            rows.append({"turn": True, "k": k, "setting": name, "seed": seed, "key": number(k, key, end)})
        i_of = {r["k"]: r["i"] for r in starts}
        gjobs = [(k, key, end, end_bank + 500 * i_of[k], kk) for (k, key), end in ends.items()]
        print(f"{len(turns)} 个回合，去重后 {len(gjobs)} 个回合末要打到终局（K = {kk}）", flush=True)
        gends = pool.map(_gend, gjobs, chunksize=1)
    with open(args.out, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
        for k, key, samples in gends:
            fh.write(json.dumps({"gend": True, "k": k, "key": key, "samples": samples}) + "\n")
    print(f"写进了 {args.out}")


def add(args):
    """One more setting on the same starts and seeds (README-sp.md's second read): its turns, Salem's end recomputed
    here to share his number, new ends numbered from 1000 per start and played out with the same per-start seeds
    (an end identical to an earlier setting's gets the same samples again: the playout depends only on the end and
    the seed)."""
    from multiprocessing import Pool
    import direction
    from svsim.search.lethal import state_key
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    TL.REC.update(recs)
    old = SP._lines(args.rows)
    salem_id = {r["k"]: r["key"] for r in old if r.get("turn") and r["setting"] == "salem"}
    starts = [r for r in _starts() if r["k"] in salem_id]
    st_rows = {st["k"]: st for st in direction._m3_starts(args.step0)[0]}
    jobs = [(r["k"], st_rows[r["k"]], args.name, args.spec, TURN_BANK + 100 * r["i"] + j)
            for r in starts for j in range(SEEDS)]
    with Pool(args.workers, initializer=SP._init, initargs=(recs,)) as pool:
        turns = pool.map(_turn, jobs, chunksize=1)
        salem_key = {}
        for r in starts:
            state, rec = TL._start_state(st_rows[r["k"]])
            status, end = SP.turn_end(state, TL._salem_turn(rec, st_rows[r["k"]]["at"]))
            salem_key[r["k"]] = state_key(end)
        ids, ends, rows = {}, {}, []
        for k, name, seed, key, end in turns:
            if key == salem_key[k]:
                kid = salem_id[k]
            else:
                if (k, key) not in ids:
                    ids[(k, key)] = 1000 + sum(1 for x in ids if x[0] == k)
                    ends[(k, ids[(k, key)])] = end
                kid = ids[(k, key)]
            rows.append({"turn": True, "k": k, "setting": name, "seed": seed, "key": kid})
        i_of = {r["k"]: r["i"] for r in starts}
        gjobs = [(k, kid, end, END_BANK + 500 * i_of[k], K) for (k, kid), end in ends.items()]
        print(f"{len(turns)} 个回合，新的回合末 {len(gjobs)} 个要打到终局（K = {K}）", flush=True)
        gends = pool.map(_gend, gjobs, chunksize=1)
    with open(args.out, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
        for k, kid, samples in gends:
            fh.write(json.dumps({"gend": True, "k": k, "key": kid, "samples": samples}) + "\n")
    print(f"写进了 {args.out}")


def read(args):
    rows = [r for path in args.rows for r in SP._lines(path)]
    g = {(r["k"], r["key"]): sum(r["samples"]) / len(r["samples"]) for r in rows if r.get("gend")}
    turns = [r for r in rows if r.get("turn")]
    ks = sorted({r["k"] for r in turns})
    salem = {r["k"]: r["key"] for r in turns if r["setting"] == "salem"}
    names = [n for n, _ in SETTINGS] + sorted({r["setting"] for r in turns} - {n for n, _ in SETTINGS} - {"salem"})
    val = {n: {k: [g[(k, r["key"])] for r in turns if r["k"] == k and r["setting"] == n] for k in ks} for n in names}
    per = {n: {k: sum(v) / len(v) for k, v in val[n].items()} for n in names}
    per["salem"] = {k: g[(k, salem[k])] for k in ks}
    mean = {n: sum(per[n].values()) / len(ks) for n in per}
    same = {n: sum(r["key"] == salem[r["k"]] for r in turns if r["setting"] == n) /
            sum(1 for r in turns if r["setting"] == n) for n in names}
    rng = random.Random(0)
    picks = [[ks[rng.randrange(len(ks))] for _ in ks] for _ in range(2000)]

    def diff(a, b):
        d = sum(per[a][k] - per[b][k] for k in ks) / len(ks)
        bs = sorted(sum(per[a][k] - per[b][k] for k in p) / len(p) for p in picks)
        return d, bs[49], bs[1949]
    gap = {n: mean["salem"] - mean[n] for n in names}
    out = ["条件：对手卡表已知（牌序、手牌未知）。新评估器在 Salem 局面上的运营（README-opsgap.md）\n",
           f"- 开头 {len(ks)} 个；每个设置 {sum(1 for r in turns if r['setting'] == names[0])} 次回合末；"
           f"去重后打到终局的回合末 {len(g)} 个（每个 K = {len(next(iter(r['samples'] for r in rows if r.get('gend'))))}）\n",
           "| 设置 | 平均 G_end | 和 Salem 的差距 | 比现装缩小 | 和 Salem 回合末一样 |", "|---|---|---|---|---|",
           f"| Salem 的回合末 | {mean['salem']:.3f} | — | — | — |"]
    for n in names:
        shrink = "—" if n == "installed" else f"{(gap['installed'] - gap[n]) / gap['installed']:+.0%}" if gap["installed"] else "—"
        out.append(f"| {n} | {mean[n]:.3f} | {gap[n]:+.3f} | {shrink} | {same[n]:.1%} |")
    d1, d2 = diff("kc", "installed"), diff("nl", "kc")
    out += ["", f"- cand-kc − 现装：{d1[0]:+.3f}（按开头成对重抽 2000 次 {d1[1]:+.3f}～{d1[2]:+.3f}）；"
                f"**J67**（> 0，置信 60%）→ {'对' if d1[0] > 0 else '错'}",
            f"- cand-nl − cand-kc：{d2[0]:+.3f}（{d2[1]:+.3f}～{d2[2]:+.3f}）；**J68**（> 0，置信 40%）→ {'对' if d2[0] > 0 else '错'}",
            f"- 另：cand-nl − 现装 {diff('nl', 'installed')[0]:+.3f}；Salem − 现装 {diff('salem', 'installed')[0]:+.3f}"]
    if "sp" in names:
        d3 = diff("sp", "kc")
        out += [f"- cand-sp − cand-kc：{d3[0]:+.3f}（{d3[1]:+.3f}～{d3[2]:+.3f}）；**J77**（> 0，置信 50%）→ {'对' if d3[0] > 0 else '错'}；"
                f"cand-sp − 现装 {diff('sp', 'installed')[0]:+.3f}"]
    out += ["", "**四道题**（每个设置：8 次回合末的平均 G_end；出现最多的回合末的次数；和 Salem 的一样几次）", "",
            "| 题 | Salem | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for k in PUZZLES:
        if k not in per["salem"]:
            continue
        cells = []
        for n in names:
            keys = [r["key"] for r in turns if r["k"] == k and r["setting"] == n]
            top = Counter(keys).most_common(1)[0][1]
            cells.append(f"{per[n][k]:.3f}（最多 {top}/8，同 Salem {sum(x == salem[k] for x in keys)}/8）")
        out.append(f"| {k} | {per['salem'][k]:.3f} | " + " | ".join(cells) + " |")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=3)
    a.add_argument("--ks", type=int, nargs="*", default=None, help="only these starts (smoke)")
    a.add_argument("--seeds", type=int, default=None, help="fewer turn seeds (smoke)")
    a.add_argument("--smoke", action="store_true", help="off-bank seeds 99800000 / 99850000 and K = 4")
    a = sub.add_parser("add")
    a.add_argument("step0")
    a.add_argument("--rows", required=True, help="the first run's rows (Salem's end numbers)")
    a.add_argument("--name", required=True)
    a.add_argument("--spec", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=3)
    a = sub.add_parser("read")
    a.add_argument("rows", nargs="+")
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    {"run": run, "add": add, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
