"""Why do veterans fade slowly, and does an inactivity / stale-evidence adjustment predict better?

Out-of-sample on official events (fit before each event, prior / half-life as bt.py, no invite credit).
For each player at prediction time we record
  gap  = days since their last official match,
  age  = weight-averaged age (days) of the evidence behind their rating.
Then test adjusted ratings  b' = b - k * f(player)  with k fitted on DEV (events before 2024) and
scored on HOLDOUT (2024 onward), event-level paired bootstrap.
"""
import csv
import math
import os
from collections import defaultdict
from datetime import datetime

import numpy as np

from bt import DATA, fit_bt, load_matches

HL, SD = 240, 0.4


def collect():
    ms = load_matches({"official"}, False)
    start = defaultdict(lambda: datetime.max)
    for m in ms:
        start[m[4]] = min(start[m[4]], m[0])
    evs = sorted(start, key=start.get)[2:]
    out = []  # (event, year, b_w, b_l, feat_w, feat_l) ; outcome = winner listed first
    for ev in evs:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        age = np.array([(t0 - m[0]).total_seconds() / 86400 for m in past])
        w = 0.5 ** (age / HL)
        b, _ = fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), SD)
        last, wsum, agesum = {}, defaultdict(float), defaultdict(float)
        for m, a, wt in zip(past, age, w):
            for p in (m[1], m[2]):
                last[p] = min(last.get(p, 1e9), a)
                wsum[p] += wt
                agesum[p] += wt * a
        feat = lambda p: (last.get(p, None), agesum[p] / wsum[p] if p in wsum else None, wsum.get(p, 0.0))  # noqa: E731
        for m in ms:
            if m[4] == ev:
                bw = b[idx[m[1]]] if m[1] in idx else 0.0
                bl = b[idx[m[2]]] if m[2] in idx else 0.0
                out.append((ev, t0.year, bw, bl, feat(m[1]), feat(m[2])))
    return out


def main():
    rows = collect()
    # 1) diagnostics: how does a player's actual win rate compare with the model, by gap and evidence age
    def table(name, key, bins):
        print(f"\n{name}：实际胜率 − 模型预测（正 = 模型低估，负 = 模型高估）")
        acc = defaultdict(lambda: [0.0, 0.0, 0])
        for ev, yr, bw, bl, fw, fl in rows:
            p = 1 / (1 + math.exp(-(bw - bl)))
            for f, won, pp in ((fw, 1, p), (fl, 0, 1 - p)):
                v = key(f)
                if v is None:
                    continue
                for lo, hi, lab in bins:
                    if lo <= v < hi:
                        a = acc[lab]; a[0] += won; a[1] += pp; a[2] += 1
        for _, _, lab in bins:
            a = acc[lab]
            if a[2]:
                print(f"  {lab:<14} {a[2]:>5} 人次  实际 {a[0] / a[2]:.3f}  预测 {a[1] / a[2]:.3f}  差 {(a[0] - a[1]) / a[2]:+.3f}")
    table("距上次出赛", lambda f: f[0], [(0, 45, "≤45 天"), (45, 120, "45–120 天"), (120, 240, "120–240 天"), (240, 1e9, ">240 天")])
    table("分数背后证据的平均年龄", lambda f: f[1], [(0, 120, "<120 天"), (120, 240, "120–240 天"), (240, 360, "240–360 天"), (360, 1e9, ">360 天")])

    # 2) adjustments, k fitted on DEV, scored on HOLDOUT
    def ll(rs, k, fn):
        s = 0.0
        for ev, yr, bw, bl, fw, fl in rs:
            d = bw - k * fn(fw) - (bl - k * fn(fl))
            s += -math.log(1 / (1 + math.exp(-d)))
        return s
    dev = [r for r in rows if r[1] < 2024]
    hold = [r for r in rows if r[1] >= 2024]
    known = lambda f: f[0] is not None  # noqa: E731
    variants = {
        "无调整": lambda f: 0.0,
    }
    for tau in (120, 240, 365):
        variants[f"久未出赛扣分 τ={tau}"] = (lambda tau: lambda f: (1 - 0.5 ** (f[0] / tau)) if known(f) else 0.0)(tau)
    for a0 in (180, 270, 365):
        variants[f"旧证据扣分 >{a0}天"] = (lambda a0: lambda f: max(0.0, f[1] - a0) / 365 if known(f) else 0.0)(a0)
    base_h = None
    print(f"\nDEV {len(dev)} 场（2024 前），HOLDOUT {len(hold)} 场（2024 起）")
    for name, fn in variants.items():
        ks = [0.0] if name == "无调整" else np.linspace(-0.5, 1.0, 61)
        k = min(ks, key=lambda k: ll(dev, k, fn))
        h = ll(hold, k, fn) / len(hold)
        base_h = h if base_h is None else base_h
        # bootstrap over holdout events
        evs = sorted({r[0] for r in hold})
        per = {e: [r for r in hold if r[0] == e] for e in evs}
        d = np.array([ll(per[e], k, fn) - ll(per[e], 0.0, variants["无调整"]) for e in evs])
        c = np.array([len(per[e]) for e in evs])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / c[i].sum() for i in (rng.integers(0, len(evs), len(evs)) for _ in range(3000))]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"  {name:<18} k={k:.3f}（{k * 400 / math.log(10):.0f} 分）  HOLDOUT log loss {h:.4f}  差 {h - base_h:+.4f} [{lo:+.4f}, {hi:+.4f}]")


if __name__ == "__main__":
    main()
