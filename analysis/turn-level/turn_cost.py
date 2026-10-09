"""Equal compute for the turnpick gate (README.md here, "turnpick 门"): each agent plays the mover's whole turn from
the first N training starts of step 1 (starts.jsonl order, split train), on the real position, seed 7, one process,
the specs taken in turn on each start; the wall milliseconds of the whole turn, the pick's own plans and scores
included. The gate's ms (tools.gate) times only the moves the base search ran, so on a turn the pick switched, its
plans and scores go unrecorded; hence this. Prints each spec's mean ms per turn, and for each B the ratio
A / B = sum of A's ms / sum of B's over the same starts, with the N for B that would match: round(N_B x ratio).
Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host turn_cost <step 1 dir> --n 60 --a SPEC --b SPEC [SPEC ...] [--out cost.jsonl]
"""
import argparse
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "card-value"))

import student_data as SD        # noqa: E402


def _pick(agent):
    for _ in range(8):
        if agent is None or hasattr(agent, "choose_plan"):
            return agent
        agent = getattr(agent, "base", None)
    return None


def turn(spec, games, st):
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    s = SD._state_at(games[st["game"]], st["at"])
    me = s.active
    agent = make_agent(spec, 7)
    t = time.perf_counter()
    n = 0
    while not s.over and s.active == me:
        apply(s, agent.act(s, legal_actions(s)))
        n += 1
    ms = 1000 * (time.perf_counter() - t)
    pick = _pick(agent)
    chosen = (pick.last_pick or {}).get("chosen") if pick is not None else None
    return {"k": st["k"], "spec": spec, "ms": round(ms, 1), "decisions": n, "chosen": chosen}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step1", help="the step-1 data folder (selfplay.jsonl, starts.jsonl)")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=1, help="ignored (one process); for the launcher")
    args = ap.parse_args()
    games = {r["g"]: r for r in SD._lines(os.path.join(args.step1, "selfplay.jsonl"))}
    starts = [r for r in SD._lines(os.path.join(args.step1, "starts.jsonl")) if r["split"] == "train"]
    specs = [args.a] + args.b
    for sp in specs:                                  # warm-up (models load), not counted
        turn(sp, games, starts[args.n])
    rows = {sp: [] for sp in specs}
    if args.out and os.path.dirname(args.out):
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fh = open(args.out, "w", encoding="utf-8") if args.out else None
    for st in starts[:args.n]:
        for sp in specs:
            r = turn(sp, games, st)
            rows[sp].append(r)
            if fh:
                fh.write(json.dumps(r) + "\n")
                fh.flush()
    print("条件：对手卡表已知（牌序、手牌未知）。整回合耗时（单进程，种子 7，第 1 步前 "
          f"{args.n} 个训练开头）")
    total_a = sum(r["ms"] for r in rows[args.a])
    for sp in specs:
        ms = [r["ms"] for r in rows[sp]]
        line = f"- `{sp}`：每回合 {statistics.mean(ms):.0f} ms（中位 {statistics.median(ms):.0f}）"
        if sp == args.a:
            sw = sum(1 for r in rows[sp] if r["chosen"] not in (None, "bot"))
            line += f"；换了打法的回合 {sw}/{len(ms)}"
        else:
            ratio = total_a / sum(ms)
            m = re.match(r"mcts:(\d+)", sp)
            line += f"；A ÷ 它 = {ratio:.3f}"
            if m:
                line += f"，配平的 N = round({m.group(1)} × {ratio:.3f}) = {round(int(m.group(1)) * ratio)}"
        print(line)


if __name__ == "__main__":
    main()
