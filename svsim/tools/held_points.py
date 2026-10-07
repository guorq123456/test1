"""What a fitted evaluation thinks one more unused evolution point is worth, by game state.

    python -m svsim.tools.held_points MODEL.json games.jsonl [--max-games N]

For a linear model with the version-3 features (learn.features.SIDE3), the derivative of its logit
with respect to the player's unused evolution points (and super-evolution points) at a position is
the point's own weight plus each context interaction's weight times that context value. This averages
it over the turn-end positions of some games, in two tables (the architecture session's checks):

- turns since that evolution unlocked (0, 1, 2, 3-4, 5+) by how long the game still looks (both
  leaders' defense together: 30 or more long, 18-29 middle, under 18 short);
- what the points could go to: a payoff follower (learn.payoff) reachable on the coming turn, one in
  hand out of reach only, or neither;

and the defense gap (ahead / even / behind by 4) as a reference column. Logit units; at even odds a
logit of x is about x / 4 of win probability. A version-2 model gives the same number everywhere.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SINCE = (("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3-4", 3, 4), ("5+", 5, 99))
LENGTH = (("long", 30, 99), ("middle", 18, 29), ("short", 0, 17))
PAYOFF = ("reachable", "out of reach", "neither")
GAP = (("ahead", 4, 99), ("even", -3, 3), ("behind", -99, -4))


def marginal(model, state, player: int) -> tuple[float, float]:
    """d logit / d (evolution points), d logit / d (super-evolution points) at `state` for `player`."""
    from svsim.learn.features import CONTEXT, context
    w = model.weights_by_name()
    out = []
    for pt, super_ in (("ep", False), ("sep", True)):
        d = w.get(f"me_{pt}", 0.0)
        if model.version >= 3:
            d += sum(w[f"me_{pt}_x_{c}"] * v for c, v in zip(CONTEXT, context(state, player, False, super_)))
        out.append(d)
    return out[0], out[1]


def _cell(name_lo_hi, value):
    return next(name for name, lo, hi in name_lo_hi if lo <= value <= hi)


def tables(model, records) -> dict:
    """{table: {key: [sum d/d ep, sum d/d sep, positions]}} over the turn-end positions (ENDED)."""
    from svsim.learn.encode import ENDED
    from svsim.learn.features import context
    from svsim.learn.netdata import rows
    from svsim.search.evaluate import effective_hp
    acc = {"since x length": {}, "payoff": {}, "gap": {}, "card": {}}

    def add(table, key, e, s):
        a = acc[table].setdefault(key, [0.0, 0.0, 0])
        a[0] += e
        a[1] += s
        a[2] += 1
    for record in records:
        for phase, me, state, _ in rows(record):
            if phase != ENDED:
                continue
            p, op = state.players[me], state.players[1 - me]
            e, s = marginal(model, state, me)
            ctx = context(state, me, False)
            since = round(ctx[0] * 5)
            hp_sum = effective_hp(p) + effective_hp(op)
            add("since x length", (_cell(SINCE, since), _cell(LENGTH, hp_sum)), e, s)
            add("payoff", "reachable" if ctx[1] > 0 else "out of reach" if ctx[2] > 0 else "neither", e, s)
            add("gap", _cell(GAP, effective_hp(p) - effective_hp(op)), e, s)
            pp = p.max_pp + 1 + (1 if p.bonus_ready else 0)          # the coming turn's play points
            for cid in {c.defn.card_id for c in p.hand if c.cost > pp}:  # by card: in hand, out of reach
                add("card", cid, e, s)
    return acc


def report(model, records) -> str:
    acc = tables(model, records)
    f = lambda a: f"{a[0] / a[2]:+.3f}/{a[1] / a[2]:+.3f} ({a[2]})" if a else ""
    lines = [f"version {model.version}: d logit / d point (evolution / super-evolution), positions"]
    lines.append("since unlock  " + "".join(f"{n:>24}" for n, _, _ in LENGTH))
    for s, _, _ in SINCE:
        lines.append(f"{s:<13}" + "".join(f"{f(acc['since x length'].get((s, n))):>24}" for n, _, _ in LENGTH))
    lines.append("payoff:  " + "   ".join(f"{k} {f(acc['payoff'].get(k))}" for k in PAYOFF))
    lines.append("gap:     " + "   ".join(f"{k} {f(acc['gap'].get(k))}" for k, _, _ in GAP))
    from svsim.cards.pool import POOL
    from svsim.learn.payoff import tier
    by_id = POOL                                     # card id -> CardDef
    lines.append("in hand, out of reach, by card:")
    for cid, a in sorted(acc["card"].items(), key=lambda kv: -kv[1][2]):
        d = by_id.get(cid)
        if d is not None and d.is_follower:
            lines.append(f"  tier {tier(d)}  {f(a)}  {d.name_zh or d.name}")
    return "\n".join(lines)


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
    print(args.model)
    print(report(model, records))


if __name__ == "__main__":
    main()
