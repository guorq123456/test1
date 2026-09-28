"""The candidate space: what a searcher is allowed to vary.

A candidate ``config`` is a plain dict, so it can come from a human, a random
search, an evolutionary loop, or an LLM agent that writes JSON. ``build``
turns it into an unfitted sklearn pipeline.

Feature-engineering flags are deliberately *ecological* rather than generic,
so that a searcher's choices are interpretable:
    euclid_hydro  : straight-line distance to water from the two components
    elev_minus_vh : elevation of the nearest water body
    aspect_sincos : aspect as a circular variable
    shade_stats   : mean/range of the three hillshade values
    road_fire_mix : sums/differences of roads and fire-point distances
    drop_soil     : ignore the 40 soil one-hots (tests how much they matter)
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import SOIL

FEATURE_FLAGS = ["euclid_hydro", "elev_minus_vh", "aspect_sincos", "shade_stats", "road_fire_mix", "drop_soil"]


class EcoFeatures(BaseEstimator, TransformerMixin):
    def __init__(self, flags: tuple[str, ...] = ()):
        self.flags = flags

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        f = set(self.flags)
        if "euclid_hydro" in f:
            X["Euclid_Hydro"] = np.hypot(
                X["Horizontal_Distance_To_Hydrology"], X["Vertical_Distance_To_Hydrology"]
            )
        if "elev_minus_vh" in f:
            X["Elev_Water"] = X["Elevation"] - X["Vertical_Distance_To_Hydrology"]
        if "aspect_sincos" in f:
            rad = np.deg2rad(X["Aspect"])
            X["Aspect_sin"], X["Aspect_cos"] = np.sin(rad), np.cos(rad)
            X = X.drop(columns=["Aspect"])
        if "shade_stats" in f:
            sh = X[["Hillshade_9am", "Hillshade_Noon", "Hillshade_3pm"]]
            X["Shade_mean"] = sh.mean(axis=1)
            X["Shade_range"] = sh.max(axis=1) - sh.min(axis=1)
        if "road_fire_mix" in f:
            X["Road_plus_Fire"] = X["Horizontal_Distance_To_Roadways"] + X["Horizontal_Distance_To_Fire_Points"]
            X["Road_minus_Fire"] = X["Horizontal_Distance_To_Roadways"] - X["Horizontal_Distance_To_Fire_Points"]
        if "drop_soil" in f:
            X = X.drop(columns=SOIL)
        return X


def build(config: dict[str, Any]) -> BaseEstimator:
    flags = tuple(config.get("features", ()))
    model = config.get("model", "hgb")
    p = config.get("params", {})
    seed = config.get("seed", 0)
    if model == "hgb":
        clf = HistGradientBoostingClassifier(
            max_iter=p.get("max_iter", 200),
            learning_rate=p.get("learning_rate", 0.1),
            max_leaf_nodes=p.get("max_leaf_nodes", 31),
            l2_regularization=p.get("l2", 0.0),
            class_weight=p.get("class_weight"),
            random_state=seed,
        )
        return Pipeline([("feat", EcoFeatures(flags)), ("clf", clf)])
    if model == "rf":
        clf = RandomForestClassifier(
            n_estimators=p.get("n_estimators", 200),
            max_depth=p.get("max_depth"),
            min_samples_leaf=p.get("min_samples_leaf", 1),
            class_weight=p.get("class_weight"),
            n_jobs=-1,
            random_state=seed,
        )
        return Pipeline([("feat", EcoFeatures(flags)), ("clf", clf)])
    if model == "logreg":
        clf = LogisticRegression(C=p.get("C", 1.0), max_iter=2000, class_weight=p.get("class_weight"))
        return Pipeline([("feat", EcoFeatures(flags)), ("scale", StandardScaler()), ("clf", clf)])
    raise ValueError(f"unknown model {model!r}")


# ------------------------------------------------------------------ sampling
def random_config(rng: random.Random) -> dict[str, Any]:
    model = rng.choice(["hgb", "hgb", "rf", "logreg"])
    feats = tuple(sorted(f for f in FEATURE_FLAGS if rng.random() < 0.4))
    cw = rng.choice([None, "balanced"])
    if model == "hgb":
        params = {
            "max_iter": rng.choice([100, 200, 400]),
            "learning_rate": rng.choice([0.03, 0.1, 0.2]),
            "max_leaf_nodes": rng.choice([15, 31, 63, 127]),
            "l2": rng.choice([0.0, 0.1, 1.0]),
            "class_weight": cw,
        }
    elif model == "rf":
        params = {
            "n_estimators": rng.choice([100, 200]),
            "max_depth": rng.choice([None, 12, 20]),
            "min_samples_leaf": rng.choice([1, 2, 5]),
            "class_weight": cw,
        }
    else:
        params = {"C": rng.choice([0.1, 1.0, 10.0]), "class_weight": cw}
    return {"model": model, "features": feats, "params": params, "seed": 0}


def mutate(config: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """One small edit: flip a feature flag or nudge one hyper-parameter."""
    c = {"model": config["model"], "features": tuple(config["features"]), "params": dict(config["params"]), "seed": 0}
    if rng.random() < 0.5:
        flag = rng.choice(FEATURE_FLAGS)
        feats = set(c["features"])
        feats.symmetric_difference_update({flag})
        c["features"] = tuple(sorted(feats))
    else:
        fresh = random_config(rng)
        if fresh["model"] == c["model"]:
            k = rng.choice(list(c["params"].keys()))
            c["params"][k] = fresh["params"][k]
        else:
            c = fresh
    return c
