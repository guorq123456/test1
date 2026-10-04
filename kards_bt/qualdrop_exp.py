"""What if qualifier results are not used at all?

A: drop the OCC monthly qualifiers (Swiss / group stages of other events kept).  B: main stages only, everywhere.
Both without the ladder-invite credit (it compensates invitees for qualifier wins nobody banks any more).
Judged out of sample on MAIN-STAGE matches (the fair test: those are rated in every variant), DEV < 2024 /
HOLDOUT >= 2024 with an event bootstrap; all-match numbers and the boards are reported alongside.
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
from normalize import MAIN, stage_name

HL, SD, INV_HL = 240, 0.4, 120
WATCH = ["Jking7", "钟离梓", "Noein5", "Bezio", "dandelion882691", "guorq123456", "Head", "失其本心八幡 (Hachiman)", "Sie_", "hqt18", "Spoker", "禁忌之门", "66better"]


def load():
    rows = [r for r in csv.DictReader(open(os.path.join(bt.DATA, "matches.csv"))) if r["valid"] == "1" and r["category"] in bt.RATED]
    out = []
    for r in rows:
        w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
        lab = stage_name(r["event"], r["stage"] or "", r["stage_type"] or "")
        out.append((bt.parse_time(r["time"]), w, l, 1.0, r["event"], lab, lab in MAIN, bool(invites.MONTH.match(r["event"])) and lab == "资格赛"))
    return sorted(out)


def run(train, test, use_credit, names):
    tr = [m[:5] for m in train]
    start = defaultdict(lambda: datetime.max)
    for m in test:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)[2:]
    virt = [c + (INV_HL,) for c in invites.credits(lambda t: bt._fit_before(tr, t, HL, SD))] if use_credit else []
    virt += newcomers.anchors(tr, HL, SD, bt.fit_bt, 2)
    gap = newcomers.offsets(tr, HL, SD, bt.fit_bt)[0]
    ids = sorted({p for m in tr for p in (m[1], m[2])}); idx = {p: i for i, p in enumerate(ids)}
    W, L = np.array([idx[m[1]] for m in tr]), np.array([idx[m[2]] for m in tr])
    T = np.array([m[0].timestamp() for m in tr])
    n_train = Counter(p for m in tr for p in (m[1], m[2]))

    def fit_at(t, two_sided):
        d = (np.abs(t.timestamp() - T) if two_sided else (t.timestamp() - T)) / 86400
        sel = np.ones(len(tr), bool) if two_sided else d > 0
        v = []
        for tc, p, level, wins, losses, hl in virt:
            if p not in idx or (not two_sided and tc >= t):
                continue
            f = 0.5 ** (abs((t - tc).total_seconds()) / 86400 / hl)
            v += [(idx[p], level, 1.0, wins * f), (idx[p], level, -1.0, losses * f)]
        return bt.fit_bt(W[sel], L[sel], 0.5 ** (d[sel] / HL), len(ids), SD, virtual=tuple(np.array(c) for c in zip(*v)) if v else None)

    per_event = {}
    for ev in evs:
        t0 = start[ev]
        b, _ = fit_at(t0, False)
        seen = {p for m in tr if m[0] < t0 for p in (m[1], m[2])}
        r = lambda p: b[idx[p]] if p in seen else -gap.get(ev, 0.0)  # noqa: E731
        per_event[ev] = [(-math.log(1 / (1 + math.exp(-(r(m[1]) - r(m[2]))))), m[6]) for m in test if m[4] == ev]
    t_last = max(m[0] for m in test)
    b, se = fit_at(t_last, False)
    e, s = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
    order = sorted((p for p in ids if n_train[p] >= 10), key=lambda p: -(e[idx[p]] - s[idx[p]]))
    cur = {names[p]: (i + 1, e[idx[p]]) for i, p in enumerate(order)}
    peak, played, k = {}, Counter(), 0
    for t, ev in bt.event_snapshots(tr):
        while k < len(tr) and tr[k][0] <= t:
            played[tr[k][1]] += 1; played[tr[k][2]] += 1; k += 1
        b, se = fit_at(t, True)
        e, s = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
        for rank, (sc, p) in enumerate(sorted(((e[idx[p]] - s[idx[p]], p) for p, n in played.items() if n >= 10), reverse=True), 1):
            if p not in peak or sc > peak[p][0]:
                peak[p] = (sc, t.strftime("%Y-%m"), rank)
    porder = sorted(peak, key=lambda p: -peak[p][0])
    return per_event, cur, {names[p]: (i + 1, peak[p][1]) for i, p in enumerate(porder)}, [names[p] for p in porder[:10]], start, len(order)


def main():
    ms = load()
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    n_main = sum(1 for m in ms if m[6]); n_occq = sum(1 for m in ms if m[7])
    print(f"计分对局 {len(ms)}：正赛 {n_main}，OCC 资格赛 {n_occq}，其他预选/瑞士/小组 {len(ms) - n_main - n_occq}")
    variants = {
        "现行（全部 + 直邀补偿）": ([m for m in ms], True),
        "A 去掉 OCC 预选": ([m for m in ms if not m[7]], False),
        "B 只用正赛": ([m for m in ms if m[6]], False),
    }
    res = {lab: run(tr, ms, cr, names) for lab, (tr, cr) in variants.items()}
    base_pe, _, _, _, start, _ = res["现行（全部 + 直邀补偿）"]
    evs = list(base_pe)
    dev = [e for e in evs if start[e].year < 2024]; hold = [e for e in evs if start[e].year >= 2024]
    ll = lambda pe, es, mainonly: (lambda xs: sum(xs) / len(xs))([x for e in es for x, mn in pe[e] if mn or not mainonly])  # noqa: E731

    def boot(pe, es, mainonly):
        d = np.array([sum(x for x, mn in pe[e] if mn or not mainonly) - sum(x for x, mn in base_pe[e] if mn or not mainonly) for e in es])
        c = np.array([sum(1 for x, mn in base_pe[e] if mn or not mainonly) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / max(c[i].sum(), 1) for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    nm = sum(1 for e in hold for x, mn in base_pe[e] if mn); na = sum(len(base_pe[e]) for e in hold)
    print(f"\nHOLDOUT（2024 起）：正赛 {nm} 场 / 全部 {na} 场")
    print(f"{'方案':<22} {'正赛 DEV':>9} {'正赛 HOLDOUT':>12} {'差 [95%]':>24} | {'全部 HOLDOUT':>12} {'差':>8}   上榜人数")
    b0m, b0a = ll(base_pe, hold, True), ll(base_pe, hold, False)
    for lab, (pe, cur, pk, top, _, nboard) in res.items():
        hm, ha = ll(pe, hold, True), ll(pe, hold, False)
        lo, hi = boot(pe, hold, True)
        print(f"{lab:<22} {ll(pe, dev, True):>9.4f} {hm:>12.4f}  {hm - b0m:+.4f} [{lo:+.4f},{hi:+.4f}] | {ha:>12.4f} {ha - b0a:>+8.4f}   {nboard}")
    print("\n当前榜（名次 BT）")
    print(f"{'':<26}" + "".join(f"{lab:>24}" for lab in res))
    for n in WATCH:
        print(f"{n:<26}" + "".join((f"#{c[n][0]} {c[n][1]:.0f}" if n in c else "– (不足10场)").rjust(24) for _, c, *_ in res.values()))
    print("\n巅峰榜（名次 巅峰月）")
    print(f"{'':<26}" + "".join(f"{lab:>24}" for lab in res))
    for n in WATCH:
        print(f"{n:<26}" + "".join((f"#{p[n][0]} {p[n][1]}" if n in p else "–").rjust(24) for _, _, p, *_ in res.values()))
    for lab, (_, _, _, top, _, _) in res.items():
        print(f"巅峰前 10 · {lab}: {' / '.join(top)}")


if __name__ == "__main__":
    main()
