"""Pick half-life / prior strength by out-of-sample prediction.

For each event (after the first few), fit on everything strictly before the
event starts and score the event's matches with log loss and accuracy.
Unknown players get rating 0 (the prior mean).
"""
import argparse
import itertools
import math

import numpy as np

from bt import event_snapshots, fit_bt, load_matches


def evaluate(matches, half_life, prior_sd, warmup=3):
    events = event_snapshots(matches)
    start = {}
    for t, _, _, _, ev in matches:
        start[ev] = min(start.get(ev, t), t)
    ll, acc, n = 0.0, 0.0, 0.0
    for _, ev in events[warmup:]:
        t0 = start[ev]
        past = [m for m in matches if m[0] < t0]
        test = [m for m in matches if m[4] == ev]
        ids = sorted({p for m in past for p in (m[1], m[2])})
        idx = {p: i for i, p in enumerate(ids)}
        age = np.array([(t0 - m[0]).total_seconds() / 86400 for m in past])
        w = (0.5 ** (age / half_life) if half_life else np.ones(len(past))) * np.array([m[3] for m in past])
        b, _ = fit_bt(np.array([idx[m[1]] for m in past]), np.array([idx[m[2]] for m in past]), w, len(ids), prior_sd)
        for m in test:
            d = (b[idx[m[1]]] if m[1] in idx else 0.0) - (b[idx[m[2]]] if m[2] in idx else 0.0)
            p = 1 / (1 + math.exp(-d))  # prob. the actual winner wins
            ll -= m[3] * math.log(p)
            acc += m[3] * ((p > 0.5) + 0.5 * (p == 0.5))
            n += m[3]
    return ll / n, acc / n, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", default="official")
    ap.add_argument("--games", action="store_true")
    args = ap.parse_args()
    matches = load_matches(set(args.categories.split(",")), args.games)
    print(f"baseline (coin flip) log loss = {math.log(2):.4f}")
    print("half_life  prior_sd  logloss  accuracy  n")
    for hl, sd in itertools.product([90, 180, 365, 730, 0], [0.4, 0.6, 0.8, 1.0, 1.5]):
        ll, acc, n = evaluate(matches, hl, sd)
        print(f"{hl or 'none':>9}  {sd:8.2f}  {ll:.4f}   {acc:.3f}   {int(n)}")


if __name__ == "__main__":
    main()
