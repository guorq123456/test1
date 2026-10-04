"""Adaptive newcomer start (option A in stage_exp.py).

First-time official players win less than the field average they are placed at, and by how much
changes with the era (about 46 Elo in 2022, ~90 in 2023-2025, ~49 in 2026). Before each event we
estimate that gap from debutants' results over the previous 365 days, using only out-of-sample
predictions made before those matches, and anchor every player who debuts at the event there: n
virtual draws against a fixed opponent, so a player with no results would sit exactly at -c. The
anchor is dated at the debut and fades with the same half-life as real results, so real results
take over.
"""
import math
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

WINDOW_DAYS = 365
MIN_DEBUT_MATCHES = 30


def _offset(samples):
    """Logit gap c (debutants weaker by c) that best explains [(d winner-minus-loser, debut_w, debut_l)]."""
    c = 0.0
    for _ in range(30):
        g = h = 0.0
        for d, dw, dl in samples:
            s = dl - dw
            if not s:
                continue
            p = 1 / (1 + math.exp(-(d + c * s)))
            g += (1 - p) * s
            h += p * (1 - p) * s * s
        if h == 0:
            return 0.0
        c += g / h
    return max(c, 0.0)


def offsets(matches, half_life, prior_sd, fit_bt):
    """{event: c} estimated before each event; matches are bt.load_matches tuples (t, w, l, weight, event)."""
    start = defaultdict(lambda: datetime.max)
    for m in matches:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)
    samples = {}
    for ev in evs[2:]:
        t0 = start[ev]
        past = [m for m in matches if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / half_life) * np.array([m[3] for m in past])
        b, _ = fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), prior_sd)
        r = lambda p: b[idx[p]] if p in idx else 0.0  # noqa: E731
        samples[ev] = [(r(m[1]) - r(m[2]), m[1] not in idx, m[2] not in idx) for m in matches if m[4] == ev]
    out = {}
    for ev in evs:
        t0 = start[ev]
        window = [x for e, xs in samples.items() if t0 - timedelta(days=WINDOW_DAYS) <= start[e] < t0 for x in xs]
        if sum(1 for _, a, b in window if a != b) < MIN_DEBUT_MATCHES:
            window = [x for e, xs in samples.items() if start[e] < t0 for x in xs]
        out[ev] = _offset(window) if window else 0.0
    return out, start


def anchors(matches, half_life, prior_sd, fit_bt, n=2.0):
    """[(debut time, player, level, wins, losses, half-life)] in the format of bt.py's virtual results."""
    if n <= 0:
        return []
    c, start = offsets(matches, half_life, prior_sd, fit_bt)
    lam = 1 / prior_sd ** 2
    debut = {}
    for m in sorted(matches):
        for p in (m[1], m[2]):
            debut.setdefault(p, m[4])
    # dated just before the debut event starts, so the debutant's pre-event rating already carries it
    return [(start[e] - timedelta(seconds=2), p, -c[e] * (0.5 * n + lam) / (0.5 * n), n, n, half_life)
            for p, e in sorted(debut.items()) if c.get(e, 0) > 0]
