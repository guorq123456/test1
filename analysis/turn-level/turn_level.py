"""Turn-level policy iteration, step 0: the turn-level regret audit (README.md here; written before any of its games).

This part picks the turn starts; the candidates, T and G_end wait for the build line's candidate generator.

    cd <svsim checkout> && python -m svsim.learn.netdata --games 150 --deck ramp --opponent ramp \\
        --agent level-strong --explore 0 --seed 65900000 --out selfplay.jsonl
    cd <svsim checkout> && PYTHONPATH=.:<this folder>:<this folder>/../card-value python3 <this> starts \\
        selfplay.jsonl --out starts.jsonl

starts.jsonl, one line per turn start, numbered k:
  k 0-299    self-play: every own-turn start (the first main-phase decision of each turn, either seat) of the 150
             games, sorted by (g, action index, seat), shuffled by Random(65910000), the first 300;
  k 300-     Salem's turns (seat 0) in his 27 games: every turn start of his, less the turns he won the game in and
             the turns his record stops inside; the 10 games, then the 17, each by (game id, action index).
  {"k", "src": "selfplay" | "salem", "game": g (self-play) or the game id, "at": the action index, "seat",
   "own_turn": the mover's turns taken, "batch": 1 (the 10 games) | 2 (the 17) | null}
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))

import salem_discrim as D        # noqa: E402  (Salem's games and turns, the discrimination experiment's)
import student_data as SD        # noqa: E402  (own_turn_starts, the student's positions')

BANK = 65900000
N_SELFPLAY = 300
SALEM_FILES = ("salem_games_10.json", "salem_games_17.json")


def salem_games():
    out = []
    for batch, f in enumerate(SALEM_FILES, 1):
        recs = json.load(open(os.path.join(HERE, "..", "card-value", f), encoding="utf-8"))["records"]
        out.append((batch, recs))
    return out


def salem_turns():
    """(batch, game id, action index) of every Salem turn start, less his winning turns and the turns the record
    stops inside."""
    out = []
    for batch, recs in salem_games():
        for gid in sorted(recs):
            for at in D.salem_turn_starts(recs[gid]):
                if D.used_this_turn(recs[gid], at)[1] or not D.turn_complete(recs[gid], at):
                    continue
                out.append((batch, gid, at))
    return out


def starts(args):
    games = SD._lines(args.selfplay)
    allp = sorted((rec["g"], at, seat) for rec in games for at, seat in SD.own_turn_starts(rec))
    random.Random(BANK + 10000).shuffle(allp)
    by_g = {rec["g"]: rec for rec in games}
    rows = []
    for g, at, seat in allp[:N_SELFPLAY]:
        st = SD._state_at(by_g[g], at)
        rows.append({"src": "selfplay", "game": g, "at": at, "seat": seat,
                     "own_turn": st.players[seat].turns_taken, "batch": None})
    recs = {gid: r for _, rs in salem_games() for gid, r in rs.items()}
    for batch, gid, at in salem_turns():
        st = D.state_at(recs[gid], at)
        rows.append({"src": "salem", "game": gid, "at": at, "seat": st.active,
                     "own_turn": st.players[st.active].turns_taken, "batch": batch})
    with open(args.out, "w", encoding="utf-8") as fh:
        for k, r in enumerate(rows):
            fh.write(json.dumps({"k": k, **r}) + "\n")
    n_salem = sum(r["src"] == "salem" for r in rows)
    print(f"自对弈 {len(games)} 局，{len(allp)} 个自己回合的开头，取 {min(len(allp), N_SELFPLAY)} 个；"
          f"Salem {n_salem} 个回合（10 局 {sum(r['batch'] == 1 for r in rows)}，17 局 {sum(r['batch'] == 2 for r in rows)}）；"
          f"共 {len(rows)} 个开头")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("starts")
    a.add_argument("selfplay")
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    {"starts": starts}[args.cmd](args)


if __name__ == "__main__":
    main()
