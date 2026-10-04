"""Debut anchor for first-time official players (option C).

First-time official players win less than the model predicts (they start at the field average, 1500, but
are weaker on average). Give every player n virtual draws against an opponent of level -c, dated at their
first official match and fading with the same half-life as real results: newcomers start below average and
real results take over. (c, n) fitted on DEV (events before 2024), scored on HOLDOUT (2024 onward) with an
event-level paired bootstrap. Same half-life / prior as bt.py, no invite credit.
"""
import math
from collections import defaultdict
from datetime import datetime

import numpy as np

from bt import ELO_SCALE, fit_bt, load_matches

HL, SD = 240, 0.4
GRID = [(0.0, 0.0)] + [(c, n) for c in (0.25, 0.5, 0.75, 1.0, 1.5) for n in (2.0, 4.0, 8.0, 16.0, 32.0)]


def run():
    ms = load_matches({"official"}, False)
    start = defaultdict(lambda: datetime.max)
    first = {}
    for m in sorted(ms):
        start[m[4]] = min(start[m[4]], m[0])
        for p in (m[1], m[2]):
            first.setdefault(p, m[0])
    evs = sorted(start, key=start.get)[2:]
    res = {g: {} for g in GRID}  # grid -> event -> [(nll, newcomer side?, p_winner)]
    for ev in evs:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / HL)
        win, lose = np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past])
        fade = np.array([0.5 ** ((t0 - first[p]).total_seconds() / 86400 / HL) for p in ids])
        test = [m for m in ms if m[4] == ev]
        for c, n in GRID:
            virtual = None
            if n > 0:
                k = len(ids)
                virtual = (np.concatenate([np.arange(k)] * 2), np.full(2 * k, -c),
                           np.concatenate([np.ones(k), -np.ones(k)]), np.concatenate([n * fade] * 2))
            b, _ = fit_bt(win, lose, w, len(ids), SD, virtual=virtual)
            out = []
            for m in test:
                # a player never seen before also starts at the anchor (-c) when the anchor is on
                bw = b[idx[m[1]]] if m[1] in idx else (-c * n * 0.5 / (n * 0.5 + 1 / SD ** 2) if n else 0.0)
                bl = b[idx[m[2]]] if m[2] in idx else (-c * n * 0.5 / (n * 0.5 + 1 / SD ** 2) if n else 0.0)
                p = 1 / (1 + math.exp(-(bw - bl)))
                out.append((-math.log(p), m[1] not in idx, m[2] not in idx, p))
            res[(c, n)][ev] = out
    return evs, start, res


def main():
    evs, start, res = run()
    dev = [e for e in evs if start[e].year < 2024]
    hold = [e for e in evs if start[e].year >= 2024]
    tot = lambda g, es: sum(x[0] for e in es for x in res[g][e])  # noqa: E731
    cnt = lambda es: sum(len(res[GRID[0]][e]) for e in es)  # noqa: E731
    print(f"DEV {cnt(dev)} 场，HOLDOUT {cnt(hold)} 场")
    print("c（低于平均多少）  n（虚拟和局数）  DEV log loss   HOLDOUT log loss")
    for g in GRID:
        print(f"  {g[0]:.2f}（{g[0] * ELO_SCALE:.0f} 分）  {g[1]:.0f}   {tot(g, dev) / cnt(dev):.4f}   {tot(g, hold) / cnt(hold):.4f}")
    best = min(GRID[1:], key=lambda g: tot(g, dev))
    base = GRID[0]
    d = np.array([tot(best, [e]) - tot(base, [e]) for e in hold])
    c = np.array([cnt([e]) for e in hold])
    rng = np.random.default_rng(1)
    bs = [d[i].sum() / c[i].sum() for i in (rng.integers(0, len(hold), len(hold)) for _ in range(4000))]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"\nDEV 上最好：c={best[0]}（{best[0] * ELO_SCALE:.0f} 分），n={best[1]:.0f}")
    print(f"HOLDOUT 相对无锚点：{d.sum() / c.sum():+.4f}  95% 区间 [{lo:+.4f}, {hi:+.4f}]")
    for g, lab in ((base, "无锚点"), (best, "有锚点")):
        a = [0.0, 0.0, 0]
        for e in hold:
            for nll, nw, nl, p in res[g][e]:
                if nw:
                    a[0] += 1; a[1] += p; a[2] += 1
                if nl:
                    a[1] += 1 - p; a[2] += 1
        print(f"  {lab}：首次参加官方赛的选手 {a[2]} 人次，实际胜率 {a[0] / a[2]:.3f}，预测 {a[1] / a[2]:.3f}")


if __name__ == "__main__":
    main()
