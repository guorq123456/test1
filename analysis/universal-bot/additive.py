"""Shared evaluation, step B's first form: each pairing's linear model as my deck's term + the opponent's.

    cd <checkout> && PYTHONPATH=. python3 analysis/universal-bot/additive.py OUT [--exclude me:op ...]

Reads every fitted per-pairing phased model on this branch (svsim/learn/phased_models/*.json and its
local-* candidate folders; the top-level file wins where both exist; the Game8 ramp/dragon mirror
left out) and fits, on the standardized coefficients (a feature's effect per its typical spread in
that pairing's positions: weights per raw unit blow up where a feature barely varies in one pairing,
and their correlations were near 0 even between fitted pairings), feature by feature and
moment by moment (ended, act), w(me, op) = w0 + a[me] + b[op] by least squares over the pairings not
excluded. Writes a phased models folder OUT holding that prediction for every pairing of the decks
seen (the excluded and never-fitted ones included), with each feature standardized by the mean of
the means and stds of the source pairings that share a deck with it (the model has no intercept; the constant that changes is the
same for every position, so the search's comparisons don't see it).

This is the additive form of the plan's w0 + A·e(D_me) + B·e(D_op) with one free vector per deck;
with four decks the deck description (learn.deckrep) can't be fitted yet (79 numbers per deck from
four decks), so this step tests what the description would have to reproduce: that a pairing's
weights are mostly a sum of a my-deck part and an opponent part. Also prints, per pairing, how well
the fit of the other pairings predicts it (correlation of standardized weights).
"""
import argparse
import glob
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path("svsim/learn/phased_models")


def collect():
    out = {}
    for path in sorted(glob.glob(str(ROOT / "local-*" / "*.json"))) + sorted(glob.glob(str(ROOT / "*.json"))):
        d = json.load(open(path))
        info = d["info"]
        if info["deck"] in ("ramp", "dragon"):
            continue
        out[(info["deck"], info["opponent"], info["moment"])] = d      # top level read last: it wins
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--exclude", nargs="*", default=[])
    a = ap.parse_args()
    excl = {tuple(x.split(":")) for x in a.exclude}
    models = collect()
    os.makedirs(a.out, exist_ok=True)
    for moment in ("ended", "act"):
        ms = {(me, op): d for (me, op, mo), d in models.items() if mo == moment}
        decks = sorted({x for k in ms for x in k})
        train = sorted(k for k in ms if k not in excl)
        names = ms[train[0]]["names"]

        def design(me, op):
            return [1.0] + [1.0 * (me == d) for d in decks[1:]] + [1.0 * (op == d) for d in decks[1:]]

        W = np.array([np.array(ms[k]["coef"]) for k in train])
        D = np.array([design(*k) for k in train])
        B, *_ = np.linalg.lstsq(D, W, rcond=None)
        src = ms[train[0]]
        for me in decks:
            for op in decks:
                w = np.array(design(me, op)) @ B
                near = [k for k in train if me in k or op in k] or train   # spreads of positions like these
                mean = np.mean([ms[k]["mean"] for k in near], axis=0)
                std = np.mean([ms[k]["std"] for k in near], axis=0)
                model = {"names": names, "coef": list(map(float, w)), "mean": list(map(float, mean)),
                         "std": list(map(float, std)), "potential": src["potential"], "version": src["version"],
                         "info": {"deck": me, "opponent": op, "moment": moment, "kind": "additive",
                                  "fitted_on": [f"{x}:{y}" for x, y in train],
                                  "held_out": (me, op) in excl, "had_specialist": (me, op) in ms}}
                json.dump(model, open(os.path.join(a.out, f"{me}-{op}-{moment}.json"), "w"), indent=1)
                if (me, op) in ms:
                    actual = np.array(ms[(me, op)]["coef"])
                    print(f"{moment:5s} {me:9s} vs {op:9s} {'HELD OUT' if (me, op) in excl else 'fitted  '} "
                          f"corr(additive, specialist) {np.corrcoef(w, actual)[0, 1]:.3f}")
                else:
                    print(f"{moment:5s} {me:9s} vs {op:9s} no specialist: additive only")


if __name__ == "__main__":
    main()
