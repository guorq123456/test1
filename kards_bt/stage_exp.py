"""Two fixes for ratings inflated by qualifier wins over newcomers (out-of-sample, official events).

A. Adaptive newcomer start: before each event, estimate how far below average debutants really were
   over the previous 365 days (from earlier out-of-sample predictions only), and anchor each new player
   there at their debut; the anchor fades with the same half-life as real results. Free parameter: the
   anchor strength n (virtual draws), chosen on DEV.
B. Qualifier weight: qualifier / Swiss / group-stage results count w times a main-stage result.

DEV = events before 2024 (choose settings), HOLDOUT = 2024 onward (judge), event-level paired bootstrap.
Also reported: log loss on main-stage matches only, and how qualifier-built players and debutants are
predicted in main stages.
"""
import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

from bt import DATA, fit_bt, parse_time
from placements import stage_name

HL, SD = 240, 0.4
LAM = 1 / SD ** 2
PRE = {"资格赛", "瑞士轮", "小组赛"}
MAIN = {"8 强", "16 强", "总决赛", "邀请赛", "32 强", "淘汰赛"}


def load():
    rows = [r for r in csv.DictReader(open(f"{DATA}/matches.csv")) if r["valid"] == "1" and r["category"] == "official"]
    ms = []
    for r in rows:
        w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
        ms.append((parse_time(r["time"]), w, l, r["event"], stage_name(r["event"], r["stage"], r["stage_type"])))
    ms.sort()
    start = defaultdict(lambda: datetime.max)
    debut = {}
    for m in ms:
        start[m[3]] = min(start[m[3]], m[0])
        for p in (m[1], m[2]):
            debut.setdefault(p, m[3])
    return ms, start, debut


def offset(samples):
    """Logit shift c (newcomers weaker by c) that best explains [(d_winner_minus_loser, debut_w, debut_l)]."""
    c = 0.0
    for _ in range(30):
        g = h = 0.0
        for d, dw, dl in samples:
            s = dl - dw  # d' = d + c * (dl - dw)
            if not s:
                continue
            p = 1 / (1 + math.exp(-(d + c * s)))
            g += (1 - p) * s
            h += p * (1 - p) * s * s
        if h == 0:
            return 0.0
        c += g / h
    return max(c, 0.0)


def run(ms, start, debut, n_anchor, wq, chat=None):
    """Returns ({event: [(nll, main?, featW, featL)]}, {event: [(d, debut_w, debut_l)]})."""
    evs = sorted(start, key=start.get)
    first_t = {p: start[e] for p, e in debut.items()}
    res, dbg = {}, {}
    for ev in evs[2:]:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        age = np.array([(t0 - m[0]).total_seconds() / 86400 for m in past])
        w = 0.5 ** (age / HL) * np.array([wq if m[4] in PRE else 1.0 for m in past])
        c_now = chat.get(ev, 0.0) if chat else 0.0
        virtual = None
        if n_anchor and chat:
            k, lv, wt = [], [], []
            for p, i in idx.items():
                c = chat.get(debut[p], 0.0)
                if c <= 0:
                    continue
                fade = 0.5 ** ((t0 - first_t[p]).total_seconds() / 86400 / HL)
                k.append(i)
                lv.append(-c * (0.5 * n_anchor + LAM) / (0.5 * n_anchor))  # a player with no results sits at -c
                wt.append(n_anchor * fade)
            if k:
                k, lv, wt = np.array(k), np.array(lv), np.array(wt)
                virtual = (np.concatenate([k, k]), np.concatenate([lv, lv]),
                           np.concatenate([np.ones(len(k)), -np.ones(len(k))]), np.concatenate([wt, wt]))
        b, _ = fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), SD, virtual=virtual)
        src, tot = defaultdict(float), defaultdict(float)
        for m, wt in zip(past, 0.5 ** (age / HL)):
            for p in (m[1], m[2]):
                tot[p] += wt
                src[p] += wt * (m[4] in PRE)
        rate = lambda p: b[idx[p]] if p in idx else (-c_now if n_anchor else 0.0)  # noqa: E731
        feat = lambda p: (p not in idx, src[p] / tot[p] if tot[p] else None)  # noqa: E731
        out, dd = [], []
        for m in ms:
            if m[3] != ev:
                continue
            d = rate(m[1]) - rate(m[2])
            out.append((math.log1p(math.exp(-d)), m[4] in MAIN, feat(m[1]), feat(m[2]), 1 / (1 + math.exp(-d))))
            dd.append((d, m[1] not in idx, m[2] not in idx))
        res[ev], dbg[ev] = out, dd
    return res, dbg


def main():
    ms, start, debut = load()
    evs = sorted(start, key=start.get)[2:]
    # baseline predictions give the debutant residuals that the adaptive offset is estimated from
    base, dbg = run(ms, start, debut, 0, 1.0)
    chat = {}
    for ev in sorted(start, key=start.get):
        t0 = start[ev]
        window = [x for e in evs if t0 - timedelta(days=365) <= start[e] < t0 for x in dbg[e]]
        if sum(1 for _, a, b in window if a != b) < 30:  # too few debut matches: use all history
            window = [x for e in evs if start[e] < t0 for x in dbg[e]]
        chat[ev] = offset(window) if window else 0.0
    print("新人比平均弱多少（logit，每站赛前估计，近 365 天）：")
    for y in (2022, 2023, 2024, 2025, 2026):
        v = [chat[e] for e in evs if start[e].year == y]
        if v:
            print(f"  {y}: 平均 {np.mean(v):.2f}（约 {np.mean(v) * 400 / math.log(10):.0f} 分）")

    dev = [e for e in evs if start[e].year < 2024]
    hold = [e for e in evs if start[e].year >= 2024]
    configs = {("无修正", 0, 1.0): base}
    for n in (2, 4, 8, 16):
        configs[(f"A 新人起点 n={n}", n, 1.0)] = run(ms, start, debut, n, 1.0, chat)[0]
    for wq in (0.75, 0.5, 0.25):
        configs[(f"B 预选权重 {wq}", 0, wq)] = run(ms, start, debut, 0, wq)[0]

    def ll(r, es, sel=lambda x: True):
        xs = [x for e in es for x in r[e] if sel(x)]
        return sum(x[0] for x in xs) / len(xs), len(xs)

    def boot(r, es, sel=lambda x: True):
        d = np.array([sum(x[0] for x in r[e] if sel(x)) - sum(x[0] for x in base[e] if sel(x)) for e in es])
        c = np.array([sum(1 for x in base[e] if sel(x)) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / max(c[i].sum(), 1) for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    main_sel = lambda x: x[1]  # noqa: E731
    print(f"\nDEV {ll(base, dev)[1]} 场（正赛 {ll(base, dev, main_sel)[1]}），HOLDOUT {ll(base, hold)[1]} 场（正赛 {ll(base, hold, main_sel)[1]}）")
    print(f"{'方案':<16} {'DEV':>7} {'HOLDOUT':>8} {'差 [95%]':>22} {'HOLDOUT 正赛':>12} {'差 [95%]':>22}")
    b0, b0m = ll(base, hold)[0], ll(base, hold, main_sel)[0]
    for (name, n, wq), r in configs.items():
        h, hm = ll(r, hold)[0], ll(r, hold, main_sel)[0]
        lo, hi = boot(r, hold)
        lom, him = boot(r, hold, main_sel)
        print(f"{name:<16} {ll(r, dev)[0]:.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   {hm:.4f}  {hm - b0m:+.4f} [{lom:+.4f},{him:+.4f}]")
    bestA = min((k for k in configs if k[1]), key=lambda k: ll(configs[k], dev)[0])
    bestB = min((k for k in configs if k[2] < 1), key=lambda k: ll(configs[k], dev)[0])
    both = run(ms, start, debut, bestA[1], bestB[2], chat)[0]
    configs[(f"A+B（n={bestA[1]}, w={bestB[2]}）", bestA[1], bestB[2])] = both
    h, hm = ll(both, hold)[0], ll(both, hold, main_sel)[0]
    lo, hi = boot(both, hold)
    lom, him = boot(both, hold, main_sel)
    print(f"{'A+B':<16} {ll(both, dev)[0]:.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   {hm:.4f}  {hm - b0m:+.4f} [{lom:+.4f},{him:+.4f}]")
    print(f"DEV 上选出：A 用 n={bestA[1]}，B 用 w={bestB[2]}")

    print("\nHOLDOUT 正赛里两类人的 实际 − 预测 胜率（负 = 被高估）：")
    for key in (("无修正", 0, 1.0), bestA, bestB, list(configs)[-1]):
        r = configs[key]
        acc = defaultdict(lambda: [0.0, 0.0, 0])
        for e in hold:
            for nll, is_main, fw, fl, p in r[e]:
                if not is_main:
                    continue
                for f, won, pp in ((fw, 1, p), (fl, 0, 1 - p)):
                    for lab, ok in (("第一次出现", f[0]), ("分数≥80%来自预选", f[1] is not None and f[1] >= 0.8)):
                        if ok:
                            a = acc[lab]; a[0] += won; a[1] += pp; a[2] += 1
        print(f"  {key[0]:<18} " + "  ".join(f"{lab} {(a[0] - a[1]) / a[2]:+.3f}（{a[2]}）" for lab, a in acc.items()))


if __name__ == "__main__":
    main()
