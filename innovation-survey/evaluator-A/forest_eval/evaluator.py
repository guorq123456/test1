"""The evaluator: a scoring function that is cheap, automatic, and hard to game.

设计要点 / Design points (each one answers a documented failure mode of
"AI scientist" systems, arXiv 2509.08713):

1. Fixed metric, fixed data, fixed splits -> no metric shopping, no
   benchmark shopping.
2. ``transfer`` score (leave-one-area-out) is reported next to the ``iid``
   score, and the *composite* used for ranking is the transfer score. A
   candidate cannot win by memorising spatial structure.
3. A sealed test set with a hard budget. Every sealed call is logged, so
   post-hoc selection on test performance is visible in the log.
4. Append-only JSONL audit log of every evaluation: candidate fingerprint,
   config, seeds, per-fold scores, wall time. Read the log, not the paper.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold

from .data import CovertypeSplits, WILDERNESS

# A candidate is: a config dict  ->  an (unfitted) sklearn estimator/pipeline.
CandidateBuilder = Callable[[dict[str, Any]], BaseEstimator]


def _fingerprint(config: dict[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


@dataclass
class EvalResult:
    fingerprint: str
    mode: str  # "dev" | "sealed"
    composite: float  # what the search should maximise
    iid_macro_f1: float | None
    iid_accuracy: float | None
    transfer_macro_f1: float | None  # mean over held-out areas
    transfer_per_area: dict[str, float] = field(default_factory=dict)
    sealed_macro_f1: float | None = None
    sealed_accuracy: float | None = None
    fit_seconds: float = 0.0
    config: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class SealedBudgetExceeded(RuntimeError):
    pass


class ForestEvaluator:
    def __init__(
        self,
        splits: CovertypeSplits,
        log_path: str | Path,
        sealed_budget: int = 3,
        iid_folds: int = 3,
        transfer_areas: tuple[int, ...] = (0, 1, 2, 3),
        seed: int = 0,
    ):
        self.s = splits
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.sealed_budget = sealed_budget
        self.iid_folds = iid_folds
        self.transfer_areas = transfer_areas
        self.seed = seed
        self._sealed_used = self._count_sealed_in_log()

    # ------------------------------------------------------------------ utils
    def _count_sealed_in_log(self) -> int:
        if not self.log_path.exists():
            return 0
        n = 0
        with self.log_path.open() as f:
            for line in f:
                try:
                    if json.loads(line).get("mode") == "sealed":
                        n += 1
                except json.JSONDecodeError:
                    continue
        return n

    def _log(self, result: EvalResult) -> None:
        rec = {"ts": time.time(), **result.to_json()}
        with self.log_path.open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    @staticmethod
    def _scores(y_true, y_pred) -> tuple[float, float]:
        return (
            float(f1_score(y_true, y_pred, average="macro")),
            float(accuracy_score(y_true, y_pred)),
        )

    # ------------------------------------------------------------- dev eval
    def evaluate(self, build: CandidateBuilder, config: dict[str, Any], note: str = "") -> EvalResult:
        """Score a candidate on the dev set only. Safe to call as often as you like."""
        fp = _fingerprint(config)
        t0 = time.time()
        X, y, g = self.s.X_dev, self.s.y_dev, self.s.groups_dev

        # iid: stratified k-fold
        skf = StratifiedKFold(n_splits=self.iid_folds, shuffle=True, random_state=self.seed)
        f1s, accs = [], []
        for tr, te in skf.split(X, y):
            est = clone(build(config))
            est.fit(X.iloc[tr], y[tr])
            f1, acc = self._scores(y[te], est.predict(X.iloc[te]))
            f1s.append(f1)
            accs.append(acc)

        # transfer: leave-one-wilderness-area-out
        per_area: dict[str, float] = {}
        for area in self.transfer_areas:
            tr, te = np.flatnonzero(g != area), np.flatnonzero(g == area)
            if len(te) == 0:
                continue
            est = clone(build(config))
            est.fit(X.iloc[tr], y[tr])
            f1, _ = self._scores(y[te], est.predict(X.iloc[te]))
            per_area[WILDERNESS[area]] = f1
        transfer = float(np.mean(list(per_area.values()))) if per_area else None

        res = EvalResult(
            fingerprint=fp,
            mode="dev",
            composite=transfer if transfer is not None else float(np.mean(f1s)),
            iid_macro_f1=float(np.mean(f1s)),
            iid_accuracy=float(np.mean(accs)),
            transfer_macro_f1=transfer,
            transfer_per_area=per_area,
            fit_seconds=time.time() - t0,
            config=config,
            note=note,
        )
        self._log(res)
        return res

    # ---------------------------------------------------------- sealed eval
    def evaluate_sealed(self, build: CandidateBuilder, config: dict[str, Any], note: str = "") -> EvalResult:
        """Train on ALL dev rows, score once on the sealed set. Budgeted and logged."""
        if self._sealed_used >= self.sealed_budget:
            raise SealedBudgetExceeded(
                f"sealed budget of {self.sealed_budget} already spent (see {self.log_path})"
            )
        self._sealed_used += 1
        fp = _fingerprint(config)
        t0 = time.time()
        est = clone(build(config))
        est.fit(self.s.X_dev, self.s.y_dev)
        pred = est.predict(self.s.X_sealed)
        f1, acc = self._scores(self.s.y_sealed, pred)
        # also report sealed score per area, for the honest picture
        per_area = {}
        for area in range(4):
            m = self.s.groups_sealed == area
            if m.any():
                per_area[WILDERNESS[area]] = float(
                    f1_score(self.s.y_sealed[m], pred[m], average="macro")
                )
        res = EvalResult(
            fingerprint=fp,
            mode="sealed",
            composite=f1,
            iid_macro_f1=None,
            iid_accuracy=None,
            transfer_macro_f1=None,
            transfer_per_area=per_area,
            sealed_macro_f1=f1,
            sealed_accuracy=acc,
            fit_seconds=time.time() - t0,
            config=config,
            note=f"sealed call {self._sealed_used}/{self.sealed_budget}. {note}",
        )
        self._log(res)
        return res

    # -------------------------------------------------------------- reports
    def leaderboard(self, top: int = 10) -> pd.DataFrame:
        if not self.log_path.exists():
            return pd.DataFrame()
        rows = [json.loads(l) for l in self.log_path.open() if l.strip()]
        df = pd.DataFrame(rows)
        dev = df[df["mode"] == "dev"].copy()
        if dev.empty:
            return dev
        dev = dev.sort_values("composite", ascending=False).drop_duplicates("fingerprint")
        cols = ["fingerprint", "composite", "iid_macro_f1", "transfer_macro_f1", "iid_accuracy", "fit_seconds", "note"]
        return dev[cols].head(top).reset_index(drop=True)
