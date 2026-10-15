"""The installed turn-end evaluator's logit at every turn end of recorded games (scaledata records), for the scaling
test's calibration of the installed evaluator (README section 2): the state before EndTurn with after_end_of_turn
applied (skipped when that finishes the game, as netdata.rows), from the side that ends the turn, logit =
evaluate / SCALE; label = that side's result; turn = the state's turn after the end of turn (as the token files).
Condition: the opponent's deck list is known (order and hand not).

    PYTHONPATH=<svsim> python3 installed_logits.py rec-70100000.jsonl.gz --out logits.jsonl [--games N] [--workers 3]
"""
import argparse
import gzip
import json
from multiprocessing import Pool

W = None


def _init():
    global W
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    W = _search(make_agent("v2s", 0)).weights


def _game(line):
    from svsim.cards import decks
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply, new_game
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.ui.session import DECKS
    g = json.loads(line)
    st = new_game(decks.build(DECKS["ramp-t"][1]), decks.build(DECKS["ramp-t"][1]), seed=g["seed"])
    rows = []
    for data in g["actions"]:
        if st.over:
            break
        act = from_dict(data)
        if isinstance(act, EndTurn):
            me = st.active
            end = after_end_of_turn(st.clone())
            if not end.over:                     # as netdata.rows' ENDED: a finished position is not a training row
                rows.append([me, end.turn, evaluate(end, me, W, False) / SCALE])
        apply(st, act)
    ok = st.over and st.winner == g["winner"]
    s = (g["seed"] - g["g"]) // 100003
    out = []
    for me, turn, x in rows:
        y = 0.5 if g["winner"] is None else (1.0 if g["winner"] == me else 0.0)
        out.append({"seed": s, "g": g["g"], "turn": turn, "x": x, "y": y})
    return ok, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--out", required=True)
    ap.add_argument("--games", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    lines = [l for l in gzip.open(args.records, "rt", encoding="utf-8") if l.strip()]
    if args.games:
        lines = lines[:args.games]
    with Pool(args.workers, initializer=_init) as pool:
        res = pool.map(_game, lines)
    bad = sum(not ok for ok, _ in res)
    with open(args.out, "w", encoding="utf-8") as fh:
        for _, out in res:
            for r in out:
                fh.write(json.dumps(r) + "\n")
    print(f"{len(lines)} games, replay vs recorded winner mismatches {bad}, {sum(len(o) for _, o in res)} turn ends")


if __name__ == "__main__":
    main()
