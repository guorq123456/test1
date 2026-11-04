"""R1: is the playouts' verdict d predictable beyond the hand-written score? (cross-validated, before any gate)

For each labelled decision (r1_labels.py), the two children are rebuilt from the record (replayed to the step, the
two moves applied; an end of turn as the search scores it, search.evaluate.after_end_of_turn: before the opponent's
turn begins) and described from the mover's view by learn.features (version 2, without the planner's
potential: the version's per-side terms, the hand's and the deck's roles), the extras "tempo", "hand" and "hpphase",
and the engine counters a combo, ramp or amulet deck builds (cards played this turn, followers entered this match,
cemetery, evolutions, distinct costs played, amulets on the field and their countdowns), each side's. The rows are
the differences, first child minus second.

Models of d, compared by 5-fold cross-validation over decisions (folds by the deal's key):
- hand: d ~ a * tanh(dh / s) (dh the hand-written score's difference; s chosen in the fold);
- hand+phi: the same plus ridge-penalised w . dphi (standardised; the penalty chosen in the fold).
Reported: the held-out correlation with d, the share of clear decisions (|d| > 2 SE) whose sign is right, and the
ceiling the labels' own noise allows (the correlation a perfect predictor of the true d would reach).

    python analysis/playnet/r1_fit.py runs/r1/pilot.jsonl --records runs/s1/rec-p3 [--out analysis/playnet/fit-pilot.json]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

EXTRAS = ("tempo", "hand", "hpphase")
ENGINE = ["combo", "rally", "shadows", "evolutions", "costs_played", "amulets", "amulet_countdown", "max_pp"]


def engine(state, side: int) -> list[float]:
    from svsim.core.enums import CardType
    p = state.players[side]
    amulets = [c for c in p.field if getattr(c.defn, "type", None) == CardType.AMULET]
    return [p.combo, p.rally, p.shadows, p.evolutions, len(p.played_base_costs), len(amulets),
            sum(c.countdown for c in amulets if c.countdown is not None), p.max_pp]


def names() -> list[str]:
    from svsim.learn import features as F
    return (F.names(False, 2)[:-1] + F.extra_names(EXTRAS) + [f"me_{n}" for n in ENGINE] +
            [f"op_{n}" for n in ENGINE])


def describe(state, me: int) -> list[float]:
    from svsim.learn import features as F
    return (F.features(state, me, potential=False, version=2)[:-1] + F.extra_features(state, me, EXTRAS) +
            engine(state, me) + engine(state, 1 - me))


def rebuild(row: dict, records: Path):
    """The two children of the row's decision, and the mover."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    with gzip.open(records / row["file"], "rt") as fh:
        for k, text in enumerate(fh):
            if k == row["line"]:
                record = json.loads(text)
                break
    for i, (state, _action) in enumerate(R.steps(record)):
        if i == row["step"]:
            out = []
            for mv in row["moves"]:
                action = from_dict(mv)
                if isinstance(action, EndTurn):         # as the search scores it (and r1_labels' hand score):
                    child = after_end_of_turn(state)    # the turn's end abilities done, the opponent's turn not begun
                else:
                    child = state.clone()
                    apply(child, action)
                out.append(child)
            return out, state.active
    raise ValueError(f"step {row['step']} not in {row['file']}:{row['line']}")


def table(rows: list, records: Path):
    X, dh, d, se, keys = [], [], [], [], []
    for row in rows:
        (c1, c2), me = rebuild(row, records)
        X.append(np.array(describe(c1, me)) - np.array(describe(c2, me)))
        dh.append(row["hand"][0] - row["hand"][1])
        D = np.array(row["results"][0], float) - np.array(row["results"][1], float)
        d.append(D.mean())
        se.append(math.sqrt(D.var(ddof=1) / len(D)))
        keys.append(int(row["key"]))
    return np.array(X), np.array(dh), np.array(d), np.array(se), np.array(keys)


def _ridge(A: np.ndarray, y: np.ndarray, lam: np.ndarray) -> np.ndarray:
    return np.linalg.solve(A.T @ A + np.diag(lam), A.T @ y)


def _design(X, dh, s, mean, std):
    return np.column_stack([np.ones(len(dh)), np.tanh(dh / s), (X - mean) / std])


def fit_fold(X, dh, d, train, scales=(2.0, 5.0, 10.0, 20.0, 50.0), lams=(1.0, 10.0, 100.0, 1000.0, 1e4),
             use_phi=True):
    """The best (s, lam) by an inner 4-fold split of `train`, refitted on all of `train`; returns predict(idx)."""
    mean, std = X[train].mean(axis=0), X[train].std(axis=0)
    std[std < 1e-9] = 1.0
    k = X.shape[1] if use_phi else 0
    rng = np.random.default_rng(len(train))
    inner = rng.integers(0, 4, len(train))
    best = None
    for s in scales:
        A = _design(X, dh, s, mean, std)[:, :2 + k]
        for lam in (lams if use_phi else (0.0,)):
            pen = np.r_[0.0, 0.0, np.full(k, lam)]
            err = 0.0
            for f in range(4):
                tr, te = train[inner != f], train[inner == f]
                coef = _ridge(A[tr], d[tr], pen + 1e-9)
                err += float(((A[te] @ coef - d[te]) ** 2).sum())
            if best is None or err < best[0]:
                best = (err, s, lam)
    _, s, lam = best
    A = _design(X, dh, s, mean, std)[:, :2 + k]
    coef = _ridge(A[train], d[train], np.r_[0.0, 0.0, np.full(k, lam)] + 1e-9)
    return (lambda idx: A[idx] @ coef), {"s": s, "lam": lam, "coef": coef}


def crossval(X, dh, d, se, keys, folds: int = 5) -> dict:
    fold = np.array([int(k) % folds for k in keys])
    out = {}
    for name, use_phi in (("hand", False), ("hand+phi", True)):
        pred = np.zeros(len(d))
        for f in range(folds):
            train, test = np.where(fold != f)[0], np.where(fold == f)[0]
            predict, _ = fit_fold(X, dh, d, train, use_phi=use_phi)
            pred[test] = predict(test)
        clear = (se > 0) & (np.abs(d) > 2 * se) | (se == 0) & (d != 0)
        out[name] = {"corr": float(np.corrcoef(pred, d)[0, 1]),
                     "mse": float(((pred - d) ** 2).mean()),
                     "sign_clear": float((np.sign(pred[clear]) == np.sign(d[clear])).mean()),
                     "sign_teacher_wrong_clear": float((pred[clear & (d < 0)] < 0).mean())
                     if (clear & (d < 0)).any() else None}
    true_var = d.var() - (se ** 2).mean()
    out["ceiling_corr"] = float(math.sqrt(max(true_var, 0) / d.var()))
    out["mse_constant"] = float(d.var())
    out["clear"] = int(((se > 0) & (np.abs(d) > 2 * se) | (se == 0) & (d != 0)).sum())
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--records", default="runs/s1/rec-p3")
    ap.add_argument("--cache")
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = [r for r in map(json.loads, open(args.path)) if r.get("results") is not None]
    if args.cache and Path(args.cache).exists():
        z = np.load(args.cache)
        X, dh, d, se, keys = z["X"], z["dh"], z["d"], z["se"], z["keys"]
    else:
        X, dh, d, se, keys = table(rows, Path(args.records))
        if args.cache:
            np.savez(args.cache, X=X, dh=dh, d=d, se=se, keys=keys)
    res = {"decisions": len(d), "features": len(names()), **crossval(X, dh, d, se, keys)}
    all_idx = np.arange(len(d))
    _, info = fit_fold(X, dh, d, all_idx)
    top = np.argsort(-np.abs(info["coef"][2:]))[:15]
    res["full_fit"] = {"s": info["s"], "lam": info["lam"], "hand_coef": float(info["coef"][1]),
                       "top_features": [[names()[j], round(float(info["coef"][2 + j]), 4)] for j in top]}
    res["condition"] = "对手卡表已知（牌序、手牌未知）"
    text = json.dumps(res, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        open(args.out, "w").write(text + "\n")


if __name__ == "__main__":
    main()
