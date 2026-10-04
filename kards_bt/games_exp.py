"""Game-level evidence: fit on individual games (a 2-0 is two wins, a 2-1 two wins and a loss) with a per-game
weight w_g, instead of one result per series. Judged on predicting the SERIES winner, out of sample
(DEV < 2024 to choose w_g, HOLDOUT >= 2024, event-level bootstrap vs the series model). Production corrections
(newcomer anchor, ladder-invite credit) are fitted the same way in every variant.

Motivation: dominant players (sweeps) are the ones the prior shrinks most visibly (residuals.py: 八幡, 骡博,
dandelion at z +2.7); games give them more evidence per match without changing the model.
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

HL, SD, INV_HL = 240, 0.4, 120
WATCH = ["失其本心八幡 (Hachiman)", "作死的骡博 (Radish)", "dandelion882691", "Sie_", "Spoker", "hqt18", "guorq123456", "Jking7", "钟离梓", "Noein5"]


def main():
    series = sorted(bt.load_matches({"official"}, False))
    games = sorted(bt.load_matches({"official"}, True))
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    start = defaultdict(lambda: datetime.max)
    for m in series:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)[2:]
    total = Counter(p for m in series for p in (m[1], m[2]))
    n_series_games = sum(m[3] for m in games) / len(series)
    print(f"每个系列赛平均 {n_series_games:.2f} 小局")

    variants = {"按场（现行）": (series, 1.0)}
    for wg in (0.4, 0.6, 0.8, 1.0):
        variants[f"按小局 w={wg}"] = (games, wg)
    res, zs, boards = {}, {}, {}
    for label, (train, wg) in variants.items():
        train = [(t, w, l, k * wg, e) for t, w, l, k, e in train]
        credits = invites.credits(lambda t: bt._fit_before(train, t, HL, SD))
        virt_all = [c + (INV_HL,) for c in credits] + newcomers.anchors(train, HL, SD, bt.fit_bt, 2)
        gap = newcomers.offsets(train, HL, SD, bt.fit_bt)[0]
        per_event, acc = {}, defaultdict(lambda: [0.0, 0.0, 0.0])
        for ev in evs + [None]:
            t0 = start[ev] if ev else max(m[0] for m in train)
            past = [m for m in train if (m[0] < t0 if ev else True)]
            ids = sorted({p for m in past for p in (m[1], m[2])})
            idx = {p: i for i, p in enumerate(ids)}
            w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / HL) * np.array([m[3] for m in past])
            v = [(idx[p], level, sign, n * 0.5 ** ((t0 - t).total_seconds() / 86400 / hl))
                 for t, p, level, wins, losses, hl in virt_all if t <= t0 and p in idx
                 for sign, n in ((1.0, wins), (-1.0, losses)) if n > 0]
            virtual = tuple(np.array(c) for c in zip(*v)) if v else None
            b, se = bt.fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), SD, virtual=virtual)
            if ev is None:
                elo, sd_e = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
                order = sorted((p for p in ids if total[p] >= 10), key=lambda p: -(elo[idx[p]] - sd_e[idx[p]]))
                boards[label] = {names[p]: (i + 1, elo[idx[p]], sd_e[idx[p]]) for i, p in enumerate(order)}
                continue
            r = lambda p: b[idx[p]] if p in idx else -gap.get(ev, 0.0)  # noqa: E731
            out = []
            for m in series:
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
    base = res["按场（现行）"]
    ll = lambda r, es: sum(sum(r[e]) for e in es) / sum(len(r[e]) for e in es)  # noqa: E731

    def boot(r, es):
        d = np.array([sum(r[e]) - sum(base[e]) for e in es])
        c = np.array([len(base[e]) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / c[i].sum() for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    pid = {v: k for k, v in names.items()}
    print(f"DEV {sum(len(base[e]) for e in dev)} 场，HOLDOUT {sum(len(base[e]) for e in hold)} 场（都按系列赛胜负打分）")
    print(f"{'方案':<14} {'DEV':>7} {'HOLDOUT':>8} {'差 [95%]':>24}  z均值 老将≥40  |  八幡 / 骡博 / dandelion 的 z")
    b0 = ll(base, hold)
    for label, r in res.items():
        h = ll(r, hold)
        lo, hi = boot(r, hold)
        z = zs[label]
        zv = np.mean([v for q, v in z.items() if total[q] >= 40])
        trio = " / ".join(f"{z.get(pid[n], float('nan')):+.2f}" for n in WATCH[:3])
        print(f"{label:<14} {ll(r, dev):.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   {zv:+.2f}        {trio}")
    best = min((k for k in variants if k != "按场（现行）"), key=lambda k: ll(res[k], dev))
    print(f"\nDEV 上最好：{best}\n\n当前榜对比（名次 / BT ±SE）")
    for n in WATCH:
        a, b_ = boards["按场（现行）"].get(n), boards[best].get(n)
        fmt = lambda x: f"#{x[0]} {x[1]:.0f}±{x[2]:.0f}" if x else "-"  # noqa: E731
        print(f"  {n:<24}{fmt(a):>18}  →{fmt(b_):>18}")
    top = lambda lab: " / ".join(f"{n} {v[1]:.0f}" for n, v in sorted(boards[lab].items(), key=lambda x: x[1][0])[:10])  # noqa: E731
    print(f"\n按场 前 10：{top('按场（现行）')}\n{best} 前 10：{top(best)}")


if __name__ == "__main__":
    main()
