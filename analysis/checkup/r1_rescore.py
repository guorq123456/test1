"""R1's hand-written baseline, rescored as the search scores (the bot check-up, step A; search.mcts leaf contract).

R1 (analysis/playnet) stored, per labelled decision, the hand-written score of the teacher's two moves' children
(row "hand"). A child inside the mover's turn was scored with player_moves_next=True; the search scores every leaf
with False (search.mcts.leaf_score). This script rebuilds both children from the records (search.mcts.search_child),
checks that the old rule reproduces the stored numbers (so the rebuild is the right position), scores them under
the contract, and re-runs R1's comparison (analysis/playnet/r1_cards.py: hand alone, + generic features, + card
sums, both) with the contract's score; the features are R1's cached ones (their rebuild already matched the
search's, aff45d01, and tests/test_leaf_contract.py checks that rule).

    python analysis/checkup/r1_rescore.py --cache-dir runs/r1 --records runs/s1/rec-p3 \
        [--out analysis/checkup/r1-rescored.json]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
VERSION = "r1-rescore-1 (leaf contract 1)"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows(path: Path) -> list:
    with gzip.open(path, "rt") as fh:
        return [r for r in map(json.loads, fh) if r.get("results") is not None]


RECORDS = None


def score_row(row: dict) -> tuple:
    """(old rule's two scores, the contract's two scores, the two children's phases)."""
    from svsim.core.actions import from_dict
    from svsim.search.evaluate import evaluate
    from svsim.search.mcts import leaf_phase, leaf_score, search_child
    from svsim.tools import records as R
    with gzip.open(RECORDS / row["file"], "rt") as fh:
        for k, text in enumerate(fh):
            if k == row["line"]:
                record = json.loads(text)
                break
    for i, (state, _a) in enumerate(R.steps(record)):
        if i == row["step"]:
            me = state.active
            old, new, phase = [], [], []
            for mv in row["moves"]:
                child = search_child(state, from_dict(mv))
                old.append(float(evaluate(child, me, player_moves_next=child.active == me)))
                new.append(leaf_score(child, me))
                phase.append(leaf_phase(child, me))
            return old, new, phase
    raise ValueError("step not found")


def _init(records):
    global RECORDS
    RECORDS = Path(records)


def rescore(rows: list, records: str, workers: int) -> dict:
    with Pool(workers, initializer=_init, initargs=(records,)) as pool:
        got = pool.map(score_row, rows, chunksize=20)
    old = np.array([g[0] for g in got])
    new = np.array([g[1] for g in got])
    stored = np.array([r["hand"] for r in rows], float)
    phases = [tuple(g[2]) for g in got]
    return {"old": old, "new": new, "stored": stored, "phases": phases}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache-dir", default="runs/r1")
    ap.add_argument("--records", default="runs/s1/rec-p3")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out")
    args = ap.parse_args()
    cards = _module("r1_cards", ROOT / "analysis/playnet/r1_cards.py")
    cd = Path(args.cache_dir)
    res = {"version": VERSION, "condition": "对手卡表已知（牌序、手牌未知）"}
    sets = {}
    for name, path, cache in (("test", "analysis/playnet/pilot.jsonl.gz", "cards-test.npz"),
                              ("train", "analysis/playnet/labels-m4.jsonl.gz", "cards-train.npz")):
        rows = _rows(ROOT / path)
        z = dict(np.load(cd / cache))
        assert len(z["d"]) == len(rows), (name, len(z["d"]), len(rows))
        sc = rescore(rows, args.records, args.workers)
        # the rebuild is the labelled position: the old rule gives the stored numbers (rounded to 3 places there)
        repro = float(np.mean(np.abs(sc["old"] - sc["stored"]) < 2e-3))
        changed = float(np.mean(np.abs(sc["new"] - sc["old"]) > 1e-9))
        in_turn = np.array([[p == "in_turn" for p in ph] for ph in sc["phases"]])
        dh_old, dh_new = sc["stored"][:, 0] - sc["stored"][:, 1], sc["new"][:, 0] - sc["new"][:, 1]
        res[name] = {"decisions": len(rows), "old_rule_reproduces_stored": repro,
                     "children_rescored_differently": changed,
                     "children_in_turn": float(in_turn.mean()),
                     "decisions_whose_order_flips": float(np.mean(np.sign(dh_old) != np.sign(dh_new)))}
        z_new = dict(z)
        z_new["dh"] = dh_new
        sets[name] = (z, z_new)
        np.save(cd / f"hand-contract-{name}.npy", sc["new"])
    (tr_old, tr_new), (te_old, te_new) = sets["train"], sets["test"]
    d, se = te_new["d"], te_new["se"]
    clear = (se > 0) & (np.abs(d) > 2 * se) | (se == 0) & (d != 0)
    for tag, z in (("stored", te_old), ("contract", te_new)):
        dh = z["dh"]
        res[f"pilot_hand_{tag}"] = {"corr_dh_d": float(np.corrcoef(dh, d)[0, 1]),
                                    "sign_agree_clear": float((np.sign(dh[clear]) == np.sign(d[clear])).mean()),
                                    "clear": int(clear.sum())}
    empty = lambda t: np.zeros((len(t["d"]), 0))
    for tag, (tr, te) in (("stored", (tr_old, te_old)), ("contract", (tr_new, te_new))):
        res[f"models_{tag}"] = {
            "hand": cards.evaluate(tr, te, empty),
            "hand+generic": cards.evaluate(tr, te, lambda t: t["G"]),
            "hand+cards": cards.evaluate(tr, te, lambda t: t["C"]),
            "hand+generic+cards": cards.evaluate(tr, te, lambda t: np.hstack([t["G"], t["C"]]))}
    text = json.dumps(res, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
