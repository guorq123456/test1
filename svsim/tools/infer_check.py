"""Is search.infer's guess at the opponent's hand closer than a uniform draw? On game records, where both hands
are known (self-play, or the trainer's games for the bot's side), at each player's first decision of a turn.

    python -m svsim.tools.infer_check <records>.jsonl [...] --games 60 --alpha 1 0.5 0.3 0.1 --tau -1 0 0.5 1 2
    python -m svsim.tools.infer_check <trainer export dir>/*.json --side 1          (the bot's side only)

For each (tau, alpha): the mean overlap of a drawn hand with the true one (cards of the same kind count up to
their number in the true hand), as a share of the hand, over --samples draws per point (alpha 1 is the uniform
draw core.view.determinize makes today); and, per tau, how often a flagged card (could and clearly should have
been played) was in the hand, against the base rate (hand size / hand and deck).
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from multiprocessing import Pool


def _load(path: str) -> list:
    if path.endswith(".json"):
        d = json.load(open(path, encoding="utf-8"))
        return [d.get("record", d)]
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def _points(job) -> list:
    """[(true hand ids, pool [(uid, id)], {tau: flagged uids})] at each first decision of a turn in one game."""
    record, taus, side, min_turn = job
    from svsim.core.enums import Phase
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.search.infer import unplayed_gains
    from svsim.tools import records as R
    weights = PhasedLearned(fallback=Learned())
    out, seen = [], set()
    for state, _ in R.steps(record):
        p = state.active
        turn = (p, state.players[p].turns_taken)
        if state.phase != Phase.MAIN or turn in seen or (side is not None and p != side):
            continue
        seen.add(turn)
        if state.players[p].turns_taken < min_turn:
            continue
        them = state.players[1 - p]
        if not them.hand:
            continue
        gains = unplayed_gains(state, p, weights)
        flagged = {tau: {c.uid for c in them.hand + them.deck if gains.get(c.defn.card_id, -1e9) >= tau}
                   for tau in taus}
        out.append(([c.defn.card_id for c in them.hand], [(c.uid, c.defn.card_id) for c in them.hand + them.deck],
                    flagged))
    return out


def overlap(true_ids: list, pool: list, flagged: set, alpha: float, samples: int, rng: random.Random) -> float:
    """Mean share of the true hand a weighted draw (core.view.determinize's keys) gets right."""
    want, n, total = Counter(true_ids), len(true_ids), 0.0
    for _ in range(samples):
        keys = sorted(((rng.random() ** (1.0 / (alpha if uid in flagged else 1.0)), cid) for uid, cid in pool),
                      reverse=True)
        got = Counter(cid for _, cid in keys[:n])
        total += sum(min(got[c], k) for c, k in want.items()) / n
    return total / samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("records", nargs="+")
    parser.add_argument("--games", type=int, default=60, help="games per file at most")
    parser.add_argument("--alpha", type=float, nargs="+", default=[1.0, 0.5, 0.3, 0.1])
    parser.add_argument("--tau", type=float, nargs="+", default=[-1.0, 0.0, 0.5, 1.0, 2.0])
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--side", type=int, default=None, help="only this seat's decisions (1: the trainer's bot)")
    parser.add_argument("--min-turn", type=int, default=2, help="from this own turn on")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    records = [r for path in args.records for r in _load(path)[:args.games]]
    with Pool(args.workers) as pool:
        points = [p for part in pool.imap(_points, [(r, args.tau, args.side, args.min_turn) for r in records])
                  for p in part]
    rng = random.Random(1)
    base = sum(len(t) / len(pl) for t, pl, _ in points) / len(points)
    print(f"{len(points)} points from {len(records)} games; a card's base rate of being in hand {base:.3f}")
    for tau in args.tau:
        flagged_in = [sum(1 for uid, _ in pl if uid in f[tau] and uid in {u for u, _ in pl[:len(t)]})
                      for t, pl, f in points]
        flagged_n = [len(f[tau]) for _, _, f in points]
        rate = sum(flagged_in) / max(1, sum(flagged_n))
        row = [f"tau {tau:g}: {sum(flagged_n) / len(points):.1f} flagged per point, in hand {rate:.3f}"]
        for alpha in args.alpha:
            o = sum(overlap(t, pl, f[tau], alpha, args.samples, rng) for t, pl, f in points) / len(points)
            row.append(f"alpha {alpha:g} {o:.4f}")
        print("  " + " | ".join(row), flush=True)


if __name__ == "__main__":
    main()
