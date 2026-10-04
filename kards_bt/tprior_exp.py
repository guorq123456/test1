"""Heavy-tailed (Student-t) prior instead of the Gaussian N(0, 0.4^2).

Why: the Gaussian prior compresses both ends. Out of sample, players with >= 40 matches win more than the
model predicts (mean z +0.59) and debutants less (-0.19); widening the Gaussian reduces the compression but
costs prediction everywhere (residuals.py / prior check). A t prior keeps the same pull toward average for
players with little evidence while letting players with enough evidence sit far from it.

Grid over degrees of freedom nu and scale s (same production corrections: newcomer anchor fitted under the
same prior, ladder-invite credit). DEV = events before 2024 (choose), HOLDOUT = 2024 onward (judge),
event-level paired bootstrap against the Gaussian 0.4 baseline. Also reports the group mean z and the
current ratings of a few players under the DEV-best setting.
"""
import csv
import math
import os
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

import bt
import invites
import newcomers

HL, INV_HL = 240, 120
CONFIGS = [("高斯 0.4（现行）", None, 0.4), ("高斯 0.5", None, 0.5)]
CONFIGS += [(f"t ν={df} s={s}", df, s) for df in (2, 4) for s in (0.3, 0.4, 0.5)]
WATCH = ["失其本心八幡 (Hachiman)", "作死的骡博 (Radish)", "Sie_", "Spoker", "guorq123456", "Jking7", "钟离梓", "Noein5", "青柠梦"]


def main():
    ms = sorted(bt.load_matches({"official"}, False))
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    start = defaultdict(lambda: datetime.max)
    for m in ms:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)[2:]
    total = Counter(p for m in ms for p in (m[1], m[2]))
    credits = invites.credits(lambda t: bt._fit_before(ms, t, HL, 0.4))

    res, zs, boards = {}, {}, {}
    for label, df, sd in CONFIGS:
        fit = lambda *a, **k: bt.fit_bt(*a, **k, prior_df=df)  # noqa: E731
        virt_all = [c + (INV_HL,) for c in credits] + newcomers.anchors(ms, HL, sd, fit, 2)
        gap = newcomers.offsets(ms, HL, sd, fit)[0]
        per_event, acc = {}, defaultdict(lambda: [0.0, 0.0, 0.0])
        snaps = evs + [None]  # None = the final snapshot (current board)
        for ev in snaps:
            t0 = start[ev] if ev else max(m[0] for m in ms)
            past = [m for m in ms if (m[0] < t0 if ev else True)]
            ids = sorted({p for m in past for p in (m[1], m[2])})
            idx = {p: i for i, p in enumerate(ids)}
            w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / HL)
            v = [(idx[p], level, sign, n * 0.5 ** ((t0 - t).total_seconds() / 86400 / hl))
                 for t, p, level, wins, losses, hl in virt_all if t <= t0 and p in idx
                 for sign, n in ((1.0, wins), (-1.0, losses)) if n > 0]
            virtual = tuple(np.array(c) for c in zip(*v)) if v else None
            b, se = fit(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), sd, virtual=virtual)
            if ev is None:
                elo, sd_e = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
                order = sorted((p for p in ids if total[p] >= 10), key=lambda p: -(elo[idx[p]] - sd_e[idx[p]]))
                boards[label] = {names[p]: (i + 1, elo[idx[p]], sd_e[idx[p]]) for i, p in enumerate(order)}
                continue
            r = lambda p: b[idx[p]] if p in idx else -gap.get(ev, 0.0)  # noqa: E731
            out = []
            for m in ms:
                if m[4] != ev:
                    continue
                p = 1 / (1 + math.exp(-(r(m[1]) - r(m[2]))))
                out.append(-math.log(p))
                for q, won, pp in ((m[1], 1, p), (m[2], 0, 1 - p)):
                    a = acc[q]; a[0] += won; a[1] += pp; a[2] += pp * (1 - pp)
            per_event[ev] = out
        res[label] = per_event
        zs[label] = {q: (a[0] - a[1]) / math.sqrt(a[2]) for q, a in acc.items() if a[2] > 0}

    dev = [e for e in evs if start[e].year < 2024]
    hold = [e for e in evs if start[e].year >= 2024]
    base = res[CONFIGS[0][0]]
    ll = lambda r, es: sum(sum(r[e]) for e in es) / sum(len(r[e]) for e in es)  # noqa: E731

    def boot(r, es):
        d = np.array([sum(r[e]) - sum(base[e]) for e in es])
        c = np.array([len(base[e]) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / c[i].sum() for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    def mz(label, lo, hi):
        z = [v for q, v in zs[label].items() if lo <= total[q] < hi]
        return np.mean(z)

    print(f"DEV {sum(len(base[e]) for e in dev)} 场，HOLDOUT {sum(len(base[e]) for e in hold)} 场")
    print(f"{'先验':<18} {'DEV':>7} {'HOLDOUT':>8} {'差 [95%]':>24}   z均值: 老将≥40  中坚15–39  新人5–14")
    b0 = ll(base, hold)
    for label, _, _ in CONFIGS:
        r = res[label]
        h = ll(r, hold)
        lo, hi = boot(r, hold)
        print(f"{label:<18} {ll(r, dev):.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   "
              f"{mz(label, 40, 10**9):+.2f}     {mz(label, 15, 40):+.2f}     {mz(label, 5, 15):+.2f}")
    best = min((c for c in CONFIGS if c[1] is not None), key=lambda c: ll(res[c[0]], dev))
    print(f"\nDEV 上最好的 t 先验：{best[0]}")
    print(f"\n当前榜对比（名次 / BT ±SE）：{'选手':<24}{'高斯 0.4':>22}{best[0]:>22}")
    for n in WATCH:
        a, b_ = boards[CONFIGS[0][0]].get(n), boards[best[0]].get(n)
        fmt = lambda x: f"#{x[0]} {x[1]:.0f}±{x[2]:.0f}" if x else "-"  # noqa: E731
        print(f"{'':<34}{n:<24}{fmt(a):>22}{fmt(b_):>22}")
    top = lambda lab: " / ".join(f"{n} {v[1]:.0f}" for n, v in sorted(boards[lab].items(), key=lambda x: x[1][0])[:8])  # noqa: E731
    print(f"\n高斯 0.4 前 8：{top(CONFIGS[0][0])}\n{best[0]} 前 8：{top(best[0])}")


if __name__ == "__main__":
    main()
