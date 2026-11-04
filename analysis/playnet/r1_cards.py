"""R1: does seeing the cards make d predictable? (after the pilot: generic position features added nothing)

Each child is described as in r1_fit.py (the generic features) plus, per zone, the sum of its cards' static rows
(learn.tokens.static: what a card is and does, measured from its definition and script; no card id, no per-card
value): my hand, my field, my leader area, my deck (what is left in it), the opponent's field and leader area (their
hand is hidden). A row is the difference of the two children, first minus second, so a decision between two cards of
one turn reads as "this card's effects on the field and the other's in hand" against the reverse.

Fitted on the m = 4 labels (r1_labels.py, the pilot's games left out), judged on the pilot (m = 12, lower noise): the
held-out correlation with d, the sign on clear decisions, on the clear decisions where the teacher's first is the
worse, and what switching to the second move wherever the model prefers it would gain a decision. The penalty and the hand-written score's scale are chosen by 5-fold cross-validation inside the training set.

    python analysis/playnet/r1_cards.py --train runs/r1/labels-m4.jsonl --test runs/r1/pilot.jsonl \
        --records runs/s1/rec-p3 [--cache-dir runs/r1] [--out analysis/playnet/cards.json]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_spec = importlib.util.spec_from_file_location("r1_fit", Path(__file__).with_name("r1_fit.py"))
FIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FIT)

ZONES = ("my_hand", "my_field", "my_leader", "my_deck", "op_field", "op_leader")


def card_sums(state, me: int) -> np.ndarray:
    from svsim.learn import tokens as T
    p, o = state.players[me], state.players[1 - me]
    zones = (p.hand, p.field, p.leader_area, p.deck_view(), o.field, o.leader_area)
    out = np.zeros((len(zones), len(T.static_names())), np.float64)
    for z, cards in enumerate(zones):
        for c in cards:
            out[z] += T.static(c.defn)
    return out.ravel()


def table(rows: list, records: Path):
    G, C, dh, d, se, keys = [], [], [], [], [], []
    for row in rows:
        (c1, c2), me = FIT.rebuild(row, records)
        G.append(np.array(FIT.describe(c1, me)) - np.array(FIT.describe(c2, me)))
        C.append(card_sums(c1, me) - card_sums(c2, me))
        dh.append(row["hand"][0] - row["hand"][1])
        D = np.array(row["results"][0], float) - np.array(row["results"][1], float)
        d.append(D.mean())
        se.append(math.sqrt(D.var(ddof=1) / len(D)))
        keys.append(int(row["key"]))
    return {k: np.array(v) for k, v in zip(("G", "C", "dh", "d", "se", "keys"), (G, C, dh, d, se, keys))}


def load(path: str, records: Path, cache: Path | None) -> dict:
    rows = [r for r in map(json.loads, open(path)) if r.get("results") is not None]
    if cache is not None and cache.exists():
        z = dict(np.load(cache))
        if len(z["d"]) == len(rows):
            return z
        done = len(z["d"])                    # rows are appended in order: encode only the new ones
        new = table(rows[done:], records)
        z = {k: np.concatenate([z[k], new[k]]) for k in z}
    else:
        z = table(rows, records)
    if cache is not None:
        np.savez(cache, **z)
    return z


def evaluate(train: dict, test: dict, X_of) -> dict:
    Xtr, Xte = X_of(train), X_of(test)
    X = np.vstack([Xtr, Xte])
    dh = np.r_[train["dh"], test["dh"]]
    d = np.r_[train["d"], test["d"]]
    tr, te = np.arange(len(train["d"])), np.arange(len(train["d"]), len(d))
    predict, info = FIT.fit_fold(X, dh, d, tr, use_phi=X.shape[1] > 0, lams=(1.0, 10.0, 100.0, 1e3, 1e4, 1e5, 1e6))
    pred = predict(te)
    dt, st = test["d"], test["se"]
    clear = (st > 0) & (np.abs(dt) > 2 * st) | (st == 0) & (dt != 0)
    wrong = clear & (dt < 0)
    return {"corr": float(np.corrcoef(pred, dt)[0, 1]), "mse": float(((pred - dt) ** 2).mean()),
            "sign_clear": float((np.sign(pred[clear]) == np.sign(dt[clear])).mean()),
            "teacher_wrong_clear_right": f"{int((pred[wrong] < 0).sum())}/{int(wrong.sum())}",
            # Switching to the second move wherever the model says it is better: how often, and what it gains a
            # decision on average over always taking the teacher's first (win-rate points, SE over decisions).
            "switch_rate": float((pred < 0).mean()),
            "switch_gain": float(np.mean(np.where(pred < 0, -dt, 0.0))),
            "switch_gain_se": float(np.std(np.where(pred < 0, -dt, 0.0), ddof=1) / math.sqrt(len(dt))),
            "s": info["s"], "lam": info["lam"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--records", default="runs/s1/rec-p3")
    ap.add_argument("--cache-dir")
    ap.add_argument("--out")
    args = ap.parse_args()
    records = Path(args.records)
    cd = Path(args.cache_dir) if args.cache_dir else None
    train = load(args.train, records, cd / "cards-train.npz" if cd else None)
    test = load(args.test, records, cd / "cards-test.npz" if cd else None)
    empty = lambda t: np.zeros((len(t["d"]), 0))
    res = {"train": len(train["d"]), "test": len(test["d"]),
           "test_ceiling_corr": float(math.sqrt(max(test["d"].var() - (test["se"] ** 2).mean(), 0) / test["d"].var())),
           "hand": evaluate(train, test, empty),
           "hand+generic": evaluate(train, test, lambda t: t["G"]),
           "hand+cards": evaluate(train, test, lambda t: t["C"]),
           "hand+generic+cards": evaluate(train, test, lambda t: np.hstack([t["G"], t["C"]])),
           "condition": "对手卡表已知（牌序、手牌未知）"}
    text = json.dumps(res, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        open(args.out, "w").write(text + "\n")


if __name__ == "__main__":
    main()
