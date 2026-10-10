"""Is the bot's resource waste a search problem or an evaluator problem? (the architecture thread 2026-10-10 06:27Z;
measurement only, nothing wired.) Condition: the opponent's deck list is known (order and hand not).

The 85 stage-0 starts of the analysis line's M3 (ca822b5: Salem's line a candidate of its own; turn-level step 0,
RC 84d735e). On each, the bot's turn is played again on the real start, as step 0 played its "bot" line
(search.candidates.play_turn with the spec's agent), by three specs at the same seeds:
level-strong (mcts:200+plan+learned+phased), mcts:1043+plan+learned+phased and mcts:3000+plan+learned+phased;
seed j of start k is 65960000 + k + 1000 j (j = 0 is step 0's own seed: level-strong there replays step 0's line).
Each turn end is read with M3's own snapshot (generic fields, analysis line's direction.py) against Salem's line,
and each line's actions are tagged with generic events (no table per card):
- evolve_no_kill: an evolution after which neither the evolve nor that follower's attacks this turn destroyed an
  enemy follower, on a turn not won (split: the follower then hit the leader / it didn't attack at all);
- overkill: attacks on a follower that died, the attack above its defense (sum, and the attacks with any);
- play_no_change: a card played that changed neither board nor either leader's defense (split: drew a card / nothing
  visible);
- counts: cards played, PP spent, evolutions, super-evolutions, attacks on the leader and on followers, enemy
  followers destroyed.
The resource gap R (Salem - line) in M3's conserve units: a card in hand, 2 PP, an EP, a SEP each count 1.

    python3 waste.py run STEP0_DIR ANA_DIR M3_ROWS --out ROWS.jsonl [--seeds 4] [--workers 3]
    python3 waste.py read ROWS.jsonl M3_ROWS
(ANA_DIR: the analysis line's analysis/ folder, with lethal-setup/, turn-level/ and card-value/.)
"""
import argparse
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

SPECS = ("level-strong", "mcts:1043+plan+learned+phased", "mcts:3000+plan+learned+phased")
SEED = 65960000
CONSERVE = (("hand", 1.0), ("pp_left", 0.5), ("ep", 1.0), ("sep", 1.0))
G = {}


def _ana(ana):
    for sub in ("lethal-setup", "turn-level", "card-value"):
        p = os.path.join(ana, sub)
        if p not in sys.path:
            sys.path.insert(0, p)


def gap(d) -> float:
    return sum(w * d[f] for f, w in CONSERVE)


def tags(state, actions) -> dict:
    """Generic events of a turn's actions on the real start (module docstring)."""
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard, from_dict
    from svsim.core.engine import apply
    s = state.clone()
    me = s.active
    t = Counter()
    evolved = {}                       # uid -> [kills, face damage, attacked]

    def board(p):
        return (tuple(sorted((c.uid, c.atk, c.life) for c in p.followers)),
                tuple(sorted(c.uid for c in p.field if c.defn.is_amulet)))

    pp0 = s.players[me].pp
    for a in actions:
        a = from_dict(a) if isinstance(a, dict) else a
        if isinstance(a, EndTurn) or s.over:
            break
        mine, theirs = s.players[me], s.players[1 - me]
        before = (board(mine), board(theirs), mine.leader_hp, theirs.leader_hp)
        hand0 = len(mine.hand)
        enemy0 = {c.uid: c.life for c in theirs.followers}
        hp0 = theirs.leader_hp
        atk = tgt_life = None
        if isinstance(a, Attack):
            att = next((c for c in mine.followers if c.uid == a.attacker), None)
            atk = att.atk if att is not None else 0
            tgt_life = enemy0.get(a.target)
        apply(s, a)
        mine, theirs = s.players[me], s.players[1 - me]
        killed = [u for u in enemy0 if u not in {c.uid for c in theirs.followers}]
        t["kills"] += len(killed)
        if isinstance(a, PlayCard):
            t["plays"] += 1
            if (board(mine), board(theirs), mine.leader_hp, theirs.leader_hp) == before:
                t["play_no_change"] += 1
                t["play_no_change_drew" if len(mine.hand) >= hand0 else "play_no_change_nothing"] += 1
        elif isinstance(a, Evolve):
            t["super_evolves" if a.super_ else "evolves"] += 1
            evolved[a.uid] = [len(killed), 0, False]
        elif isinstance(a, Attack):
            if tgt_life is None:
                t["face_attacks"] += 1
            else:
                t["follower_attacks"] += 1
                if a.target in killed and atk > tgt_life:
                    t["overkill"] += atk - tgt_life
                    t["overkill_attacks"] += 1
            if a.attacker in evolved:
                e = evolved[a.attacker]
                e[2] = True
                if tgt_life is None:
                    e[1] += max(hp0 - theirs.leader_hp, 0)
                elif a.target in killed:
                    e[0] += 1
    won = s.over and s.winner == me
    for kills, face, attacked in evolved.values():
        if kills == 0 and not won:
            t["evolve_no_kill"] += 1
            t["evolve_no_kill_face" if face > 0 else "evolve_no_kill_no_attack" if not attacked
              else "evolve_no_kill_other"] += 1
    t["pp_spent"] = pp0 - s.players[me].pp
    return dict(t)


def _init(step0, ana):
    _ana(ana)
    import setup_prob as SP
    import turn_level as TL
    TL.REC.update(TL._records(os.path.join(step0, "selfplay.jsonl")))
    starts, plans = SP._starts(step0)
    G["starts"] = {r["k"]: r for r in starts}
    G["plans"] = plans


def _canon(x):
    """state_key as a string, the same in every process (frozensets sorted)."""
    if isinstance(x, (frozenset, set)):
        return "{" + ",".join(sorted(_canon(v) for v in x)) + "}"
    if isinstance(x, (tuple, list)):
        return "(" + ",".join(_canon(v) for v in x) + ")"
    return repr(x)


def _end(state, actions):
    import direction as DR
    import setup_prob as SP
    from svsim.search.lethal import state_key
    how, s = SP.turn_end(state, actions)
    return DR.snapshot(state, actions), (_canon(state_key(s)) if how == "ended" else how)


def _salem_job(k):
    import turn_level as TL
    st = G["starts"][k]
    state, rec = TL._start_state(st)
    salem = TL._salem_turn(rec, st["at"])
    snap, key = _end(state, salem)
    return {"k": k, "spec": "salem", "j": None, "snap": snap, "key": key, "tags": tags(state, salem)}


def _job(job):
    import turn_level as TL
    from svsim.core.actions import to_dict
    from svsim.search.candidates import _agent_decider, play_turn
    k, spec, j = job
    st = G["starts"][k]
    state, _ = TL._start_state(st)
    t = time.perf_counter()
    actions, _ = play_turn(state, _agent_decider(spec, SEED + k + 1000 * j))
    ms = (time.perf_counter() - t) * 1000
    snap, key = _end(state, actions)
    row = {"k": k, "spec": spec, "j": j, "snap": snap, "key": key, "tags": tags(state, actions), "ms": round(ms),
           "actions": [to_dict(a) for a in actions]}
    if spec == "level-strong" and j == 0:
        stored = next(p for p in G["plans"][k]["plans"] if p["kind"] == "bot")["actions"]
        row["replays_step0"] = json.loads(json.dumps(row["actions"])) == stored
    return row


def run(args):
    from multiprocessing import Pool
    ks = [json.loads(x)["k"] for x in open(args.m3) if x.strip()]
    done = set()
    if os.path.exists(args.out):
        for x in open(args.out):
            if x.strip():
                r = json.loads(x)
                done.add((r["k"], r["spec"], r["j"]))
    jobs = [(k, spec, j) for spec in args.specs for j in range(args.seeds) for k in ks if (k, spec, j) not in done]
    with Pool(args.workers, initializer=_init, initargs=(args.step0, args.ana)) as pool, \
            open(args.out, "a", encoding="utf-8") as fh:
        for r in pool.imap_unordered(_salem_job, [k for k in ks if (k, "salem", None) not in done]):
            fh.write(json.dumps(r) + "\n")
        fh.flush()
        for n, r in enumerate(pool.imap_unordered(_job, jobs), 1):
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(f"{n}/{len(jobs)}", flush=True)


def read(args):
    import direction as DR
    rows = [json.loads(x) for x in open(args.rows) if x.strip()]
    m3 = {r["k"]: r for r in (json.loads(x) for x in open(args.m3) if x.strip())}
    salem = {r["k"]: r for r in rows if r["spec"] == "salem"}
    lines = defaultdict(list)                   # (k, spec) -> rows by seed
    for r in rows:
        if r["spec"] != "salem":
            lines[(r["k"], r["spec"])].append(r)
    specs = [s for s in SPECS if any(sp == s for _, sp in lines)]
    ks = sorted(m3)
    mean = statistics.mean

    def diff(k, r):
        a, b = salem[k]["snap"], r["snap"]
        return {f: a[f] - b[f] for f in DR.FIELDS}

    per = {}                                    # (k, spec) -> seed-mean of R, diffs, tags, same end, conserve hit
    for (k, spec), rs in lines.items():
        ds = [diff(k, r) for r in rs]
        per[(k, spec)] = {
            "R": mean(gap(d) for d in ds),
            "d": {f: mean(d[f] for d in ds) for f in DR.FIELDS},
            "same": mean(float(r["key"] == salem[k]["key"]) for r in rs),
            "conserve": mean(float("conserve" in DR.classify(d)[1]) for d in ds),
            "tags": {t: mean(r["tags"].get(t, 0) for r in rs) for t in TAGS},
            "ms": mean(r["ms"] for r in rs), "n": len(rs)}
    print("条件：对手卡表已知（牌序、手牌未知）。资源浪费：搜索还是评估（测量，不接线）\n")
    rep = [r for r in rows if "replays_step0" in r]
    print(f"- 核对：level-strong 用第 0 步的种子（j = 0）重打，{sum(r['replays_step0'] for r in rep)}/{len(rep)} "
          f"个开头和第 0 步存下的 bot 线逐步相同")
    print(f"- 开头 {len(ks)} 个，每个规格 {max(p['n'] for p in per.values())} 个种子；R = Salem 多留的资源"
          f"（M3 的 conserve 单位：一张手牌、2 PP、一个 EP、一个 SEP 各算 1），正数是 Salem 多留\n")
    s0 = {k: diff(k, next(r for r in lines[(k, "level-strong")] if r["j"] == 0)) for k in ks
          if (k, "level-strong") in lines}
    print(f"**全部 {len(ks)} 个**\n")
    print("| 规格 | R 平均 | conserve 仍成立 | 和 Salem 回合末相同 | 每回合 ms |\n|---|---|---|---|---|")
    if s0:
        print(f"| level-strong 只看 j = 0（第 0 步的线） | {mean(gap(d) for d in s0.values()):+.2f} | "
              f"{mean(float('conserve' in DR.classify(d)[1]) for d in s0.values()):.0%} | – | – |")
    for spec in specs:
        ps = [per[(k, spec)] for k in ks if (k, spec) in per]
        print(f"| {spec} | {mean(p['R'] for p in ps):+.2f} | {mean(p['conserve'] for p in ps):.0%} | "
              f"{mean(p['same'] for p in ps):.0%} | {mean(p['ms'] for p in ps):.0f} |")
    print("\n**各字段的差（Salem − 该规格，种子平均后再对开头平均）**\n")
    print("| 字段 | " + " | ".join(specs) + " |\n|---|" + "---|" * len(specs))
    for f in DR.FIELDS:
        vals = [mean(per[(k, s)]["d"][f] for k in ks if (k, s) in per) for s in specs]
        if any(abs(v) > 1e-9 for v in vals):
            print(f"| {f} | " + " | ".join(f"{v:+.2f}" for v in vals) + " |")
    print("\n**按 M3 的类：更多搜索能不能缩小资源差**（R 平均；R 比 level-strong 小 / 大的开头数，按开头配对）\n")
    head = " | ".join(f"R {s.split('+')[0]}" for s in specs)
    print(f"| 类 | 个数 | {head} | 3000 比 strong：R 更小 / 更大 / 相同 | conserve 仍成立（strong → 3000） |\n|---|---|"
          + "---|" * len(specs) + "---|---|")
    order = ["race", "clear", "develop", "conserve", "mixed", "small"]
    top = specs[-1]
    for c in order + ["全部"]:
        sel = [k for k in ks if c == "全部" or m3[k]["class"] == c]
        sel = [k for k in sel if all((k, s) in per for s in specs)]
        if not sel:
            continue
        rs = [mean(per[(k, s)]["R"] for k in sel) for s in specs]
        lo = sum(1 for k in sel if per[(k, top)]["R"] < per[(k, "level-strong")]["R"] - 1e-9)
        hi = sum(1 for k in sel if per[(k, top)]["R"] > per[(k, "level-strong")]["R"] + 1e-9)
        cs = [mean(per[(k, s)]["conserve"] for k in sel) for s in ("level-strong", top)]
        print(f"| {c} | {len(sel)} | " + " | ".join(f"{v:+.2f}" for v in rs)
              + f" | {lo} / {hi} / {len(sel) - lo - hi} | {cs[0]:.0%} → {cs[1]:.0%} |")
    import random
    rng = random.Random(0)
    print("\n**分资源：Salem − 该规格（种子平均），以及 3000 − strong 的配对差和区间（按开头重抽 2000 次，种子 0）**\n")
    print("| 类 | 资源 | " + " | ".join(s.split("+")[0] for s in specs) + " | 3000 − strong [95%] |\n|---|---|"
          + "---|" * len(specs) + "---|")
    for c in ("conserve", "mixed", "全部"):
        sel = [k for k in ks if (c == "全部" or m3[k]["class"] == c) and all((k, s) in per for s in specs)]
        if not sel:
            continue
        for f, w in CONSERVE + (("R", None),):
            def val(k, s):
                return per[(k, s)]["R"] if f == "R" else per[(k, s)]["d"][f]
            vals = [mean(val(k, s) for k in sel) for s in specs]
            diffs = [val(k, "level-strong") - val(k, top) for k in sel]      # > 0: 3000 closer to Salem (kept more)
            boots = sorted(mean(rng.choice(diffs) for _ in diffs) for _ in range(2000))
            print(f"| {c} | {f} | " + " | ".join(f"{v:+.2f}" for v in vals)
                  + f" | {-mean(diffs):+.2f} [{-boots[1949]:+.2f}, {-boots[50]:+.2f}] |")
    print("\n**多花的是什么**（每回合平均次数；Salem 的线一列）\n")
    print("| 事件 | Salem | " + " | ".join(specs) + " |\n|---|---|" + "---|" * len(specs))
    for t in TAGS:
        sv = mean(salem[k]["tags"].get(t, 0) for k in ks)
        vals = [mean(per[(k, s)]["tags"][t] for k in ks if (k, s) in per) for s in specs]
        print(f"| {t} | {sv:.2f} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")
    for c in ("conserve", "mixed"):
        sel = [k for k in ks if m3[k]["class"] == c and all((k, s) in per for s in specs)]
        if not sel:
            continue
        print(f"\n**{c} 类（{len(sel)} 个）的事件**\n")
        print("| 事件 | Salem | " + " | ".join(specs) + " |\n|---|---|" + "---|" * len(specs))
        for t in TAGS:
            sv = mean(salem[k]["tags"].get(t, 0) for k in sel)
            vals = [mean(per[(k, s)]["tags"][t] for k in sel) for s in specs]
            print(f"| {t} | {sv:.2f} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")


TAGS = ("plays", "pp_spent", "evolves", "super_evolves", "face_attacks", "follower_attacks", "kills",
        "evolve_no_kill", "evolve_no_kill_face", "evolve_no_kill_no_attack", "evolve_no_kill_other", "overkill",
        "overkill_attacks", "play_no_change", "play_no_change_drew", "play_no_change_nothing")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run")
    a.add_argument("step0")
    a.add_argument("ana")
    a.add_argument("m3")
    a.add_argument("--out", required=True)
    a.add_argument("--seeds", type=int, default=4)
    a.add_argument("--workers", type=int, default=3)
    a.add_argument("--specs", nargs="+", default=list(SPECS))
    b = sub.add_parser("read")
    b.add_argument("rows")
    b.add_argument("m3")
    b.add_argument("--ana", required=True)
    args = ap.parse_args()
    _ana(args.ana)
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    {"run": run, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
