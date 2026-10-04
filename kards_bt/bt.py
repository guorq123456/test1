"""Time-varying Bradley-Terry ratings for KARDS tournament players.

After every event we refit a Bradley-Terry model on all matches played up to
that day:

    P(i beats j) = sigmoid(b_i - b_j)

with two tweaks that make the snapshot reflect form *at that time*:

* time decay: a match played d days before the snapshot gets weight
  0.5 ** (d / half_life), so old results fade out;
* Gaussian prior b_i ~ N(0, prior_sd^2): players with few matches are pulled
  toward the field average instead of exploding to +-infinity after a
  perfect 2-0 record.

The MAP estimate is a weighted, L2-regularized logistic regression. Standard
errors come from the inverse Hessian (Laplace approximation). Ratings are
reported on the Elo scale: elo = 1500 + b * 400 / ln(10).
"""
import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool

# parallelism comes from one process per core; a multi-threaded BLAS in every process would oversubscribe
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import numpy as np  # noqa: E402  (after the thread settings above)
import invites  # noqa: E402
from scipy.linalg import lapack  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.special import expit, log_expit  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ELO_SCALE = 400 / math.log(10)


def parse_time(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


OPEN = ("open", "open_special")


def load_matches(categories, use_games, open_weight=1.0):
    """Return list of (time, winner_id, loser_id, weight, event) for valid matches.

    open_weight scales Open-series results (no entry bar, so a noisier signal than official events)."""
    out = []
    for r in csv.DictReader(open(os.path.join(DATA, "matches.csv"))):
        if r["valid"] != "1" or r["category"] not in categories:
            continue
        k = open_weight if r["category"] in OPEN else 1.0
        if k <= 0:
            continue
        p1, p2 = r["p1"], r["p2"]
        t = parse_time(r["time"])
        if use_games and r["s1"] not in ("", None) and r["s2"] not in ("", None):
            g1, g2 = max(int(float(r["s1"])), 0), max(int(float(r["s2"])), 0)
            if g1 + g2 > 0:
                if g1:
                    out.append((t, p1, p2, k * g1, r["event"]))
                if g2:
                    out.append((t, p2, p1, k * g2, r["event"]))
                continue
        w, l = (p1, p2) if r["winner"] == "1" else (p2, p1)
        out.append((t, w, l, k, r["event"]))
    return out


def fit_bt(winners, losers, weights, n, prior_sd, x0=None, virtual=None):
    """MAP Bradley-Terry fit. winners/losers are int index arrays into n players.

    virtual: optional (player idx, opponent level, +1 win / -1 loss, weight) arrays for results
    against a fixed-strength opponent (the ladder-invite credit, see invites.py).
    """
    lam = 1.0 / prior_sd ** 2
    vi, vl, vs, vw = virtual if virtual is not None else (np.zeros(0, int), np.zeros(0), np.zeros(0), np.zeros(0))

    def f(b):
        d = b[winners] - b[losers]
        nll = -(weights * log_expit(d)).sum() + 0.5 * lam * (b @ b)
        g = weights * (expit(d) - 1.0)  # d nll / d d
        grad = lam * b
        np.add.at(grad, winners, g)
        np.add.at(grad, losers, -g)
        if len(vi):
            dv = vs * (b[vi] - vl)
            nll -= (vw * log_expit(dv)).sum()
            np.add.at(grad, vi, vw * vs * (expit(dv) - 1.0))
        return nll, grad

    res = minimize(f, np.zeros(n) if x0 is None else x0, jac=True, method="L-BFGS-B",
                   options={"maxiter": 2000, "gtol": 1e-8})
    b = res.x

    # Hessian of the negative log posterior -> Laplace standard errors
    d = b[winners] - b[losers]
    h = weights * expit(d) * expit(-d)
    H = np.diag(np.full(n, lam))
    np.add.at(H, (winners, winners), h)
    np.add.at(H, (losers, losers), h)
    np.add.at(H, (winners, losers), -h)
    np.add.at(H, (losers, winners), -h)
    if len(vi):
        dv = b[vi] - vl
        np.add.at(H, (vi, vi), vw * expit(dv) * expit(-dv))
    # H is symmetric positive definite: invert through its Cholesky factor (only the diagonal is needed)
    c, info = lapack.dpotrf(H)
    if info == 0:
        inv, info = lapack.dpotri(c)
    se = np.sqrt(np.diag(inv)) if info == 0 else np.sqrt(np.diag(np.linalg.inv(H)))
    return b, se


def event_snapshots(matches):
    """One snapshot per event, dated at the event's last match."""
    end = defaultdict(lambda: datetime.min)
    for t, *_, ev in matches:
        end[ev] = max(end[ev], t)
    return sorted((t, ev) for ev, t in end.items())


def month_snapshots(matches):
    """One snapshot at the start of every month (event ""), so a time axis shows decay between events."""
    first, last = min(m[0] for m in matches), max(m[0] for m in matches)
    out, y, mo = [], first.year, first.month + 1
    while True:
        if mo > 12:
            y, mo = y + 1, 1
        t = datetime(y, mo, 1)
        if t > last:
            return out
        out.append((t, ""))
        mo += 1


_JOB = None  # (matches, names, half_life, prior_sd, active_days), inherited by forked workers


def _fit_before(matches, t0, half_life, prior_sd):
    past = [m for m in matches if m[0] < t0]
    if not past:
        return {}
    ids = sorted({p for m in past for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    w = 0.5 ** (np.array([(t0 - m[0]).total_seconds() / 86400 for m in past]) / half_life) * np.array([m[3] for m in past])
    b, _ = fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), prior_sd)
    return dict(zip(ids, b))


def _snapshot_chunk(snaps):
    matches, names, half_life, prior_sd, active_days, credits, invite_half_life = _JOB
    rows, prev = [], {}
    for snap_t, snap_event in snaps:
        past = [m for m in matches if m[0] <= snap_t]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        age = np.array([(snap_t - m[0]).total_seconds() / 86400 for m in past])
        decay = 0.5 ** (age / half_life) if half_life > 0 else np.ones(len(past))
        weights = decay * np.array([m[3] for m in past])
        winners = np.array([idx[m[1]] for m in past])
        losers = np.array([idx[m[2]] for m in past])
        x0 = np.array([prev.get(p, 0.0) for p in ids])
        virtual = [(idx[p], level, sign, n * 0.5 ** ((snap_t - t).total_seconds() / 86400 / invite_half_life))
                   for t, p, level, wins, losses in credits if t <= snap_t and p in idx
                   for sign, n in ((1.0, wins), (-1.0, losses)) if n > 0]
        virtual = tuple(np.array(c) for c in zip(*virtual)) if virtual else None
        b, se = fit_bt(winners, losers, weights, len(ids), prior_sd, x0=x0, virtual=virtual)
        prev = dict(zip(ids, b))

        n_matches = np.zeros(len(ids))
        eff = np.zeros(len(ids))
        last = {}
        for m, w in zip(past, decay):
            for p in (m[1], m[2]):
                n_matches[idx[p]] += 1
                eff[idx[p]] += w
                last[p] = max(last.get(p, m[0]), m[0])
        for p, i in idx.items():
            if (snap_t - last[p]).days > active_days:
                continue
            rows.append({
                "date": snap_t.strftime("%Y-%m-%d"), "event": snap_event, "player_id": p,
                "name": names.get(p, p), "elo": round(1500 + ELO_SCALE * b[i], 1),
                "se": round(ELO_SCALE * se[i], 1), "results": int(n_matches[i]),
                "eff_results": round(eff[i], 2), "last_played": last[p].strftime("%Y-%m-%d"),
            })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categories", default="official",
                    help="comma list of match categories to use (open, open_special, community, official, ...)")
    ap.add_argument("--half-life", type=float, default=240, help="days; <=0 disables time decay")
    ap.add_argument("--prior-sd", type=float, default=0.4, help="prior sd of ratings in log-odds units (0.4 ~ 70 Elo)")
    ap.add_argument("--games", action="store_true", help="count individual games instead of match (series) wins")
    ap.add_argument("--active-days", type=float, default=730,
                    help="only report a player at a snapshot if they played within this many days")
    ap.add_argument("--open-weight", type=float, default=1.0,
                    help="weight of Open-series results relative to official events (0 = official only)")
    ap.add_argument("--out", default=os.path.join(DATA, "ratings_timeline.csv"))
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="worker processes")
    ap.add_argument("--no-invites", action="store_true", help="skip the OCC ladder-invite credit (invites.py)")
    ap.add_argument("--invite-half-life", type=float, default=120,
                    help="days; how fast the ladder-invite credit fades (real results take over)")
    args = ap.parse_args()

    matches = load_matches(set(args.categories.split(",")), args.games, args.open_weight)
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(DATA, "players.csv")))}
    snapshots = sorted(event_snapshots(matches) + month_snapshots(matches))
    print(f"{len(matches)} results, {len(snapshots)} snapshots")

    # snapshots are independent fits; split them into contiguous chunks, one per core, and warm-start
    # each fit from the previous snapshot of the same chunk (consecutive snapshots differ by one event)
    global _JOB
    credits = [] if args.no_invites else invites.credits(lambda t: _fit_before(matches, t, args.half_life, args.prior_sd))
    print(f"ladder-invite credits: {len(credits)}")
    _JOB = (matches, names, args.half_life, args.prior_sd, args.active_days, credits, args.invite_half_life)
    workers = max(1, min(args.jobs, len(snapshots)))
    chunks = [list(c) for c in np.array_split(np.arange(len(snapshots)), workers) if len(c)]
    jobs = [[snapshots[i] for i in c] for c in chunks]
    if workers > 1:
        with Pool(workers) as pool:
            parts = pool.map(_snapshot_chunk, jobs)
    else:
        parts = [_snapshot_chunk(j) for j in jobs]
    rows = [r for part in parts for r in part]

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
