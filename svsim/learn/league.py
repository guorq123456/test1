"""Bradley–Terry strengths for bot versions from the gate's paired results.

The gate (tools.gate) answers "is A stronger than B"; with several versions
played against each other in some pattern (each new candidate against the
installed bot, now and then against an older one), this puts them all on one
scale: P(i beats j) = logistic(r_i - r_j), fitted by maximum likelihood, one
version held at 0. A draw counts half a win for each side.

Intervals come from resampling: the gate plays each seed twice with the seats
swapped, so the two games of a pair share the deal and are not independent;
`bootstrap` redraws whole pairs within each match and refits.

CR. The ladder (learn.rating) holds a player's CR where they win
1/2 + gap/800 of their games, which near even is 800 * (p - 1/2) ~ 200 * logit
gap: `CR_PER_LOGIT`. The scale is still a free parameter (`to_cr`): with two
or more anchors (name = known CR) it is fitted to them, with one anchor it
stays at `slope` and the anchor fixes the offset, with none the CRs are
relative to the reference version. Past a 175-point gap the ladder can't tell
players apart (learn.rating), so far-apart CRs are a reading of the scale,
not something the ladder would show.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

CR_PER_LOGIT = 200.0


@dataclass
class Match:
    """A head-to-head series between two versions: A's points per game, grouped in pairs."""
    a: str
    b: str
    pairs: list = field(default_factory=list)       # [(a's points in game 1, in game 2), ...]

    def totals(self) -> tuple[float, int]:
        points = sum(sum(p) for p in self.pairs)
        games = sum(len(p) for p in self.pairs)
        return points, games


def names_of(matches: list[Match]) -> list[str]:
    out = []
    for m in matches:
        for n in (m.a, m.b):
            if n not in out:
                out.append(n)
    return out


def connected(matches: list[Match]) -> bool:
    names = names_of(matches)
    if not names:
        return True
    seen, todo = {names[0]}, [names[0]]
    while todo:
        n = todo.pop()
        for m in matches:
            for x, y in ((m.a, m.b), (m.b, m.a)):
                if x == n and y not in seen:
                    seen.add(y)
                    todo.append(y)
    return len(seen) == len(names)


def fit(matches: list[Match], ref: str | None = None, prior: float = 1e-3, iters: int = 100) -> dict:
    """{name: r} maximizing the Bradley–Terry likelihood (Newton's method), r[ref] = 0 (default:
    the first version named). `prior` is a tiny ridge that keeps a version that won or lost
    every game finite."""
    import numpy as np
    names = names_of(matches)
    if not names:
        return {}
    ref = ref or names[0]
    idx = {n: i for i, n in enumerate(names)}
    free = [n for n in names if n != ref]
    col = {n: k for k, n in enumerate(free)}
    data = []
    for m in matches:
        w, n = m.totals()
        if n:
            data.append((idx[m.a], idx[m.b], w, n))
    r = np.zeros(len(names))
    for _ in range(iters):
        g = np.zeros(len(free))
        H = np.zeros((len(free), len(free)))
        for i, j, w, n in data:
            p = 1 / (1 + math.exp(-(r[i] - r[j])))
            d = w - n * p                      # d loglik / d r_i
            h = n * p * (1 - p)
            for x, s in ((names[i], 1.0), (names[j], -1.0)):
                if x in col:
                    g[col[x]] += s * d
            for x, sx in ((names[i], 1.0), (names[j], -1.0)):
                for y, sy in ((names[i], 1.0), (names[j], -1.0)):
                    if x in col and y in col:
                        H[col[x], col[y]] -= sx * sy * h
        rf = np.array([r[idx[n]] for n in free])
        g -= 2 * prior * rf
        H -= 2 * prior * np.eye(len(free))
        step = np.linalg.solve(H, g) if len(free) else np.zeros(0)
        for n in free:
            r[idx[n]] -= step[col[n]]
        if len(free) == 0 or float(np.max(np.abs(step))) < 1e-10:
            break
    return {n: float(r[idx[n]]) for n in names}


def bootstrap(matches: list[Match], ref: str | None = None, samples: int = 500, seed: int = 0,
              level: float = 0.95) -> dict:
    """{name: (low, high)}: percentile intervals of r from refits on pairs redrawn within each match."""
    rng = random.Random(seed)
    names = names_of(matches)
    draws = {n: [] for n in names}
    for _ in range(samples):
        redrawn = [Match(m.a, m.b, [rng.choice(m.pairs) for _ in m.pairs]) for m in matches if m.pairs]
        for n, v in fit(redrawn, ref).items():
            draws[n].append(v)
    out = {}
    for n, vals in draws.items():
        vals.sort()
        lo = vals[int((1 - level) / 2 * (len(vals) - 1))]
        hi = vals[int((1 + level) / 2 * (len(vals) - 1))]
        out[n] = (lo, hi)
    return out


def to_cr(ratings: dict, anchors: dict | None = None, slope: float = CR_PER_LOGIT) -> tuple[dict, float, float]:
    """({name: CR}, slope, offset) with CR = offset + slope * r. Two or more anchors fit slope
    and offset (least squares); one fixes the offset at the given slope; none leaves CR relative
    (offset 0: the reference version at 0)."""
    anchors = {n: c for n, c in (anchors or {}).items() if n in ratings}
    if len(anchors) >= 2:
        xs = [ratings[n] for n in anchors]
        ys = list(anchors.values())
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        if sxx > 1e-12:
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        offset = my - slope * mx
    elif len(anchors) == 1:
        (n, c), = anchors.items()
        offset = c - slope * ratings[n]
    else:
        offset = 0.0
    return {n: offset + slope * r for n, r in ratings.items()}, slope, offset


def read_gate(path: str, a: str, b: str) -> Match:
    """A gate results file (JSON lines with "points": [A in seat 0, A in seat 1]) as a Match."""
    import json
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(tuple(json.loads(line)["points"]))
    return Match(a, b, pairs)
