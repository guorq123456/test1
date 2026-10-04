"""Two pre-registered experiments on the cleaned data, scored out of sample.

A. Event tiers. Does a result from a more important event say more about skill?
   Model: P(w beats l) = sigmoid(kappa * (b_w - b_l)), kappa = eta**[Bo5] * exp(theta * (4 - tier)).
   theta > 0: higher tiers are more decisive (the user's hypothesis); eta absorbs Bo5 vs Bo3.
   tier 1  WC main stage (2024 top 16, 2025, 2021-23 grand finals)
   tier 2  WC knockout stages (2021-23 groups + 32 double elim, 2024 swiss), OCC Ultimate,
           expansion / seasonal Top 8
   tier 3  OCC Top 8, Open top cuts, expansion / seasonal swiss
   tier 4  OCC qualifiers, Open qualifiers and swiss
   Control: 20 placebos shuffling tier labels across (event, stage) blocks within each year.

B. Ladder invites. In OCC months with both qualifier and Top 8 data, a Top 8 entrant who never
   played that month's qualifier is a ladder invite. Invitees bank no results while qualifier
   advancers bank several wins.
   F1 (no free parameter): credit each invitee with the month's median advancer qualifier record,
      against a virtual opponent rated at the mean pre-month rating of the advancers' opponents.
   F2: credit each invitee with k virtual games at 50% against a fixed level L (log-odds).
   Credits are dated at the Top 8 start, when both invite status and advancer records are known.

Origins: every block (an event, or the Top 8 of an OCC month as its own block) is predicted from
everything strictly before it starts. Choose on DEV (blocks starting before 2023), confirm once on
HOLDOUT, paired bootstrap over events.
"""
import csv
import itertools
import math
import os
import random
import re
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool
from statistics import median

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit

HERE = os.path.dirname(os.path.abspath(__file__))
HALF_LIFE, PRIOR_SD = 240.0, 0.8
SPLIT = datetime(2023, 1, 1)
NO_QUALIFIER = {f"OCC 2024-0{m}" for m in range(4, 9)}


def tier(r):
    e, st, ty = r["event"], r["stage"] or "", r["stage_type"] or ""
    wc = re.search(r"world championship (20\d\d)", e, re.I)
    if wc:
        y = int(wc.group(1))
        if r["source"] == "manual" or y >= 2025 or (y == 2024 and r["source"] == "challonge"):
            return 1
        return 2
    if re.search(r"ultimate", e, re.I):
        return 2
    if re.search(r"expansion|tournament 20", e, re.I):
        return 2 if re.search(r"top", st, re.I) else 3
    if re.search(r"^occ ", e, re.I):
        return 3 if re.search(r"top|final", st, re.I) else 4
    return 3 if re.search(r"top|cut|final|elim", st + " " + ty, re.I) else 4


ALL = list(csv.DictReader(open(os.path.join(HERE, "data", "matches.csv"))))
ROWS = []
for r in ALL:
    if r["valid"] != "1" or r["category"] not in ("open", "open_special", "official"):
        continue
    t = datetime.strptime(r["time"], "%Y-%m-%dT%H:%M:%SZ")
    w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
    try:
        bo5 = max(int(float(r["s1"])), int(float(r["s2"]))) >= 3
    except ValueError:
        bo5 = False
    top8 = bool(re.match(r"OCC \d{4}-\d\d$", r["event"]) and re.search(r"top|final", r["stage"] or "", re.I))
    ROWS.append({"t": t, "w": w, "l": l, "event": r["event"], "tier": tier(r), "bo5": bo5,
                 "block": (r["event"], "top8" if top8 else "main"), "year": t.year})

BLOCK_START, EVENT_END = {}, {}
for r in ROWS:
    BLOCK_START[r["block"]] = min(BLOCK_START.get(r["block"], r["t"]), r["t"])
    EVENT_END[r["event"]] = max(EVENT_END.get(r["event"], r["t"]), r["t"])
first_events = set(sorted(EVENT_END, key=EVENT_END.get)[:3])
SCORED = sorted((b for b in BLOCK_START if b[0] not in first_events), key=BLOCK_START.get)


# --- ladder invites --------------------------------------------------------------------------------
def invite_months():
    """{month: (top8_start, invitees, advancers, {advancer: [(opponent, won)]})} for OCC months with qualifiers."""
    seen = defaultdict(lambda: defaultdict(set))  # month -> stage kind -> players (any row, valid or not)
    for r in ALL:
        if re.match(r"OCC \d{4}-\d\d$", r["event"]) and r["event"] not in NO_QUALIFIER:
            kind = "top8" if re.search(r"top|final", r["stage"] or "", re.I) else "qual"
            for p in (r["p1"], r["p2"]):
                if p != "ch:BYE":
                    seen[r["event"]][kind].add(p)
    out = {}
    for month, s in seen.items():
        if not s["qual"] or not s["top8"]:
            continue
        inv = s["top8"] - s["qual"]
        adv = s["top8"] & s["qual"]
        rec = defaultdict(list)
        for r in ROWS:
            if r["event"] == month and r["block"][1] == "main":
                if r["w"] in adv:
                    rec[r["w"]].append((r["l"], True))
                if r["l"] in adv:
                    rec[r["l"]].append((r["w"], False))
        start = BLOCK_START.get((month, "top8"))
        if start and inv and adv:
            out[month] = (start, inv, adv, rec)
    return out


INVITES = invite_months()
INVITEES = {(m, p) for m, v in INVITES.items() for p in v[1]}


# --- fitting ---------------------------------------------------------------------------------------
def fit(t0, kappa_fn, virtual=None, x0=None):
    """MAP with time decay, per-series kappa and optional virtual results [(player, opp_level, won, weight)]."""
    past = [r for r in ROWS if r["t"] < t0]
    ids = sorted({p for r in past for p in (r["w"], r["l"])} | {v[0] for v in (virtual or [])})
    idx = {p: i for i, p in enumerate(ids)}
    w = np.array([idx[r["w"]] for r in past])
    l = np.array([idx[r["l"]] for r in past])
    wt = np.array([0.5 ** ((t0 - r["t"]).total_seconds() / 86400 / HALF_LIFE) for r in past])
    k = np.array([kappa_fn(r) for r in past])
    vp = np.array([idx[v[0]] for v in virtual or []], dtype=int)
    vo = np.array([v[1] for v in virtual or []])
    vs = np.array([1.0 if v[2] else -1.0 for v in virtual or []])
    vw = np.array([v[3] for v in virtual or []])
    lam = 1 / PRIOR_SD ** 2

    def f(b):
        d = k * (b[w] - b[l])
        g = wt * k * (expit(d) - 1)
        grad = lam * b
        np.add.at(grad, w, g)
        np.add.at(grad, l, -g)
        nll = -(wt * log_expit(d)).sum() + 0.5 * lam * b @ b
        if len(vp):
            dv = vs * (b[vp] - vo)
            nll -= (vw * log_expit(dv)).sum()
            np.add.at(grad, vp, vw * vs * (expit(dv) - 1))
        return nll, grad

    b0 = np.zeros(len(ids)) if x0 is None else np.array([x0.get(p, 0.0) for p in ids])
    b = minimize(f, b0, jac=True, method="L-BFGS-B", options={"maxiter": 3000}).x
    return dict(zip(ids, b))


def plain_kappa(r):
    return 1.0


def baseline_ratings():
    """Pre-month ratings (baseline model) used to place F1's virtual opponents."""
    out = {}
    for month in INVITES:
        out[month] = fit(BLOCK_START[(month, "main")], plain_kappa)
    return out


def virtual_results(t0, scheme, pre=None):
    if scheme is None:
        return []
    res = []
    for month, (start, inv, adv, rec) in INVITES.items():
        if start >= t0:
            continue
        decay = 0.5 ** ((t0 - start).total_seconds() / 86400 / HALF_LIFE)
        if scheme[0] == "F1":
            wins = median(sum(1 for _, won in rec[a] if won) for a in adv)
            losses = median(sum(1 for _, won in rec[a] if not won) for a in adv)
            opps = [o for a in adv for o, _ in rec[a]]
            level = float(np.mean([pre[month].get(o, 0.0) for o in opps])) if opps else 0.0
            for p in inv:
                res += [(p, level, True, decay * wins), (p, level, False, decay * losses)]
        else:  # F2: k games at 50% vs a fixed level
            _, k, level = scheme
            for p in inv:
                res += [(p, level, True, decay * k / 2), (p, level, False, decay * k / 2)]
    return res


def run(cfg):
    """cfg = (theta, eta, rho, invite_scheme, placebo_seed) -> {(block, i): p(actual winner wins)}."""
    theta, eta, rho, scheme, seed = cfg
    tiers = {}
    if seed is not None:  # placebo: shuffle tier labels across blocks within each year
        rnd = random.Random(seed)
        by_year = defaultdict(list)
        for b in BLOCK_START:
            by_year[BLOCK_START[b].year].append(b)
        block_tier = {r["block"]: r["tier"] for r in ROWS}
        for blocks in by_year.values():
            labels = [block_tier[b] for b in blocks]
            rnd.shuffle(labels)
            tiers.update(zip(blocks, labels))

    def tier_of(r):
        return tiers.get(r["block"], r["tier"]) if seed is not None else r["tier"]

    def kappa(r):
        return (eta if r["bo5"] else 1.0) * math.exp(theta * (4 - tier_of(r)))

    pre = PRE if scheme and scheme[0] == "F1" else None
    out, prev = {}, None
    for blk in SCORED:
        t0 = BLOCK_START[blk]
        b = fit(t0, kappa, virtual_results(t0, scheme, pre), x0=prev)
        prev = b
        for i, r in enumerate(x for x in ROWS if x["block"] == blk):
            d = kappa(r) * (b.get(r["w"], 0.0) - b.get(r["l"], 0.0))
            out[(blk, i)] = float(expit(d))
    return cfg, out


PRE = None


def logloss(p, keys):
    return -sum(math.log(p[k]) for k in keys) / len(keys)


def boot(a, b, keys, reps=4000, seed=1):
    by = defaultdict(list)
    for k in keys:
        by[k[0][0]].append(k)
    evs = list(by)
    d = {k: math.log(b[k]) - math.log(a[k]) for k in keys}
    point = sum(d.values()) / len(keys)
    rnd = random.Random(seed)
    sims = sorted(sum(d[k] for k in ks) / len(ks) for ks in
                  ([k for e in (rnd.choice(evs) for _ in evs) for k in by[e]] for _ in range(reps)))
    return point, sims[int(.025 * reps)], sims[int(.975 * reps)]


def keyset(pred):
    out = []
    for blk in SCORED:
        for i, r in enumerate(x for x in ROWS if x["block"] == blk):
            if pred(blk, r):
                out.append((blk, i))
    return out


def main():
    global PRE
    PRE = baseline_ratings()
    dev = keyset(lambda b, r: BLOCK_START[b] < SPLIT)
    hold = keyset(lambda b, r: BLOCK_START[b] >= SPLIT)
    hs_hold = keyset(lambda b, r: BLOCK_START[b] >= SPLIT and r["tier"] <= 3)
    top8 = keyset(lambda b, r: b[1] == "top8" and b[0] in INVITES)
    inv_side = {k: ((k[0][0], r["w"]) in INVITEES, (k[0][0], r["l"]) in INVITEES)
                for k, r in zip(top8, (next(x for j, x in enumerate(y for y in ROWS if y["block"] == k[0]) if j == k[1])
                                       for k in top8))}
    print(f"scored series: dev {len(dev)}, holdout {len(hold)} (tiers 1-3: {len(hs_hold)}); "
          f"OCC Top 8 with invite data {len(top8)}; invite months {len(INVITES)}, invitee slots {len(INVITEES)}")

    tier_grid = [(th, eta, 1.0, None, None) for th, eta in itertools.product(
        [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3], [0.8, 1.0, 1.2])]
    inv_grid = [(0.0, 1.0, 1.0, ("F1",), None)] + [(0.0, 1.0, 1.0, ("F2", k, L), None)
                                                    for k, L in itertools.product([4, 8], [0.4, 0.8, 1.2])]
    with Pool() as pool:
        res = dict(pool.map(run, tier_grid + inv_grid))

    print("\n== A. event tiers: (theta, eta) dev / holdout / holdout tiers 1-3")
    for c in tier_grid:
        print(f"  theta={c[0]:+.1f} eta={c[1]:.1f}: {logloss(res[c], dev):.4f} / {logloss(res[c], hold):.4f}"
              f" / {logloss(res[c], hs_hold):.4f}")
    null_cfg = min((c for c in tier_grid if c[0] == 0.0), key=lambda c: logloss(res[c], dev))
    best = min(tier_grid, key=lambda c: logloss(res[c], dev))
    if logloss(res[null_cfg], dev) - logloss(res[best], dev) < 0.0005:
        best = null_cfg
    print(f"  chosen on DEV: null {null_cfg[:2]}, tiers {best[:2]}")
    for name, keys in (("HOLDOUT", hold), ("HOLDOUT tiers 1-3", hs_hold)):
        pt, lo, hi = boot(res[null_cfg], res[best], keys)
        print(f"  {name:18s} gain (null - tiers) = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]")
    # placebo: does a shuffled tier map do as well at the chosen theta?
    if best[0] != 0.0:
        with Pool() as pool:
            plac = dict(pool.map(run, [(best[0], best[1], 1.0, None, s) for s in range(20)]))
        gains = sorted(logloss(res[null_cfg], hs_hold) - logloss(p, hs_hold) for p in plac.values())
        real = logloss(res[null_cfg], hs_hold) - logloss(res[best], hs_hold)
        print(f"  placebo gains on holdout tiers 1-3 (20 shuffles): max {gains[-1]:+.4f}, real {real:+.4f}")

    print("\n== B. ladder invites: all / OCC Top 8 log loss, and Top 8 residual (actual - predicted) for invitees")
    base = (0.0, 1.0, 1.0, None, None)
    base = min((c for c in tier_grid if c[0] == 0.0), key=lambda c: logloss(res[c], dev))

    def residual(p):
        num, n = 0.0, 0
        for k, (wi, li) in inv_side.items():
            if wi != li:  # invitee vs advancer
                q = p[k] if wi else 1 - p[k]  # predicted P(invitee wins)
                num += (1.0 if wi else 0.0) - q
                n += 1
        return num / n, n

    for c in [base] + inv_grid:
        r, n = residual(res[c])
        label = "baseline" if c is base else str(c[3])
        print(f"  {label:22s} all {logloss(res[c], dev + hold):.4f}  Top 8 {logloss(res[c], top8):.4f}"
              f"  invitee residual {r:+.3f} (n={n})")
    best_inv = min(inv_grid, key=lambda c: logloss(res[c], [k for k in top8 if BLOCK_START[k[0]] < SPLIT]))
    for name, keys in (("Top 8 holdout", [k for k in top8 if BLOCK_START[k[0]] >= SPLIT]), ("all holdout", hold),
                       ("all", dev + hold)):
        pt, lo, hi = boot(res[base], res[best_inv], keys)
        print(f"  {str(best_inv[3]):22s} {name:14s} gain = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]")
    f1 = inv_grid[0]
    for name, keys in (("Top 8", top8), ("all", dev + hold)):
        pt, lo, hi = boot(res[base], res[f1], keys)
        print(f"  F1 (no parameter)      {name:14s} gain = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]")


if __name__ == "__main__":
    main()
