"""Hold or spend, on Salem's own turns in the cell "an A card in hand, out of reach": played to the end.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/cross-turn:<test1>/analysis/card-value:<test1>/analysis/mirror-regression \
        python3 <this> analysis/mirror-regression/salem_games.json analysis/mirror-regression/evolve_probes.json \
        [--k 16] [--workers 4] --out rows.jsonl
    python3 <this> --report rows.jsonl

Background (the architecture thread, 18:34Z): 1 号's second round of "selective hold" forks lost
8-11 points against their controls, in this very cell, so it is either that holding a point there
loses, or that the bot holds badly or can't cash in what it holds. On each of Salem's turns of the
cell (evolve_probes.json; the standard table's cell, Erntz's unevolved side left out), two branches
from the same determinization (Salem's seat: own deck order, the opponent's hand and deck from its
known 40 cards, the random numbers; the same 2 x k determinizations and agent seeds for both):
- branch 1, Salem's own turn: his actions replayed; if a replayed action is not legal on this
  determinization (a card he drew is not the card drawn here), v2s finishes the turn in his class
  (no evolution if he held);
- branch 2, the other class by the bot: v2s's search with evolving vetoed if Salem evolved, or made
  to evolve (ending the turn vetoed while an evolution is legal and none was made) if he held;
then v2 against v2 to the end. Per turn: mean of (branch 1 - branch 2) over the determinizations, a
win-rate difference (positive: Salem's choice did better), and its 95% interval; over all turns the
mean ± 95% (turns resampled), and by Salem's choice (held / spent).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import math
import os
import random
import sys
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, Evolve
from svsim.core.engine import apply, legal_actions

V2, V2S = "mcts:100+plan+learned+phased", "mcts:200+plan+learned+phased"
CELL = "2 档在手够不着"
GAMES, TURNS = {}, {}


def vetoing(spec, seed, veto):
    from realized import agent_with_veto
    return agent_with_veto(spec, seed, veto)


def no_evolve(s, a):
    return isinstance(a, Evolve)


def must_evolve(s, a):
    if not isinstance(a, EndTurn):
        return False
    p = s.players[s.active]
    return not p.evolved_this_turn and any(isinstance(x, Evolve) for x in legal_actions(s))


def finish(st, me, sd):
    from svsim.tools.arena import make_agent
    agents = {me: make_agent(V2, sd + 3), 1 - me: make_agent(V2, sd + 1)}
    while not st.over:
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return 1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5


def branch_salem(base, me, actions, held, sd):
    st = base.clone()
    diverged = False
    for a in actions:
        if st.over or st.active != me:
            break
        if a in legal_actions(st):
            apply(st, a)
        else:
            diverged = True
            break
    if diverged and not st.over and st.active == me:
        agent = vetoing(V2S, sd, no_evolve if held else None)
        while not st.over and st.active == me:
            apply(st, agent.act(st, legal_actions(st)))
    return (finish(st, me, sd) if not st.over else (1.0 if st.winner == me else 0.0)), diverged


def branch_other(base, me, held, sd):
    st = base.clone()
    agent = vetoing(V2S, sd, must_evolve if held else no_evolve)
    while not st.over and st.active == me:
        apply(st, agent.act(st, legal_actions(st)))
    evolved = st.players[me].evolved_this_turn if not st.over else None
    return (finish(st, me, sd) if not st.over else (1.0 if st.winner == me else 0.0)), evolved


def measure(job):
    from svsim.core.view import determinize
    key, k, seed = job
    st0, actions, held = TURNS[key]
    me = st0.active
    diffs, div, other_evolved = [], 0, 0
    for j in range(2 * k):
        base = determinize(st0, me, random.Random(seed * 1000 + j))
        sd = seed * 1000 + 10 * j
        r1, d = branch_salem(base, me, actions, held, sd)
        r2, ev = branch_other(base, me, held, sd)
        diffs.append(r1 - r2)
        div += d
        other_evolved += bool(ev)
    return {"key": key, "held": held, "diffs": diffs, "diverged": div, "other_evolved": other_evolved}


def load_turns(games_path, probes_path):
    from evolve_hold_review import standard_row
    from evolve_targets import salem_turns
    games = json.load(open(games_path, encoding="utf-8"))["records"]
    probes = json.load(open(probes_path, encoding="utf-8"))["positions"]
    out = {}
    for p in probes:
        if p["category"] not in ("evolve_hold", "evolve_use"):
            continue
        turns = dict(salem_turns(games[p["game"]]))
        turn = turns[p["at"]]
        row = standard_row(turn)
        if row is None or row["tier"] != CELL or row.get("erntz_plain"):
            continue
        key = f"{p['game']}@{p['at']}"
        out[key] = (turn[0][0], [a for _, a in turn], p["category"] == "evolve_hold", p)
    return out


def report(path, probes_path=None):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    def ci(xs):
        m = sum(xs) / len(xs)
        se = math.sqrt(sum((x - m) ** 2 for x in xs) / max(len(xs) - 1, 1) / len(xs))
        return m, 1.96 * se
    print("条件：对手卡表已知（牌序、手牌未知）。差 = Salem 的打法 − 另一类里 bot 的最好打法（正数：Salem 的选择打到终局更好）。\n")
    print(f"{'回合':<22}{'Salem':>6}  {'胜率差':>8} ± 95%     分支 1 走偏  分支 2 进化了")
    for r in sorted(rows, key=lambda r: r["key"]):
        m, h = ci(r["diffs"])
        n = len(r["diffs"])
        print(f"{r['key']:<22}{'留' if r['held'] else '花':>6}  {m:+8.3f} ± {h:.3f}    {r['diverged']:>3}/{n}      {r['other_evolved']:>3}/{n}")
    rng = random.Random(19)
    for title, sub in (("全部", rows), ("Salem 留的", [r for r in rows if r["held"]]), ("Salem 花的", [r for r in rows if not r["held"]])):
        if not sub:
            continue
        means = [sum(r["diffs"]) / len(r["diffs"]) for r in sub]
        m = sum(means) / len(means)
        bs = sorted(sum(means[rng.randrange(len(means))] for _ in means) / len(means) for _ in range(4000))
        print(f"\n{title}：{len(sub)} 个回合，平均 {m:+.3f}（95% {bs[100]:+.3f}～{bs[3899]:+.3f}，回合重抽）")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("games")
    ap.add_argument("probes")
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    TURNS.update({k: v[:3] for k, v in load_turns(args.games, args.probes).items()})
    keys = sorted(TURNS)
    print(f"这一格的回合：{len(keys)} 个（Salem 留 {sum(TURNS[k][2] for k in keys)}，花 {sum(not TURNS[k][2] for k in keys)}）", flush=True)
    done = set()
    if os.path.exists(args.out):
        done = {json.loads(line)["key"] for line in open(args.out, encoding="utf-8") if line.strip()}
    jobs = [(k, args.k, 950000 + n) for n, k in enumerate(keys) if k not in done]
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for row in pool.imap_unordered(measure, jobs, chunksize=1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(f"  {row['key']} 完成", flush=True)


if __name__ == "__main__":
    main()
