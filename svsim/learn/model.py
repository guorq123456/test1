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
# positional, no card ids). Off unless an evaluation is made with aliases=ALIASES (arena "+alias"),
# and only when both decks have the same stand-in; other pairings keep the class fallback.
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

    def __init__(self, models: dict | None = None, fallback=None, aliases: dict | None = None):
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
