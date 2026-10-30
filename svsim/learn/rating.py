"""Class rating (CR), the ladder number the player described, used to rate the AI.

Rules (from the player):
- On reaching Grand Master a player's CR for the class starts at 1600 from the
  Diamond group, 1550 from Sapphire, 1500 from Ruby (lower groups don't count).
- Players are matched only within 200 CR of each other.
- With `gap` = my CR minus the opponent's, a win gains 16 - gap/25 and a loss
  costs 16 + gap/25 (what one side gains the other loses); above a gap of 175
  a win gains only 8 and a loss costs 24 (and the other way round below -175).
  The rules don't say how points are rounded: `change` rounds to the nearest
  point, the ladder below uses exact values.

What CR measures: a player's CR stops moving where their expected gain is zero.
Within a gap of 175 that is where they win 1/2 + gap/800 of their games
(`steady_rate`), so a CR gap reads as a win rate and back (`steady_gap`): 80
points is 60%, 175 points 72%. Winning 75% or more against everyone in reach
keeps a player climbing until nobody is within 200; past that the rules can't
tell how much stronger they are.

`ladder` rates several players (agents, the player) from their head-to-head
results: everyone starts at the anchors' CR and the expected changes are applied
until nothing moves, the way a ladder settles when everyone plays everyone in
reach equally often. `bootstrap` repeats that with the win rates redrawn from
what the games allow (few games: wide intervals).
"""
from __future__ import annotations

import math
import random

START = {"diamond": 1600, "sapphire": 1550, "ruby": 1500, "钻石": 1600, "蓝宝石": 1550, "红宝石": 1500}
WINDOW = 200                  # matched only within this gap
CAP = 175                     # past this gap a win is +8 and a loss -24


def can_match(mine: float, theirs: float) -> bool:
    return abs(mine - theirs) <= WINDOW


def exact_change(mine: float, theirs: float, won: bool) -> float:
    gap = mine - theirs
    if abs(gap) > WINDOW:
        raise ValueError(f"CR gap {gap:.0f} is outside the matching window of {WINDOW}")
    if gap > CAP:
        return 8.0 if won else -24.0
    if gap < -CAP:
        return 24.0 if won else -8.0
    return 16 - gap / 25 if won else -(16 + gap / 25)


def change(mine: float, theirs: float, won: bool) -> int:
    """The points one game moves my CR (rounded to the nearest point)."""
    x = exact_change(mine, theirs, won)
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def expected_change(gap: float, p: float) -> float:
    """My average change per game at CR gap `gap` when I win a fraction p."""
    if gap > CAP:
        return 8 * p - 24 * (1 - p)
    if gap < -CAP:
        return 24 * p - 8 * (1 - p)
    return p * (16 - gap / 25) - (1 - p) * (16 + gap / 25)       # = (800 (p - 1/2) - gap) / 25


def steady_rate(gap: float) -> float:
    """The win rate that keeps my CR steady at this gap."""
    if gap > CAP:
        return 0.75
    if gap < -CAP:
        return 0.25
    return 0.5 + gap / 800


# The player's own scale (the architecture session, 2026-10-07 16:14Z): a CR gap of 236 per logit of the
# win rate, so 200 CR is about 70%; the main number in reports, with the ladder's steady formula beside it.
SALEM_PER_LOGIT = 236


def salem_gap(p: float) -> float:
    """The CR gap on the player's scale for a win rate `p` (0 < p < 1): 236 x ln(p / (1 - p))."""
    return SALEM_PER_LOGIT * math.log(p / (1 - p))


def steady_gap(p: float) -> float:
    """The gap at which win rate p keeps my CR steady: 800 (p - 1/2), held at
    +-175; at 75% or more (25% or less) the stronger side keeps climbing until out of
    reach, reported as +-inf."""
    if p >= 0.75:
        return float("inf")
    if p <= 0.25:
        return float("-inf")
    return max(-CAP, min(CAP, 800 * (p - 0.5)))


def games_for(margin: float, p: float = 0.5, z: float = 1.645) -> int:
    """Games needed to pin a CR gap within +-margin (90% by default)."""
    return int((z * 800) ** 2 * p * (1 - p) / margin ** 2 + 0.999)


def ladder(rates: dict, anchors: dict, iters: int = 4000, step: float = 2.0) -> dict:
    """CRs where the expected changes balance. `rates` maps (a, b) to a's win rate
    against b; `anchors` fixes some players' CR (the rest start at their mean).
    Pairs more than 200 apart stop playing, so a player out of everyone's reach
    stays where it left the window."""
    players = sorted({x for pair in rates for x in pair} | set(anchors))
    start = sum(anchors.values()) / len(anchors) if anchors else 0.0
    cr = {x: float(anchors.get(x, start)) for x in players}
    games = {x: [] for x in players}
    for (a, b), p in rates.items():
        games[a].append((b, p))
        games[b].append((a, 1 - p))
    for k in range(iters):
        moved = 0.0
        delta = {}
        rate = step / (1 + k / 500)                 # shrinking steps settle the jump at a gap of 175
        for x in players:
            if x in anchors:
                continue
            reach = [(y, p) for y, p in games[x] if can_match(cr[x], cr[y])]
            if reach:
                delta[x] = rate * sum(expected_change(cr[x] - cr[y], p) for y, p in reach) / len(reach)
        for x, d in delta.items():
            cr[x] += d
            moved = max(moved, abs(d))
        if moved < 1e-3:
            break
    return cr


def connected(pairs, start: str) -> set:
    """The players linked to `start` through pairs that played each other."""
    seen, todo = {start}, [start]
    while todo:
        x = todo.pop()
        for a, b in pairs:
            for y in ((b,) if a == x else (a,) if b == x else ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
    return seen


def bootstrap(results: dict, anchors: dict, samples: int = 300, seed: int = 0,
              level: float = 0.9) -> tuple[dict, dict]:
    """`results` maps (a, b) to (a's wins, games; draws count half). Returns the
    CRs from the observed win rates and, for each player, the (low, high) range
    holding `level` of the CRs when every pair's win rate is redrawn from its
    posterior (Beta with a flat prior)."""
    rng = random.Random(seed)
    point = ladder({k: w / n for k, (w, n) in results.items()}, anchors)
    draws = {x: [] for x in point}
    for _ in range(samples):
        rates = {k: rng.betavariate(w + 1, n - w + 1) for k, (w, n) in results.items()}
        for x, v in ladder(rates, anchors).items():
            draws[x].append(v)
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    span = {}
    for x, vs in draws.items():
        vs.sort()
        span[x] = (vs[int(lo * (len(vs) - 1))], vs[int(hi * (len(vs) - 1))])
    return point, span
