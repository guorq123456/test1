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
import math
import operator
from collections import Counter
from pathlib import Path

from svsim.core.enums import Craft
from svsim.core.state import GameState
from svsim.learn.features import extra_features, features, names

WEIGHTS = Path(__file__).resolve().parent / "weights"
_mul, _tanh = operator.mul, math.tanh
SCALE = 8.0                      # ISMCTS's logistic squash: value = 1 / (1 + exp(-score / 8))


class LinearValue:
    def __init__(self, coef: list, mean: list, std: list, potential: bool, info: dict | None = None,
                 version: int = 1, hidden: dict | None = None, deck_desc: bool = False, extras: tuple = (),
                 hv=None):
        self.coef, self.mean, self.std, self.potential = coef, mean, std, potential
        self.info = info or {}
        self.version = version
        self.hidden = hidden             # {"W1": [[per hidden unit] per feature], "b1": [...], "w2": [...]}
        self.deck_desc = deck_desc       # both decks' learn.deckdesc vectors after the features (a shared model)
        self.extras = tuple(extras)      # named feature sets after those (learn.features.EXTRAS), by name
        self.hv = hv                     # the hand-value student "hand_value" reads (learn.handvalue), if used
        assert len(coef) == len(mean) == len(std) == len(self.names())
        if hidden:
            assert len(hidden["W1"]) == len(coef) and len(hidden["b1"]) == len(hidden["w2"])

    def names(self) -> list[str]:
        out = names(self.potential, self.version)
        if self.deck_desc:
            from svsim.learn import deckdesc
            out = out + [f"deck_me_{n}" for n in deckdesc.names()] + [f"deck_op_{n}" for n in deckdesc.names()]
        if self.extras:
            from svsim.learn.features import extra_names
            out = out + extra_names(self.extras)
        return out

    def inputs(self, state: GameState, player: int) -> list:
        x = features(state, player, self.potential, self.version)
        if self.deck_desc:
            from svsim.learn import deckdesc
            x = list(x) + deckdesc.pair(state, player)
        if self.extras:
            x = list(x) + extra_features(state, player, self.extras, self.hv)
        return x

    def logit(self, state: GameState, player: int) -> float:
        if not self.hidden:              # the same products summed in the same order, without the list
            return sum(c * ((v - m) / s) for c, v, m, s in zip(self.coef, self.inputs(state, player), self.mean,
                                                               self.std))
        x = [(v - m) / s for v, m, s in zip(self.inputs(state, player), self.mean, self.std)]
        return sum(c * v for c, v in zip(self.coef, x)) + self._hidden_out(x)

    # A small hidden layer (at most _PY_HIDDEN weights that can be nonzero, e.g. cand-nl's 16 units over 71 inputs)
    # is summed in plain Python (2026-10-10): numpy in the search's hot path cost more than the layer itself, the
    # whole search slowing by about 15% beyond it (analysis/nonlinear/README.md). A larger one keeps numpy, as
    # before. Rows of W1 that are all zero (inputs that don't feed the layer) are skipped.
    _PY_HIDDEN = 4096

    def _hidden_out(self, x: list) -> float:
        plan = self.__dict__.get("_hidden_plan")
        if plan is None:
            W1, b1, w2 = self.hidden["W1"], self.hidden["b1"], self.hidden["w2"]
            rows = [i for i, row in enumerate(W1) if any(row)]
            if len(rows) * len(b1) <= self._PY_HIDDEN:
                plan = ("py", rows, [tuple(W1[i][j] for i in rows) for j in range(len(b1))], list(b1), list(w2))
            else:                        # numpy: 64 hidden units over ~200 features is too slow as Python loops
                import numpy as np
                plan = ("np", np) + tuple(np.asarray(self.hidden[k], dtype=np.float64) for k in ("W1", "b1", "w2"))
            self._hidden_plan = plan
        if plan[0] == "py":
            _, rows, cols, b1, w2 = plan
            xr = [x[i] for i in rows]
            return sum(map(_mul, [_tanh(b + sum(map(_mul, xr, col))) for b, col in zip(b1, cols)], w2))
        _, np, W1, b1, w2 = plan
        return float(np.tanh(np.asarray(x) @ W1 + b1) @ w2)

    def save(self, path: Path) -> None:
        d = {"names": self.names(), "coef": self.coef, "mean": self.mean, "std": self.std,
             "potential": self.potential, "version": self.version, "info": self.info}
        if self.hidden:
            d["hidden"] = self.hidden
        if self.deck_desc:
            d["deck_desc"] = True
        if self.extras:
            d["extras"] = list(self.extras)
        path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "LinearValue":
        d = json.loads(path.read_text(encoding="utf-8"))
        extras = tuple(d.get("extras", ()))
        hv = None
        if "hand_value" in extras:       # its student sits beside it: <pairing>-hv.npz for <pairing>-<moment>.json
            from svsim.learn.handvalue import load_cached
            hv = load_cached(path.with_name(path.name.rsplit("-", 1)[0] + "-hv.npz"))
        return cls(d["coef"], d["mean"], d["std"], d["potential"], d.get("info"), d.get("version", 1),
                   d.get("hidden"), d.get("deck_desc", False), extras, hv)

    def weights_by_name(self) -> dict:
        """Coefficients per raw (unstandardized) feature unit, for reading."""
        return {n: c / s for n, c, s in zip(self.names(), self.coef, self.std)}


def deck_craft(state: GameState, player: int) -> Craft:
    p = state.players[player]
    crafts = Counter(c.defn.craft for c in p.hand + p.deck + p.field if c.defn.craft != Craft.NEUTRAL)
    return crafts.most_common(1)[0][0] if crafts else Craft.NEUTRAL


def deck_key(state: GameState, player: int) -> str | None:
    """The named deck (cards.decks.NAMED) `player` registered (engine.new_game files it), else the one
    the cards they have fit (a position built by hand); None for another deck."""
    p = state.players[player]
    if p.deck_name is not None:
        return p.deck_name or None
    from svsim.cards.decks import identify
    return identify(p.hand + p.deck + p.field + p.leader_area)


# Stand-ins for a mirror without models of its own (the architecture session, 2026-10-07): the
# tournament Ramp Dragon plays the Game8 build's mirror models (the features are functional and
# positional, no card ids). Only when both decks have the same stand-in; other pairings keep the
# class fallback. On by default since the gate (v2 with it against v2 without, ramp-t mirror: 67.3% +-
# 3.6% over a fixed 600 games); aliases=None turns it off (arena "+noalias", for ablations). A stopgap:
# the mirror's own fitted models, when they come, are gated against this, not against the class fallback.
ALIASES = {"ramp-t": "ramp"}


def matchup_keys(state: GameState, player: int, aliases: dict | None = None) -> list:
    """The keys a matchup's model may be filed under, most specific first: the pair of named decks,
    with `aliases` the pair of their stand-ins for a mirror (ALIASES), then the pair of classes."""
    out = []
    mine, theirs = deck_key(state, player), deck_key(state, 1 - player)
    if mine is not None and theirs is not None:
        out.append((mine, theirs))
        if aliases and mine == theirs and mine in aliases:
            out.append((aliases[mine], aliases[theirs]))
    out.append((deck_craft(state, player), deck_craft(state, 1 - player)))
    return out


def parse_key(part: str):
    """A file-name part: a named deck's key (cards.decks.NAMED) or a class name."""
    from svsim.cards.decks import NAMED
    return part if part in NAMED else Craft[part.upper()]


def split_keys(stem: str) -> list:
    """A file name's keys (parse_key), joined by "-": a named deck's key may have "-" in it (elf-t), so
    each part is the longest known name from the left. KeyError if some part is no known name."""
    from svsim.cards.decks import NAMED
    parts, out, i = stem.split("-"), [], 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            name = "-".join(parts[i:j])
            if name in NAMED or name.upper() in Craft.__members__:
                out.append(parse_key(name))
                i = j
                break
        else:
            raise KeyError(stem)
    return out


class Learned:
    """Evaluation with each deck's learned model: the one for the matchup (filed under the pair
    of named decks, else the pair of classes) if there is one, else the deck's (by craft); the
    hand-set one otherwise."""

    def __init__(self, models: dict | None = None, fallback=None, aliases: dict | None = ALIASES):
        from svsim.search.evaluate import DEFAULT
        self.models = models if models is not None else load_all()
        self.fallback = fallback or DEFAULT
        self.aliases = aliases                     # ALIASES: a mirror without models plays its stand-in's

    def score(self, state: GameState, player: int, player_moves_next: bool = False) -> float:
        """Learned from end-of-turn positions, so `player_moves_next` doesn't change it."""
        from svsim.search.evaluate import WIN, evaluate
        if state.winner is not None:
            return WIN if state.winner == player else (-WIN if state.winner == 1 - player else 0.0)
        model = next((self.models[k] for k in matchup_keys(state, player, self.aliases) if k in self.models), None) \
            or self.models.get(deck_craft(state, player))
        if model is None:
            return evaluate(state, player, self.fallback, player_moves_next)
        return SCALE * model.logit(state, player)


def load_all(folder: Path | None = None) -> dict:
    """The models in `folder` (default: $SVSIM_WEIGHTS, else svsim/learn/weights):
    <craft>.json for a deck, <deck>-<opponent deck>.json (named decks, cards.decks.NAMED) or
    <craft>-<opponent craft>.json for a matchup."""
    import os
    folder = folder or Path(os.environ.get("SVSIM_WEIGHTS") or WEIGHTS)
    out = {}
    for path in folder.glob("*.json"):
        try:
            keys = split_keys(path.stem)
        except KeyError:
            continue
        if len(keys) == 1 and isinstance(keys[0], Craft):
            out[keys[0]] = LinearValue.load(path)
        elif len(keys) == 2 and isinstance(keys[0], Craft) == isinstance(keys[1], Craft):
            out[tuple(keys)] = LinearValue.load(path)
    return out
