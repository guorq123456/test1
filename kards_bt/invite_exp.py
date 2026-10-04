"""Calibrating the ladder-invite credit per player (direction 2).

The current credit (invites.py, "F1") gives every OCC Top 8 invitee the same thing: that month's median
qualifier-advancer record against a virtual opponent. Repeated invitees (Jking7 32 times, Noein5 24)
accumulate a lot of it. Variants tested here, out of sample (fit before each official event, DEV = events
before 2024 to choose settings, HOLDOUT = 2024 onward to judge, event-level paired bootstrap), all with
the newcomer anchor of the production model:

  V0  uniform credit (production)
  V1  credit shrinks with the player's own real evidence: weight * n0 / (n0 + effective matches)
  V3  threshold model: an invite is one virtual term log sigmoid(a * (b - tau_m)), tau_m = median pre-month
      rating of that month's qualifier advancers; a player already above tau_m gains almost nothing
  V4  credit scaled by the player's Top 8 record as an invitee so far, relative to advancers' Top 8 record
      in the same months (shrunk toward 1 with c pseudo-matches, capped at 1): play badly after invites
      and the credit fades

Also reported: how invitees are predicted in Top 8 matches (actual - predicted win rate), split by how much
real evidence they had.
"""
import csv
import math
import os
import re
from collections import defaultdict
from datetime import datetime

import numpy as np

import bt
import invites
import newcomers

HL, SD, INV_HL = 240, 0.4, 120


def load():
    ms = sorted(bt.load_matches({"official"}, False))
    start = defaultdict(lambda: datetime.max)
    for m in ms:
        start[m[4]] = min(start[m[4]], m[0])
    top8 = defaultdict(list)  # month -> [(t, w, l)] Top 8 matches
    for r in csv.DictReader(open(os.path.join(bt.DATA, "matches.csv"))):
        if r["valid"] == "1" and r["category"] == "official" and invites.MONTH.match(r["event"]) \
                and re.search(r"top|final", r["stage"] or "", re.I):
            w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
            top8[r["event"]].append((bt.parse_time(r["time"]), w, l))
    return ms, start, top8


def month_info(ms):
    """Per month: invitees, advancers, F1 credit (level, wins, losses), tau (median advancer pre-rating)."""
    fit_before = lambda t: bt._fit_before(ms, t, HL, SD)  # noqa: E731
    out = []
    for month, qual_start, top8_start, inv, rec in invites.months():
        adv = list(rec)
        if not adv:
            continue
        pre = fit_before(qual_start)
        wins = float(np.median([sum(1 for _, won in rec[a] if won) for a in adv]))
        losses = float(np.median([sum(1 for _, won in rec[a] if not won) for a in adv]))
        opps = [o for a in adv for o, _ in rec[a]]
        level = sum(pre.get(o, 0.0) for o in opps) / len(opps)
        tau = float(np.median([pre.get(a, 0.0) for a in adv]))
        out.append((month, top8_start, sorted(inv), set(adv), level, wins, losses, tau))
    return out


def v4_scale(months, top8, c):
    """{(month, invitee): scale} from the invitee's Top 8 record as invitee in EARLIER months vs advancers'."""
    scale = {}
    inv_rec, adv_rec = defaultdict(lambda: [0, 0]), [0, 0]
    for month, t8, inv, adv, *_ in months:
        base = adv_rec[0] / max(1, sum(adv_rec))
        for p in inv:
            w, l = inv_rec[p]
            s = 1.0 if not base or (w + l) == 0 else min(1.0, ((w + c * base) / (w + l + c)) / base)
            scale[(month, p)] = s
        for t, w, l in top8[month]:  # now add this month's Top 8 results (known only afterwards)
            if w in inv:
                inv_rec[w][0] += 1
            if l in inv:
                inv_rec[l][1] += 1
            if w in adv:
                adv_rec[0] += 1
            if l in adv:
                adv_rec[1] += 1
    return scale


def main():
    ms, start, top8 = load()
    ids_all = sorted({p for m in ms for p in (m[1], m[2])})
    months = month_info(ms)
    anchors = newcomers.anchors(ms, HL, SD, bt.fit_bt, 2)
    evs = sorted(start, key=start.get)[2:]
    is_month = {e: e for e in start if invites.MONTH.match(e)}
    inv_of = {m[0]: set(m[2]) for m in months}
    top8_keys = {e: set(v) for e, v in top8.items()}

    variants = {"V0 统一补偿": ("v0", None)}
    for n0 in (10, 20, 40):
        variants[f"V1 按证据递减 n0={n0}"] = ("v1", n0)
    for a in (1.0, 2.0, 4.0):
        variants[f"V3 门槛模型 a={a}"] = ("v3", a)
    for c in (2, 5, 10):
        variants[f"V4 按8强表现 c={c}"] = ("v4", c)
    v4 = {c: v4_scale(months, top8, c) for c in (2, 5, 10)}

    res = {k: {} for k in variants}
    for ev in evs:
        t0 = start[ev]
        past = [m for m in ms if m[0] < t0]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        age = np.array([(t0 - m[0]).total_seconds() / 86400 for m in past])
        w = 0.5 ** (age / HL)
        win, lose = np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past])
        eff = defaultdict(float)
        for m, wt in zip(past, w):
            eff[m[1]] += wt
            eff[m[2]] += wt
        base_v = [(idx[p], level, sign, n * 0.5 ** ((t0 - t).total_seconds() / 86400 / hl))
                  for t, p, level, wins, losses, hl in anchors if t <= t0 and p in idx
                  for sign, n in ((1.0, wins), (-1.0, losses)) if n > 0]
        test = [m for m in ms if m[4] == ev]
        for name, (kind, par) in variants.items():
            v = list(base_v)
            for month, t8, inv, adv, level, wins, losses, tau in months:
                if t8 > t0:
                    continue
                fade = 0.5 ** ((t0 - t8).total_seconds() / 86400 / INV_HL)
                for p in inv:
                    if p not in idx:
                        continue
                    if kind == "v3":
                        v.append((idx[p], tau, par, fade))
                        continue
                    s = 1.0
                    if kind == "v1":
                        s = par / (par + eff[p])
                    elif kind == "v4":
                        s = v4[par][(month, p)]
                    for sign, n in ((1.0, wins), (-1.0, losses)):
                        if n > 0 and s > 0:
                            v.append((idx[p], level, sign, s * n * fade))
            virtual = tuple(np.array(c) for c in zip(*v)) if v else None
            b, _ = bt.fit_bt(win, lose, w, len(ids), SD, virtual=virtual)
            r = lambda p: b[idx[p]] if p in idx else 0.0  # noqa: E731
            out = []
            for m in test:
                p = 1 / (1 + math.exp(-(r(m[1]) - r(m[2]))))
                t8 = (m[0], m[1], m[2]) in top8_keys.get(ev, ())
                out.append((-math.log(p), t8, m[1] in inv_of.get(ev, ()), m[2] in inv_of.get(ev, ()), p, eff[m[1]], eff[m[2]]))
            res[name][ev] = out

    dev = [e for e in evs if start[e].year < 2024]
    hold = [e for e in evs if start[e].year >= 2024]
    base = res["V0 统一补偿"]

    def ll(r, es, sel=lambda x: True):
        xs = [x for e in es for x in r[e] if sel(x)]
        return (sum(x[0] for x in xs) / len(xs), len(xs)) if xs else (float("nan"), 0)

    def boot(r, es, sel=lambda x: True):
        d = np.array([sum(x[0] for x in r[e] if sel(x)) - sum(x[0] for x in base[e] if sel(x)) for e in es])
        c = np.array([sum(1 for x in base[e] if sel(x)) for e in es])
        rng = np.random.default_rng(1)
        bs = [d[i].sum() / max(c[i].sum(), 1) for i in (rng.integers(0, len(es), len(es)) for _ in range(4000))]
        return np.percentile(bs, [2.5, 97.5])

    t8sel = lambda x: x[1]  # noqa: E731
    print(f"DEV {ll(base, dev)[1]} 场（8 强 {ll(base, dev, t8sel)[1]}），HOLDOUT {ll(base, hold)[1]} 场（8 强 {ll(base, hold, t8sel)[1]}）")
    print(f"{'方案':<22} {'DEV':>7} {'HOLDOUT':>8} {'差 [95%]':>22} {'HOLDOUT 8强':>11} {'差 [95%]':>22}")
    b0, b0t = ll(base, hold)[0], ll(base, hold, t8sel)[0]
    for name, r in res.items():
        h, ht = ll(r, hold)[0], ll(r, hold, t8sel)[0]
        lo, hi = boot(r, hold)
        lot, hit = boot(r, hold, t8sel)
        print(f"{name:<22} {ll(r, dev)[0]:.4f}  {h:.4f}  {h - b0:+.4f} [{lo:+.4f},{hi:+.4f}]   {ht:.4f}  {ht - b0t:+.4f} [{lot:+.4f},{hit:+.4f}]")

    print("\n8 强对局里直邀选手的 实际 − 预测 胜率（正 = 被低估），全部赛事：")
    for name, r in res.items():
        acc = defaultdict(lambda: [0.0, 0.0, 0])
        for e in evs:
            for nll, t8, iw, il, p, ew, el in r[e]:
                if not t8:
                    continue
                for is_inv, won, pp, ef in ((iw, 1, p, ew), (il, 0, 1 - p, el)):
                    if is_inv:
                        for lab, ok in (("全部", True), ("真实场次<20", ef < 20), ("真实场次≥20", ef >= 20)):
                            if ok:
                                a = acc[lab]; a[0] += won; a[1] += pp; a[2] += 1
        print(f"  {name:<22} " + "  ".join(f"{lab} {(a[0] - a[1]) / a[2]:+.3f}（{a[2]}）" for lab, a in acc.items()))


if __name__ == "__main__":
    main()
