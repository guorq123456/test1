"""Static (decayed) vs dynamic (random-walk) Bradley-Terry, out of sample.

Both models predict every series of an event from information available before the event
starts; the first three events are warm-up only. Parameters are chosen on DEV (events starting
before 2023-01-01) and compared once on HOLDOUT (2023 on), with a paired bootstrap over events.
A separate subset tracks veterans after 2024 (a player with 30+ series before 2023 on either side),
where a fixed-skill model should be most overconfident.
"""
import itertools
import math
import random
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit

import dynamic_bt
from bt import load_matches

SPLIT = datetime(2023, 1, 1)
VET_SINCE = datetime(2024, 1, 1)
MATCHES = load_matches({"open", "open_special", "official"}, False)
EVENTS = defaultdict(list)
for _m in MATCHES:
    EVENTS[_m[4]].append(_m)
ORDER = sorted(EVENTS, key=lambda e: (max(m[0] for m in EVENTS[e]), e))
START = {e: min(m[0] for m in EVENTS[e]) for e in ORDER}
SCORED = ORDER[3:]
PRE = defaultdict(int)
for _m in MATCHES:
    if _m[0] < SPLIT:
        PRE[_m[1]] += 1
        PRE[_m[2]] += 1
VETS = {p for p, c in PRE.items() if c >= 30}


def static_fit(past, t0, half_life, prior_sd):
    ids = sorted({p for m in past for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    w = np.array([idx[m[1]] for m in past])
    l = np.array([idx[m[2]] for m in past])
    wt = np.array([0.5 ** ((t0 - m[0]).total_seconds() / 86400 / half_life) for m in past])
    lam = 1 / prior_sd ** 2

    def f(b):
        d = b[w] - b[l]
        g = wt * (expit(d) - 1)
        grad = lam * b
        np.add.at(grad, w, g)
        np.add.at(grad, l, -g)
        return -(wt * log_expit(d)).sum() + 0.5 * lam * b @ b, grad

    b = minimize(f, np.zeros(len(ids)), jac=True, method="L-BFGS-B", options={"maxiter": 3000}).x
    return dict(zip(ids, b))


def static_preds(cfg):
    half_life, prior_sd = cfg
    out = {}
    for ev in SCORED:
        t0 = START[ev]
        b = static_fit([m for m in MATCHES if m[0] < t0], t0, half_life, prior_sd)
        for k, m in enumerate(EVENTS[ev]):
            out[(ev, k)] = float(expit(b.get(m[1], 0.0) - b.get(m[2], 0.0)))
    return cfg, out


def dynamic_preds(cfg):
    drift, newcomer_sd = cfg
    out, outp = {}, {}
    scored = set(SCORED)

    def on_event(ev, start, end, before, after, ms):
        if before is None or ev not in scored:
            return
        for k, m in enumerate(ms):
            out[(ev, k)] = dynamic_bt.predict(before, m[1], m[2], newcomer_sd, predictive=False)
            outp[(ev, k)] = dynamic_bt.predict(before, m[1], m[2], newcomer_sd, predictive=True)

    dynamic_bt.run(MATCHES, drift, newcomer_sd, on_event=on_event)
    return cfg, out, outp


def logloss(preds, keys):
    return -sum(math.log(preds[k]) for k in keys) / len(keys)


def keys_where(pred):
    return [(ev, k) for ev in SCORED for k, m in enumerate(EVENTS[ev]) if pred(ev, m)]


def boot_diff(a, b, keys, reps=4000, seed=1):
    """Mean log-loss difference a - b with a 95% interval from resampling whole events."""
    by = defaultdict(list)
    for k in keys:
        by[k[0]].append(k)
    evs = list(by)
    d = {k: -math.log(a[k]) + math.log(b[k]) for k in keys}
    point = sum(d.values()) / len(keys)
    rnd = random.Random(seed)
    sims = []
    for _ in range(reps):
        ks = [k for e in (rnd.choice(evs) for _ in evs) for k in by[e]]
        sims.append(sum(d[k] for k in ks) / len(ks))
    sims.sort()
    return point, sims[int(0.025 * reps)], sims[int(0.975 * reps)]


def main():
    dev = keys_where(lambda ev, m: START[ev] < SPLIT)
    hold = keys_where(lambda ev, m: START[ev] >= SPLIT)
    vet = keys_where(lambda ev, m: START[ev] >= VET_SINCE and (m[1] in VETS or m[2] in VETS))
    print(f"scored series: dev {len(dev)}, holdout {len(hold)}, veterans 2024+ {len(vet)}")

    static_grid = list(itertools.product([90, 180, 365, 730], [0.6, 0.8]))
    dyn_grid = list(itertools.product([0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8], [0.5, 0.7, 0.9]))
    with Pool() as pool:
        st = dict((c, p) for c, p in pool.map(static_preds, static_grid))
        dy = {c: (p, pp) for c, p, pp in pool.map(dynamic_preds, dyn_grid)}

    print("\nstatic (half-life, prior sd): dev / holdout / veterans-2024+ log loss")
    for c in static_grid:
        print(f"  {c}: {logloss(st[c], dev):.4f} / {logloss(st[c], hold):.4f} / {logloss(st[c], vet):.4f}")
    print("dynamic (drift/yr, newcomer sd): dev / holdout / veterans-2024+ log loss [plug-in | predictive]")
    for c in dyn_grid:
        p, pp = dy[c]
        print(f"  {c}: {logloss(p, dev):.4f} / {logloss(p, hold):.4f} / {logloss(p, vet):.4f}"
              f"   | {logloss(pp, dev):.4f} / {logloss(pp, hold):.4f} / {logloss(pp, vet):.4f}")

    best_st = min(static_grid, key=lambda c: logloss(st[c], dev))
    best_dy = min(dyn_grid, key=lambda c: logloss(dy[c][1], dev))
    S, D = st[best_st], dy[best_dy][1]
    print(f"\nchosen on DEV: static {best_st}, dynamic {best_dy} (predictive)")
    for name, keys in (("DEV", dev), ("HOLDOUT", hold), ("veterans 2024+", vet)):
        pt, lo, hi = boot_diff(S, D, keys)
        print(f"  {name:15s} static {logloss(S, keys):.4f}  dynamic {logloss(D, keys):.4f}  "
              f"static - dynamic = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]  (positive favours dynamic)")
    return best_st, best_dy


if __name__ == "__main__":
    main()
