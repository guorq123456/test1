"""Does the Open series help or hurt? Out-of-sample test on official (OCC / WC / expansion / seasonal) matches.

Every official event is predicted from a fit on everything before it starts; the only thing that changes
between runs is the weight given to Open-series results (1 = current model, 0 = official data only).
Same half-life / prior as bt.py; no ladder-invite credit in any run, so the comparison is like for like.
DEV = events before 2023, HOLDOUT = 2023 onward; the difference vs weight 1 gets an event-level paired bootstrap.
"""
import csv
import math
import os
from collections import defaultdict
from datetime import datetime

import numpy as np

from bt import DATA, fit_bt, parse_time

HALF_LIFE, PRIOR_SD = 240, 0.8
WEIGHTS = [1.0, 0.5, 0.25, 0.0]


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(DATA, "matches.csv")))
            if r["valid"] == "1" and r["category"] in ("open", "open_special", "official")]
    ms = []
    for r in rows:
        w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
        ms.append((parse_time(r["time"]), w, l, r["category"] != "official", r["event"]))
    start = defaultdict(lambda: datetime.max)
    for m in ms:
        start[m[4]] = min(start[m[4]], m[0])
    official = sorted({m[4] for m in ms if not m[3]}, key=lambda e: start[e])[2:]  # skip the first two (no history)

    # per event, per weight: list of (logloss, correct, new-player match?)
    res = {w: {} for w in WEIGHTS}
    for ev in official:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        test = [m for m in ms if m[4] == ev]
        for wo in WEIGHTS:
            use = [m for m in past if not m[3] or wo > 0]
            ids = sorted({p for m in use for p in (m[1], m[2])})
            idx = {p: i for i, p in enumerate(ids)}
            age = np.array([(t0 - m[0]).total_seconds() / 86400 for m in use])
            wt = 0.5 ** (age / HALF_LIFE) * np.array([wo if m[3] else 1.0 for m in use])
            b, _ = fit_bt(np.array([idx[m[1]] for m in use]), np.array([idx[m[2]] for m in use]), wt, len(ids), PRIOR_SD)
            # "known" = both players have official history before this event (same set for every weight)
            known_off = {p for m in past if not m[3] for p in (m[1], m[2])}
            out = []
            for m in test:
                d = (b[idx[m[1]]] if m[1] in idx else 0.0) - (b[idx[m[2]]] if m[2] in idx else 0.0)
                p = 1 / (1 + math.exp(-d))
                out.append((-math.log(p), (p > 0.5) + 0.5 * (p == 0.5), m[1] in known_off and m[2] in known_off))
            res[wo][ev] = out

    def summary(evs, sel=lambda x: True):
        lines = []
        base = {e: [x for x in res[1.0][e] if sel(x)] for e in evs}
        n = sum(len(v) for v in base.values())
        for wo in WEIGHTS:
            per = {e: [x for x in res[wo][e] if sel(x)] for e in evs}
            ll = sum(x[0] for v in per.values() for x in v) / n
            acc = sum(x[1] for v in per.values() for x in v) / n
            # paired bootstrap over events of (ll[wo] - ll[1.0])
            diffs = np.array([sum(x[0] for x in per[e]) - sum(x[0] for x in base[e]) for e in evs])
            cnt = np.array([len(base[e]) for e in evs])
            rng = np.random.default_rng(1)
            bs = []
            for _ in range(4000):
                k = rng.integers(0, len(evs), len(evs))
                bs.append(diffs[k].sum() / max(cnt[k].sum(), 1))
            lo, hi = np.percentile(bs, [2.5, 97.5])
            lines.append(f"  Open 权重 {wo:<4}  log loss {ll:.4f}  准确率 {acc:.3f}  vs 现模型 {ll - sum(x[0] for v in base.values() for x in v) / n:+.4f} [{lo:+.4f}, {hi:+.4f}]")
        return n, lines

    dev = [e for e in official if start[e].year < 2023]
    hold = [e for e in official if start[e].year >= 2023]
    for name, evs in (("DEV（2023 前官方赛事）", dev), ("HOLDOUT（2023 起官方赛事）", hold), ("全部官方赛事", official)):
        for tag, sel in (("全部对局", lambda x: True), ("双方都有官方赛记录", lambda x: x[2])):
            n, lines = summary(evs, sel)
            print(f"{name} · {tag}：{n} 场")
            print("\n".join(lines))


if __name__ == "__main__":
    main()
