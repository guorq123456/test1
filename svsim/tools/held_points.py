"""What a fitted evaluation thinks one more unused evolution point is worth, by game state.

    python -m svsim.tools.held_points MODEL.json games.jsonl [--max-games N]

For a linear model with the version-3 features (learn.features.SIDE3), the derivative of its logit
with respect to the player's unused evolution points (and super-evolution points) at a position is
the point's own weight plus each context interaction's weight times that context value. This averages
it over the positions of some games, in cells: ahead / even / behind (leader defense gap of 4 or
more either way) by own turn (1-4, 5-7, 8-10, 11+). The first check of the held-points work: a point
should be worth more in long, even games than when behind. Logit units; at even odds a logit of x is
about x / 4 of win probability.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CELLS = (("ahead", lambda d: d >= 4), ("even", lambda d: -4 < d < 4), ("behind", lambda d: d <= -4))
TURNS = (("1-4", 1, 4), ("5-7", 5, 7), ("8-10", 8, 10), ("11+", 11, 99))


def marginal(model, state, player: int) -> tuple[float, float]:
    """d logit / d (evolution points), d logit / d (super-evolution points) at `state` for `player`."""
    from svsim.learn.features import CONTEXT, context, names
    w = model.weights_by_name()
    out = []
    ctx = context(state, player, False)
    for pt in ("ep", "sep"):
        d = w.get(f"me_{pt}", 0.0)
        if model.version >= 3:
            d += sum(w[f"me_{pt}_x_{c}"] * v for c, v in zip(CONTEXT, ctx))
        out.append(d)
    return out[0], out[1]


def table(model, records, phase_ended: bool = True) -> dict:
    """{(cell, turns): [mean d/d ep, mean d/d sep, positions]} over the turn-end positions (ENDED)."""
    from svsim.learn.encode import ENDED
    from svsim.learn.netdata import rows
    from svsim.search.evaluate import effective_hp
    acc = {}
    for record in records:
        for phase, me, state, _ in rows(record):
            if phase_ended and phase != ENDED:
                continue
            p, op = state.players[me], state.players[1 - me]
            gap = effective_hp(p) - effective_hp(op)
            cell = next(name for name, test in CELLS if test(gap))
            turns = next(name for name, lo, hi in TURNS if lo <= p.turns_taken <= hi)
            e, s = marginal(model, state, me)
            a = acc.setdefault((cell, turns), [0.0, 0.0, 0])
            a[0] += e
            a[1] += s
            a[2] += 1
    return {k: [v[0] / v[2], v[1] / v[2], v[2]] for k, v in acc.items()}


def main() -> None:
    from svsim.learn.model import LinearValue
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model")
    parser.add_argument("games")
    parser.add_argument("--max-games", type=int, default=300)
    args = parser.parse_args()
    model = LinearValue.load(Path(args.model))
    records = []
    for line in open(args.games, encoding="utf-8"):
        records.append(json.loads(line))
        if len(records) >= args.max_games:
            break
    t = table(model, records)
    print(f"{args.model} (version {model.version}): d logit / d point, evolution / super-evolution, positions")
    print("        " + "".join(f"{name:>22}" for name, _, _ in TURNS))
    for cell, _ in CELLS:
        row = []
        for name, _, _ in TURNS:
            v = t.get((cell, name))
            row.append(f"{v[0]:+.3f} / {v[1]:+.3f} ({v[2]:>4})" if v else " " * 22)
        print(f"{cell:<8}" + "".join(f"{x:>22}" for x in row))


if __name__ == "__main__":
    main()
