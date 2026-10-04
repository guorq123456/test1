"""Add the Open series' MAIN stages (Top 16 / Top 8 / finals, 214 matches, 2020-2023) to the official data.

The Open series was dropped because its qualifiers have no entry bar. Its main stages are matches between
players who already came through, and they cover the years where the ladder-invite credit carries the most
weight. Variants: official only (production), official + Open main stages at weight 1 and at weight 0.5.
Judged out of sample on official matches (DEV < 2024 / HOLDOUT >= 2024, event bootstrap), with the group
mean z and the current / peak (hindsight) board for a few players.
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
from placements import stage_name

HL, SD, INV_HL = 240, 0.4, 120
MAIN = {"8 强", "16 强", "总决赛", "邀请赛", "32 强", "淘汰赛"}
WATCH = ["Jking7", "Noein5", "钟离梓", "Bezio", "dandelion882691", "Head", "Vinny", "Kolbasnik", "guorq123456", "失其本心八幡 (Hachiman)"]


def load():
    official = sorted(bt.load_matches({"official"}, False))
    open_main = []
    for r in csv.DictReader(open(os.path.join(bt.DATA, "matches.csv"))):
        if r["valid"] == "1" and r["category"] in ("open", "open_special") and stage_name(r["event"], r["stage"], r["stage_type"]) in MAIN:
            w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
            open_main.append((bt.parse_time(r["time"]), w, l, 1.0, r["event"]))
    return official, sorted(open_main)


def run(train, official, names, total):
    start = defaultdict(lambda: datetime.max)
    for m in official:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)[2:]
    credits = [c + (INV_HL,) for c in invites.credits(lambda t: bt._fit_before(train, t, HL, SD))]
    virt_all = credits + newcomers.anchors(train, HL, SD, bt.fit_bt, 2)
    gap = newcomers.offsets(train, HL, SD, bt.fit_bt)[0]
    ids = sorted({p for m in train for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    W, L = np.array([idx[m[1]] for m in train]), np.array([idx[m[2]] for m in train])
    T = np.array([m[0].timestamp() for m in train])
    K = np.array([m[3] for m in train])

    def fit_at(t, two_sided):
        d = (np.abs(t.timestamp() - T) if two_sided else (t.timestamp() - T)) / 86400
        sel = np.ones(len(train), bool) if two_sided else d > 0
        w = 0.5 ** (d[sel] / HL) * K[sel]
        v = []
        for tc, p, level, wins, losses, hl in virt_all:
            if p not in idx or (not two_sided and tc >= t):
                continue
            f = 0.5 ** (abs((t - tc).total_seconds()) / 86400 / hl)
            v += [(idx[p], level, 1.0, wins * f), (idx[p], level, -1.0, losses * f)]
        b, se = bt.fit_bt(W[sel], L[sel], w, len(ids), SD, virtual=tuple(np.array(c) for c in zip(*v)) if v else None)
        return b, se

    per_event, acc = {}, defaultdict(lambda: [0.0, 0.0, 0.0])
    for ev in evs:
        t0 = start[ev]
        b, _ = fit_at(t0, False)
        seen = {p for m in train if m[0] < t0 for p in (m[1], m[2])}
        r = lambda p: b[idx[p]] if p in seen else -gap.get(ev, 0.0)  # noqa: E731
        out = []
        for m in official:
            if m[4] != ev:
                continue
            p = 1 / (1 + math.exp(-(r(m[1]) - r(m[2]))))
            out.append(-math.log(p))
            for q, won, pp in ((m[1], 1, p), (m[2], 0, 1 - p)):
                a = acc[q]; a[0] += won; a[1] += pp; a[2] += pp * (1 - pp)
        per_event[ev] = out
    z = {q: (a[0] - a[1]) / math.sqrt(a[2]) for q, a in acc.items() if a[2] > 0}

    t_last = max(m[0] for m in official)
    b, se = fit_at(t_last, False)
    e, s = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
    order = sorted((p for p in ids if total[p] >= 10), key=lambda p: -(e[idx[p]] - s[idx[p]]))
    cur = {names[p]: (i + 1, e[idx[p]]) for i, p in enumerate(order)}

    peak, played, k = {}, Counter(), 0
    for t, ev in bt.event_snapshots(official):
        while k < len(train) and train[k][0] <= t:
            played[train[k][1]] += 1; played[train[k][2]] += 1; k += 1
        b, se = fit_at(t, True)
        e, s = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
        board = sorted(((e[idx[p]] - s[idx[p]], p) for p, n in played.items() if n >= 10), reverse=True)
        for rank, (sc, p) in enumerate(board, 1):
            if p not in peak or sc > peak[p][0]:
                peak[p] = (sc, t.strftime("%Y-%m"), rank)
    porder = sorted(peak, key=lambda p: -peak[p][0])
    pk = {names[p]: (i + 1, peak[p][1], peak[p][2]) for i, p in enumerate(porder)}
    return per_event, z, cur, pk, [names[p] for p in porder[:10]], start


def main():
    official, open_main = load()
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    total = Counter(p for m in official for p in (m[1], m[2]))  # the 10-match bar counts official matches only
    print(f"官方 {len(official)} 场，Open 正赛 {len(open_main)} 场")
    variants = {"仅官方（现行）": official}
    for wo in (1.0, 0.5):
        variants[f"+Open 正赛 w={wo}"] = sorted(official + [(t, w, l, wo, e) for t, w, l, _, e in open_main])
    res = {lab: run(tr, official, names, total) for lab, tr in variants.items()}
    base_pe, _, _, _, _, start = res["仅官方（现行）"]
    evs = list(base_pe)
    dev = [e for e in evs if start[e].year < 2024]
    hold = [e for e in evs if start[e].year >= 2024]
    ll = lambda pe, es: sum(sum(pe[e]) for e in es) / sum(len(pe[e]) for e in es)  # noqa: E731

    def boot(pe, es):
        d = np.array([sum(pe[e]) - sum(base_pe[e]) for e in es])
        c = np.array([len(base_pe[e]) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / c[i].sum() for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    print(f"\n{'方案':<16} {'DEV':>7} {'HOLDOUT':>8} {'差 [95%]':>24}  z均值 老将≥40 / 中坚 / 新人")
    b0 = ll(base_pe, hold)
    for lab, (pe, z, *_) in res.items():
        h = ll(pe, hold); lo, hi = boot(pe, hold)
        mz = lambda a, b_: np.mean([v for q, v in z.items() if a <= total[q] < b_])  # noqa: E731
        print(f"{lab:<16} {ll(pe, dev):.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   {mz(40, 10**9):+.2f} / {mz(15, 40):+.2f} / {mz(5, 15):+.2f}")
    print("\n当前榜（名次 BT）")
    print(f"{'':<26}" + "".join(f"{lab:>22}" for lab in res))
    for n in WATCH:
        print(f"{n:<26}" + "".join((f"#{c[n][0]} {c[n][1]:.0f}" if n in c else "–").rjust(22) for _, _, c, *_ in res.values()))
    print("\n巅峰榜（名次，巅峰月，当时第几）")
    print(f"{'':<26}" + "".join(f"{lab:>22}" for lab in res))
    for n in WATCH:
        print(f"{n:<26}" + "".join((f"#{p[n][0]} {p[n][1]} 当时#{p[n][2]}" if n in p else "–").rjust(22) for _, _, _, p, *_ in res.values()))
    for lab, (_, _, _, _, top, _) in res.items():
        print(f"巅峰前 10 · {lab}: {' / '.join(top)}")


if __name__ == "__main__":
    main()
