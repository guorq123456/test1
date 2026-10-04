"""Per-player check of the production model: actual wins vs what the model predicted before each match.

Every official event is predicted from a fit on results before it starts (same decay, prior, newcomer anchor
and ladder-invite credit as bt.py). For each player we sum, over all their matches, the win probability the
model gave them (expected wins) and compare with actual wins. z = (actual - expected) / sqrt(sum p(1-p)).
|z| > 2 means the model has been systematically wrong about that player, not just unlucky.

    python3 residuals.py            # tables: veterans (>= 40 matches), mid (15-39), newcomers (< 15)
    python3 residuals.py --csv data/residuals.csv
"""
import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import datetime

import numpy as np

import bt
import invites
import newcomers

HL, SD, INV_HL = 240, 0.4, 120


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    ms = sorted(bt.load_matches({"official"}, False))
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    start = defaultdict(lambda: datetime.max)
    for m in ms:
        start[m[4]] = min(start[m[4]], m[0])
    credits = invites.credits(lambda t: bt._fit_before(ms, t, HL, SD))
    virt_all = [c + (INV_HL,) for c in credits] + newcomers.anchors(ms, HL, SD, bt.fit_bt, 2)

    acc = defaultdict(lambda: {"n": 0, "w": 0, "e": 0.0, "v": 0.0, "first": None, "last": None, "recent_w": 0, "recent_e": 0.0, "recent_n": 0})
    for ev in sorted(start, key=start.get)[2:]:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / HL)
        v = [(idx[p], level, sign, n * 0.5 ** ((t0 - t).total_seconds() / 86400 / hl))
             for t, p, level, wins, losses, hl in virt_all if t <= t0 and p in idx
             for sign, n in ((1.0, wins), (-1.0, losses)) if n > 0]
        virtual = tuple(np.array(c) for c in zip(*v)) if v else None
        b, _ = bt.fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), SD, virtual=virtual)
        r = lambda p: b[idx[p]] if p in idx else 0.0  # noqa: E731
        for m in ms:
            if m[4] != ev:
                continue
            p = 1 / (1 + math.exp(-(r(m[1]) - r(m[2]))))
            for q, won, pp in ((m[1], 1, p), (m[2], 0, 1 - p)):
                a = acc[q]
                a["n"] += 1
                a["w"] += won
                a["e"] += pp
                a["v"] += pp * (1 - pp)
                a["first"] = a["first"] or m[0]
                a["last"] = m[0]
                if m[0].year >= 2025:
                    a["recent_n"] += 1
                    a["recent_w"] += won
                    a["recent_e"] += pp
    rows = []
    for q, a in acc.items():
        z = (a["w"] - a["e"]) / math.sqrt(a["v"]) if a["v"] > 0 else 0.0
        rows.append({"player_id": q, "name": names.get(q, q), "matches": a["n"], "wins": a["w"], "expected": round(a["e"], 1),
                     "diff": round(a["w"] - a["e"], 1), "z": round(z, 2), "first": a["first"].strftime("%Y-%m"),
                     "last": a["last"].strftime("%Y-%m"), "since2025": f"{a['recent_w']}-{a['recent_n'] - a['recent_w']}",
                     "since2025_exp": round(a["recent_e"], 1)})
    rows.sort(key=lambda r: -abs(r["z"]))
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(sorted(rows, key=lambda r: -r["matches"]))
        print(f"{args.csv}: {len(rows)} players")

    def table(title, sel):
        xs = [r for r in rows if sel(r)]
        print(f"\n{title}（{len(xs)} 人）：|z| 最大的 {args.top} 人")
        print(f"{'选手':<28}{'场次':>5}{'实际':>5}{'期望':>7}{'差':>7}{'z':>7}  活跃期        2025 起")
        for r in xs[:args.top]:
            print(f"{r['name']:<28}{r['matches']:>5}{r['wins']:>5}{r['expected']:>7}{r['diff']:>+7}{r['z']:>+7}  {r['first']}–{r['last']}  {r['since2025']}（期望 {r['since2025_exp']}）")
        z = np.array([r["z"] for r in xs])
        print(f"  这一组 z 的均值 {z.mean():+.2f}，标准差 {z.std():.2f}（无系统偏差时应约为 0 和 1）")

    table("老将：≥40 场", lambda r: r["matches"] >= 40)
    table("中坚：15–39 场", lambda r: 15 <= r["matches"] < 40)
    table("新人：<15 场", lambda r: 5 <= r["matches"] < 15)


if __name__ == "__main__":
    main()
