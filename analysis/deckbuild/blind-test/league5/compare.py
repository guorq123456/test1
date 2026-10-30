"""The two passes of metric 5 side by side: does the deeper bot rank the 56 decks as the cheap one does? (the
architecture thread's claim 11, plan section 10.6: deckbuilding is held back by the playing level, P 0.75; wrong if
the two rankings correlate above 0.9).

Each deck's score is its mean over the pairs it played (league.json "means", cross-group only). Reported: the
Spearman and Pearson correlations of the two passes' scores over the decks, with a bootstrap interval over decks
(2000 draws, seed fixed); each group's mean in both passes; the decks that moved most.

    python analysis/deckbuild/blind-test/league5/compare.py league5/cheap/league.json league5/deep/league.json

Condition: 对手卡表已知（牌序、手牌未知）.
"""
import json
import sys

import numpy as np


def ranks(x):
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    for v in np.unique(x):                    # ties share their mean rank
        r[x == v] = r[x == v].mean()
    return r


def spearman(a, b):
    return float(np.corrcoef(ranks(a), ranks(b))[0, 1])


def main():
    cheap, deep = (json.load(open(p)) for p in sys.argv[1:3])
    assert cheap["decks"] == deep["decks"], "the two passes must have the same roster in the same order"
    decks = cheap["decks"]
    a, b = np.array(cheap["means"]), np.array(deep["means"])
    rng = np.random.default_rng(85960002)
    boot = []
    for _ in range(2000):
        k = rng.integers(0, len(a), len(a))
        boot.append(spearman(a[k], b[k]))
    print(f"decks {len(decks)}; cheap {cheap['agent']} seed {cheap['seed']}; deep {deep['agent']} seed {deep['seed']}")
    print(f"Spearman {spearman(a, b):.3f} (95% {np.percentile(boot, 2.5):.3f}-{np.percentile(boot, 97.5):.3f}); "
          f"Pearson {np.corrcoef(a, b)[0, 1]:.3f}")
    print("claim 11 (wrong if above 0.9):", "WRONG" if spearman(a, b) > 0.9 else "stands")
    for name, run in (("cheap", cheap), ("deep", deep)):
        # Each deck's mean has its pairs' noise (SE over the pairs it played); the correlation two passes of one bot
        # with fresh seeds would reach is about the reliability 1 - mean(SE^2) / var(means). The SE over pairs counts
        # the matchups' real differences as noise too, so this reliability is a lower bound.
        se2 = []
        for row in run["score"]:
            x = np.array([v for v in row if v is not None], float)
            se2.append(x.var(ddof=1) / len(x))
        m = np.array(run["means"])
        print(f"{name}: spread of deck scores {100 * m.std():.1f} points, reliability at least {1 - np.mean(se2) / m.var():.3f}")
    groups = []
    for d in decks:
        g = d.split("/", 1)[0]
        if g not in groups:
            groups.append(g)
    print("group  cheap  deep")
    for g in groups:
        k = np.array([d.split("/", 1)[0] == g for d in decks])
        print(f"{g:7s} {100 * a[k].mean():5.1f} {100 * b[k].mean():5.1f}")
    move = b - a
    print("moved most (deep - cheap, points):")
    for j in np.argsort(-np.abs(move))[:12]:
        print(f"  {decks[j]:32s} {100 * a[j]:5.1f} -> {100 * b[j]:5.1f} ({100 * move[j]:+.1f})")
    print("condition: 对手卡表已知（牌序、手牌未知）")


if __name__ == "__main__":
    main()
