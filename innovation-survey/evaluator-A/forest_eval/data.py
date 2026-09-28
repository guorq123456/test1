"""Data loading and *sealed* splitting for the Covertype forestry benchmark.

数据来源 / Source: UCI Covertype (Roosevelt National Forest, Colorado; Blackard & Dean 1999).
581,012 30m cells, 54 cartographic features, 7 forest cover types.
The GitHub mirror we can reach mislabels its header (the four wilderness-area
one-hot columns are spread across ``wilderness_type`` and ``soil_type1..3``);
we verified column sums and restore the original UCI names here.

Why the split design matters (this is the whole point of "evaluator-first"):

* ``sealed``  – 20% of rows chosen by a salted hash. Nobody (human or agent)
  may look at it during search. The evaluator enforces a small budget of
  sealed evaluations and logs each one.
* ``dev``     – the other 80%. Search happens here.
* Inside ``dev`` we score two ways:
    - ``iid``      : random 5-fold CV — the usual (optimistic) number.
    - ``transfer`` : leave-one-wilderness-area-out — train on 3 areas, test on
      the 4th. Wilderness areas are spatially contiguous, so this is the
      cheapest honest proxy for *spatial* generalization, the classic
      pitfall of ecological ML.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

NUMERIC = [
    "Elevation",
    "Aspect",
    "Slope",
    "Horizontal_Distance_To_Hydrology",
    "Vertical_Distance_To_Hydrology",
    "Horizontal_Distance_To_Roadways",
    "Hillshade_9am",
    "Hillshade_Noon",
    "Hillshade_3pm",
    "Horizontal_Distance_To_Fire_Points",
]
WILDERNESS = ["Rawah", "Neota", "Comanche_Peak", "Cache_la_Poudre"]
SOIL = [f"Soil_Type{i}" for i in range(1, 41)]
TARGET = "Cover_Type"
COVER_NAMES = {
    1: "Spruce/Fir",
    2: "Lodgepole Pine",
    3: "Ponderosa Pine",
    4: "Cottonwood/Willow",
    5: "Aspen",
    6: "Douglas-fir",
    7: "Krummholz",
}


def _restore_uci_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    expected = 10 + 4 + 40 + 1
    if df.shape[1] != expected:
        raise ValueError(f"expected {expected} columns, got {df.shape[1]}")
    df.columns = NUMERIC + WILDERNESS + SOIL + [TARGET]
    # sanity: one-hot blocks must sum to 1 in every row
    assert (df[WILDERNESS].sum(axis=1) == 1).all(), "wilderness one-hot broken"
    assert (df[SOIL].sum(axis=1) == 1).all(), "soil one-hot broken"
    return df


def _sealed_mask(n: int, frac: float, salt: str) -> np.ndarray:
    """Deterministic, index-based membership: row i is sealed iff
    sha256(salt|i) mod 10_000 < frac*10_000. Stable across machines and
    independent of any shuffling library."""
    thresh = int(frac * 10_000)
    out = np.empty(n, dtype=bool)
    for i in range(n):
        h = hashlib.sha256(f"{salt}|{i}".encode()).digest()
        out[i] = int.from_bytes(h[:4], "big") % 10_000 < thresh
    return out


@dataclass
class CovertypeSplits:
    X_dev: pd.DataFrame
    y_dev: np.ndarray
    groups_dev: np.ndarray  # wilderness-area id 0..3 per dev row
    X_sealed: pd.DataFrame
    y_sealed: np.ndarray
    groups_sealed: np.ndarray

    def describe(self) -> str:
        lines = [
            f"dev rows    : {len(self.y_dev):,}",
            f"sealed rows : {len(self.y_sealed):,}",
            "dev rows per wilderness area: "
            + ", ".join(
                f"{WILDERNESS[g]}={int((self.groups_dev == g).sum()):,}" for g in range(4)
            ),
        ]
        return "\n".join(lines)


def load_covertype(
    csv_path: str | Path,
    sealed_frac: float = 0.20,
    salt: str = "forest_eval_v1",
    max_dev_rows: int | None = None,
    seed: int = 0,
) -> CovertypeSplits:
    """Load the mirror CSV, restore UCI names, and produce sealed/dev splits.

    ``max_dev_rows`` subsamples the *dev* portion only (stratified by area) so
    that a search loop can iterate quickly on 4 CPUs. The sealed set is never
    subsampled.
    """
    df = _restore_uci_columns(pd.read_csv(csv_path))
    y = df[TARGET].to_numpy()
    groups = df[WILDERNESS].to_numpy().argmax(axis=1)
    X = df.drop(columns=[TARGET])

    sealed = _sealed_mask(len(df), sealed_frac, salt)
    dev_idx = np.flatnonzero(~sealed)
    if max_dev_rows is not None and max_dev_rows < len(dev_idx):
        rng = np.random.default_rng(seed)
        # stratify by area so the small areas keep enough rows for transfer eval
        keep = []
        for g in range(4):
            idx_g = dev_idx[groups[dev_idx] == g]
            k = int(round(max_dev_rows * len(idx_g) / len(dev_idx)))
            keep.append(rng.choice(idx_g, size=min(k, len(idx_g)), replace=False))
        dev_idx = np.sort(np.concatenate(keep))

    return CovertypeSplits(
        X_dev=X.iloc[dev_idx].reset_index(drop=True),
        y_dev=y[dev_idx],
        groups_dev=groups[dev_idx],
        X_sealed=X.loc[sealed].reset_index(drop=True),
        y_sealed=y[sealed],
        groups_sealed=groups[sealed],
    )
