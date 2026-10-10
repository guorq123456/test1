"""The lethal-fix gates' companion (README-lethal2.md, README-lethal3.md here): the gate's 300 pairs played again with the gate's own
game function and agent seeds (tools.gate._game / _agent: A seeded 2 x seed + seat, B 2 x seed + 1 - seat + 7919),
so on the machine that ran the gate the games are the same; their records kept (the gate keeps none here). Then:
- every pair's points set beside the gate's rows (they should all match);
- lethals realized per 100 games, A and B: games the winner won during its own turn (an end-of-turn win counts);
- at A's own-turn starts: the share with a ticker on A's field (search.combo.tickers_of), and both turn-start checks
  timed on the real position (level-strong's: the planner, then LethalSearch 2000 / screen 200 / near (1000, 4);
  +lethal2's: the planner with tickers, then LethalSearch 3000 / screen 200 / near (2000, 4); as the builder's
  analysis/speed/lethal2_eval.py), A's added ms per turn start = the difference.
Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host lethal2_games play --a A --b B --deck pirate-t --opponent pirate-t --seed 66600000 \\
        --pairs 300 --workers 12 --out records.jsonl
    python -m svsim.tools.host lethal2_games read records.jsonl gate.jsonl --workers 12
"""
import argparse
import json
import math
import statistics
import time


def _cards(deck, opponent):
    from svsim.cards import decks
    from svsim.ui.session import DECKS
    return decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])


def _pair(job):
    from svsim.tools import gate
    k, seed, a, b, deck, opponent = job
    mine, theirs = _cards(deck, opponent)
    out = []
    for seat in (0, 1):
        pts, record = gate._game(mine, theirs, seat, gate._agent(a, 2 * seed + seat, None),
                                 gate._agent(b, 2 * seed + 1 - seat + 7919, None), seed,
                                 f"{a} / {b}" if seat == 0 else f"{b} / {a}", [deck, opponent])
        out.append({"k": k, "seed": seed, "a_seat": seat, "points": pts, "first": record.get("first"),
                    "winner": record.get("winner"), "actions": record["actions"], "deck": deck, "opponent": opponent})
    return out


def play(args):
    from multiprocessing import Pool
    jobs = [(k, args.seed + k, args.a, args.b, args.deck, args.opponent) for k in range(args.pairs)]
    with Pool(args.workers) as pool, open(args.out, "w", encoding="utf-8") as fh:
        for n, games in enumerate(pool.imap_unordered(_pair, jobs), 1):
            for g in games:
                fh.write(json.dumps(g) + "\n")
            fh.flush()
            if n % 25 == 0:
                print(f"{n}/{len(jobs)}", flush=True)
    print(f"{len(jobs)} 对写进了 {args.out}")


def check(state, tickers: bool, near, max_nodes):
    """A LethalAgent turn-start check with the planner first (+plan): (found, ms). As the builder's lethal2_eval."""
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    t = time.perf_counter()
    hp = state.players[1 - state.active].leader_hp
    p = combo.plan(state, 20000, tickers=tickers)
    if p.damage >= hp and p.steps:
        line = combo.realize(state, p.steps, face_first=p.tickers)
        if line and combo.verify(state, line):
            return True, (time.perf_counter() - t) * 1000
    r = LethalSearch(max_nodes=max_nodes, screen=200, near=near, seed=0).solve(state.clone())
    return r.sure, (time.perf_counter() - t) * 1000


# +lethal3's checks (the builder's analysis/speed/lethal3_eval.py, 715230d): the planner via combo.planned_lethal
# (tickers / plannerfix / eot), else the screened search; level-strong's (NOW) and the package's (NEW)
NOW3 = dict(tickers=False, fix=False, eot=False, max_nodes=2000, near=(1000, 4))
NEW3 = dict(tickers=True, fix=True, eot=True, max_nodes=3000, near=(2000, 4))
PACKAGE = "lethal2"


def check3(state, tickers, fix, eot, max_nodes, near):
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    t = time.perf_counter()
    line, _ = combo.planned_lethal(state, 20000, tickers=tickers, fix=fix, eot=eot)
    if line:
        return True, (time.perf_counter() - t) * 1000
    r = LethalSearch(max_nodes=max_nodes, screen=200, near=near, seed=0).solve(state.clone())
    return r.sure, (time.perf_counter() - t) * 1000


def _checks(state, package):
    if package == "lethal3":
        return check3(state, **NOW3), check3(state, **NEW3)
    return check(state, False, (1000, 4), 2000), check(state, True, (2000, 4), 3000)


def _game_facts(g):
    """Replay one game: who won and whether during its own turn; at A's own-turn starts the tickers and both checks."""
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, new_game
    from svsim.core.enums import Phase
    from svsim.search.combo import tickers_of
    mine, theirs = _cards(g["deck"], g["opponent"])
    a = g["a_seat"]
    cards = [None, None]
    cards[a], cards[1 - a] = mine, theirs
    st = new_game(cards[0], cards[1], seed=g["seed"])
    seen, starts = set(), []
    last_mover = None
    for data in g["actions"]:
        if st.phase == Phase.MAIN and st.active == a and (st.turn, st.active) not in seen:
            seen.add((st.turn, st.active))
            old, new = _checks(st, g.get("package", "lethal2"))
            starts.append({"tickers": len(tickers_of(st)), "old": old, "new": new})
        last_mover = st.active
        apply(st, from_dict(data))
    own_turn_win = st.over and st.winner in (0, 1) and st.winner == last_mover
    return {"k": g["k"], "a_seat": a, "points": g["points"], "winner": st.winner,
            "lethal_by": ("A" if st.winner == a else "B") if own_turn_win else None, "starts": starts}


def read(args):
    from multiprocessing import Pool
    games = [dict(json.loads(x), package=args.package) for x in open(args.records, encoding="utf-8") if x.strip()]
    gate = {json.loads(x)["k"]: json.loads(x) for x in open(args.gate, encoding="utf-8") if x.strip()}
    with Pool(args.workers) as pool:
        facts = pool.map(_game_facts, games)
    mismatch = sum(1 for f in facts if gate[f["k"]]["points"][f["a_seat"]] != f["points"])
    n = len(facts)
    la = sum(f["lethal_by"] == "A" for f in facts)
    lb = sum(f["lethal_by"] == "B" for f in facts)
    starts = [s for f in facts for s in f["starts"]]
    added = [s["new"][1] - s["old"][1] for s in starts]
    p90 = sorted(added)[min(len(added) - 1, int(math.ceil(0.9 * len(added))) - 1)] if added else float("nan")
    print("条件：对手卡表已知（牌序、手牌未知）。斩杀修正门的附带计数\n")
    print(f"- 重打的 {n} 局，和门的记录逐局比：得分不同 {mismatch} 局")
    print(f"- 在自己回合里赢下的局（斩杀兑现），每 100 局：A {100 * la / n:.1f}（{la} 局），B {100 * lb / n:.1f}（{lb} 局）")
    print(f"- A 的自己回合开头 {len(starts)} 个：场上有 ticker 的 {sum(s['tickers'] > 0 for s in starts) / max(len(starts), 1):.1%}")
    print(f"- 开头的检查找到斩杀：+{args.package} {sum(s['new'][0] for s in starts)}，level-strong 的 {sum(s['old'][0] for s in starts)}；"
          f"只有 +{args.package} 找到 {sum(s['new'][0] and not s['old'][0] for s in starts)}，只有 level-strong 找到 "
          f"{sum(s['old'][0] and not s['new'][0] for s in starts)}")
    print(f"- A 每个回合开头多花的毫秒：平均 {statistics.mean(added):+.1f}，p90 {p90:+.1f}"
          f"（level-strong 的检查平均 {statistics.mean(s['old'][1] for s in starts):.1f} ms）")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("play")
    a.add_argument("--a", required=True)
    a.add_argument("--b", required=True)
    a.add_argument("--deck", default="pirate-t")
    a.add_argument("--opponent", default="pirate-t")
    a.add_argument("--seed", type=int, required=True)
    a.add_argument("--pairs", type=int, default=300)
    a.add_argument("--workers", type=int, default=12)
    a.add_argument("--out", required=True)
    a = sub.add_parser("read")
    a.add_argument("records")
    a.add_argument("gate", help="the gate's results file (same seeds)")
    a.add_argument("--package", default="lethal2", choices=("lethal2", "lethal3"),
                   help="which turn-start checks to time: +lethal2's (23b317d) or +lethal3's (715230d)")
    a.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    {"play": play, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
