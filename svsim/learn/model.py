"""A learned evaluation, one per deck (keyed by the deck's craft) or matchup.

`LinearValue` turns features into a win probability: P(win) = logistic(coef .
standardized features), plus, optionally, one small hidden layer
(w2 . tanh(W1 x + b1), x the standardized features), which lets the evaluation
weigh things against each other (a big follower is worth more when the
opponent has no removal left) where a sum of separate terms can't. Agents use it like the hand-set evaluate.Weights: an
object with `score(state, player, player_moves_next)` returning a score on the
same scale as evaluate (ISMCTS squashes score / 8 into 0..1, so score = 8 *
logit). `Learned` picks each player's model by the craft of their deck and
falls back to the hand-set evaluation for decks without one.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from svsim.core.enums import Craft
from svsim.core.state import GameState
from svsim.learn.features import features, names

WEIGHTS = Path(__file__).resolve().parent / "weights"
SCALE = 8.0                      # ISMCTS's logistic squash: value = 1 / (1 + exp(-score / 8))


class LinearValue:
    def __init__(self, coef: list, mean: list, std: list, potential: bool, info: dict | None = None,
                 version: int = 1, hidden: dict | None = None):
        self.coef, self.mean, self.std, self.potential = coef, mean, std, potential
        self.info = info or {}
        self.version = version
        self.hidden = hidden             # {"W1": [[per hidden unit] per feature], "b1": [...], "w2": [...]}
        assert len(coef) == len(mean) == len(std) == len(names(potential, version))
        if hidden:
            assert len(hidden["W1"]) == len(coef) and len(hidden["b1"]) == len(hidden["w2"])

    def logit(self, state: GameState, player: int) -> float:
        x = [(v - m) / s for v, m, s in zip(features(state, player, self.potential, self.version), self.mean,
                                             self.std)]
        out = sum(c * v for c, v in zip(self.coef, x))
        if self.hidden:
            import math
            h = list(self.hidden["b1"])
            for v, row in zip(x, self.hidden["W1"]):
                if v:
                    for j, a in enumerate(row):
                        h[j] += v * a
            out += sum(b * math.tanh(a) for a, b in zip(h, self.hidden["w2"]))
        return out

    def save(self, path: Path) -> None:
        d = {"names": names(self.potential, self.version), "coef": self.coef, "mean": self.mean, "std": self.std,
             "potential": self.potential, "version": self.version, "info": self.info}
        if self.hidden:
            d["hidden"] = self.hidden
        path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "LinearValue":
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(d["coef"], d["mean"], d["std"], d["potential"], d.get("info"), d.get("version", 1),
                   d.get("hidden"))

    def weights_by_name(self) -> dict:
        """Coefficients per raw (unstandardized) feature unit, for reading."""
        return {n: c / s for n, c, s in zip(names(self.potential, self.version), self.coef, self.std)}


def deck_craft(state: GameState, player: int) -> Craft:
    p = state.players[player]
    crafts = Counter(c.defn.craft for c in p.hand + p.deck + p.field if c.defn.craft != Craft.NEUTRAL)
    return crafts.most_common(1)[0][0] if crafts else Craft.NEUTRAL


class Learned:
    """Evaluation with each deck's learned model: the one for the matchup (keyed by the
    deck's craft and the opponent's) if there is one, else the deck's (by craft); the
    hand-set one otherwise."""

    def __init__(self, models: dict | None = None, fallback=None):
        from svsim.search.evaluate import DEFAULT
        self.models = models if models is not None else load_all()
        self.fallback = fallback or DEFAULT

    def score(self, state: GameState, player: int, player_moves_next: bool = False) -> float:
        """Learned from end-of-turn positions, so `player_moves_next` doesn't change it."""
        from svsim.search.evaluate import WIN, evaluate
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        mine = deck_craft(state, player)
        model = self.models.get((mine, deck_craft(state, 1 - player))) or self.models.get(mine)
        if model is None:
            return evaluate(state, player, self.fallback, player_moves_next)
        return SCALE * model.logit(state, player)


def load_all(folder: Path | None = None) -> dict:
    """The models in `folder` (default: $SVSIM_WEIGHTS, else svsim/learn/weights):
    <craft>.json for a deck, <craft>-<opponent craft>.json for a matchup."""
    import os
    folder = folder or Path(os.environ.get("SVSIM_WEIGHTS") or WEIGHTS)
    out = {}
    for path in folder.glob("*.json"):
        try:
            crafts = [Craft[part.upper()] for part in path.stem.split("-")]
        except KeyError:
            continue
        if len(crafts) in (1, 2):
            out[crafts[0] if len(crafts) == 1 else tuple(crafts)] = LinearValue.load(path)
    return out
