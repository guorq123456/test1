"""A learned linear evaluation, one per deck (keyed by the deck's craft).

`LinearValue` turns features into a win probability: P(win) = logistic(coef .
standardized features). Agents use it like the hand-set evaluate.Weights: an
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
                 version: int = 1):
        self.coef, self.mean, self.std, self.potential = coef, mean, std, potential
        self.info = info or {}
        self.version = version
        assert len(coef) == len(mean) == len(std) == len(names(potential, version))

    def logit(self, state: GameState, player: int) -> float:
        x = features(state, player, self.potential, self.version)
        return sum(c * ((v - m) / s) for c, v, m, s in zip(self.coef, x, self.mean, self.std))

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"names": names(self.potential, self.version), "coef": self.coef,
                                    "mean": self.mean, "std": self.std, "potential": self.potential,
                                    "version": self.version, "info": self.info},
                                   ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "LinearValue":
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(d["coef"], d["mean"], d["std"], d["potential"], d.get("info"), d.get("version", 1))

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
