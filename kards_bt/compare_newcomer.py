"""Does a newcomer's entry path tell us their starting level?

Static decayed BT with a per-player prior mean: a player first seen in an open-registration
event (KARDS Open, Operation: Kards, Singleton) starts at mu_open; one first seen in a
ladder-gated or invitational official event (OCC, expansion/seasonal tournaments, World
Championship) starts at mu_gate. Chosen on DEV (events before 2023), compared once on HOLDOUT,
same scored series and bootstrap as compare_dynamic.py.
"""
import itertools
from multiprocessing import Pool

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit

import compare_dynamic as cd

FIRST = {}
for m in sorted(cd.MATCHES, key=lambda m: m[0]):
    for p in (m[1], m[2]):
        FIRST.setdefault(p, m[4])


def gated(event):
    e = event.lower()
    return any(k in e for k in ("occ", "world championship", "expansion", "tournament 20", "ultimate"))


ENTRY = {p: ("gate" if gated(ev) else "open") for p, ev in FIRST.items()}


def fit(past, t0, half_life, prior_sd, mu_open, mu_gate):
    ids = sorted({p for m in past for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    w = np.array([idx[m[1]] for m in past])
    l = np.array([idx[m[2]] for m in past])
    wt = np.array([0.5 ** ((t0 - m[0]).total_seconds() / 86400 / half_life) for m in past])
    mu = np.array([mu_gate if ENTRY[p] == "gate" else mu_open for p in ids])
    lam = 1 / prior_sd ** 2

    def f(b):
        d = b[w] - b[l]
        g = wt * (expit(d) - 1)
        grad = lam * (b - mu)
        np.add.at(grad, w, g)
        np.add.at(grad, l, -g)
        return -(wt * log_expit(d)).sum() + 0.5 * lam * (b - mu) @ (b - mu), grad

    b = minimize(f, mu.copy(), jac=True, method="L-BFGS-B", options={"maxiter": 3000}).x
    return dict(zip(ids, b))


def preds(cfg):
    half_life, prior_sd, mu_open, mu_gate = cfg
    out = {}
    for ev in cd.SCORED:
        t0 = cd.START[ev]
        b = fit([m for m in cd.MATCHES if m[0] < t0], t0, half_life, prior_sd, mu_open, mu_gate)
        for k, m in enumerate(cd.EVENTS[ev]):
            # a player never seen before the event starts at their entry-path mean
            ba = b.get(m[1], mu_gate if gated(ev) else mu_open)
            bb = b.get(m[2], mu_gate if gated(ev) else mu_open)
            out[(ev, k)] = float(expit(ba - bb))
    return cfg, out


def main():
    dev = cd.keys_where(lambda ev, m: cd.START[ev] < cd.SPLIT)
    hold = cd.keys_where(lambda ev, m: cd.START[ev] >= cd.SPLIT)
    vet = cd.keys_where(lambda ev, m: cd.START[ev] >= cd.VET_SINCE and (m[1] in cd.VETS or m[2] in cd.VETS))
    print("entry paths:", {k: sum(v == k for v in ENTRY.values()) for k in ("open", "gate")})
    grid = list(itertools.product([180, 365], [0.6, 0.8], [-0.3, -0.15, 0.0], [0.0, 0.2, 0.4, 0.6, 0.8]))
    with Pool() as pool:
        res = dict(pool.map(preds, grid))
    print("(half-life, prior sd, mu_open, mu_gate): dev / holdout / veterans-2024+")
    for c in sorted(grid, key=lambda c: cd.logloss(res[c], dev))[:12]:
        print(f"  {c}: {cd.logloss(res[c], dev):.4f} / {cd.logloss(res[c], hold):.4f} / {cd.logloss(res[c], vet):.4f}")
    base = [c for c in grid if c[2] == 0.0 and c[3] == 0.0]
    best_base = min(base, key=lambda c: cd.logloss(res[c], dev))
    best = min(grid, key=lambda c: cd.logloss(res[c], dev))
    print(f"\nchosen on DEV: baseline {best_base}, entry-path prior {best}")
    for name, keys in (("DEV", dev), ("HOLDOUT", hold), ("veterans 2024+", vet)):
        pt, lo, hi = cd.boot_diff(res[best_base], res[best], keys)
        print(f"  {name:15s} baseline {cd.logloss(res[best_base], keys):.4f}  entry-path {cd.logloss(res[best], keys):.4f}"
              f"  baseline - entry = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]  (positive favours entry-path prior)")


if __name__ == "__main__":
    main()
