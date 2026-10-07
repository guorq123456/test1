"""What a card and a deck are, for an evaluation shared by every deck: measured, never named.

The player's question (2026-10-07): one bot that plays every deck and understands a new deck quickly.
The bot's hands and eyes already work for any deck (scripts, search, the features of learn.features);
what is kept per deck is the evaluation's weights, which need a deck's name to be found. Here a card
and a deck get a description from what they do, so weights can be a function of the description and
a deck no one has fitted still gets some (docs/universal-bot-plan.md):

- `card_vector(defn)`: cost and stats, card type, keywords, the roles sandbox (learn.roles: what
  playing it does; what it does by itself on the field each round, plain and evolved), what evolving
  and super-evolving it with a point adds (learn.payoff), and which kinds of ability its script has
  (Fanfare, Last Words, Evolve, listeners, Engage, Enhance, Invoke, Accelerate, tokens it makes...).
  No card id, no name, no class.
- `deck_static(cards)`: the 40 cards' vectors pooled: their mean, the count and mean roles of each
  cost band, and how much the cards share traits (a tribe deck holds together, a toolbox does not).

Nothing here is written per card, and a card the sandbox can't play still gets its stats and tags.
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from svsim.core.enums import CardType, Keyword
from svsim.learn.roles import RECURRING, ROLES

KEYWORDS = ("WARD", "STORM", "RUSH", "BANE", "DRAIN", "AMBUSH", "BARRIER", "INTIMIDATE", "AURA")
TYPES = (CardType.FOLLOWER, CardType.AMULET, CardType.COUNTDOWN_AMULET, CardType.SPELL)
# Kinds of ability, from which hooks a card's script defines (grouped: a listener is a listener).
TAGS = {
    "fanfare": ("fanfare",),
    "cast": ("cast",),
    "last_words": ("last_words",),
    "evolve": ("on_evolve", "on_super_evolve", "on_evolved"),
    "strike": ("strike", "follower_strike", "leader_strike", "clash"),
    "turn": ("on_turn_start", "on_turn_end", "on_opponent_turn_start", "on_opponent_turn_end"),
    "listener": ("on_play", "on_ally_enter", "on_enemy_enter", "on_ally_evolve", "on_attack",
                 "on_card_destroyed", "on_ally_leave", "on_engage", "on_earth_rite", "on_draw",
                 "on_leader_healed"),
    "engage": ("engage",),
    "in_hand": ("on_drawn", "on_discard", "on_spellboost", "on_buffed"),
}
EXTRA = ("enhance", "invoke", "accelerate", "crystallize", "skybound", "fuse", "makes_tokens", "choice")
BANDS = ((0, 2), (3, 4), (5, 6), (7, 99))

CARD_NAMES = (["cost", "atk", "life"] + [f"type_{t.name.lower()}" for t in TYPES] + [f"kw_{k.lower()}" for k in KEYWORDS]
              + [f"role_{r}" for r in ROLES] + [f"rec_{r}" for r in RECURRING] + [f"rec_evo_{r}" for r in RECURRING]
              + ["evo_face", "evo_value", "sevo_face", "sevo_value"] + [f"tag_{t}" for t in TAGS] + [f"tag_{t}" for t in EXTRA])

_CARD: dict = {}


def card_vector(defn) -> np.ndarray:
    hit = _CARD.get(defn.card_id)
    if hit is not None:
        return hit
    from svsim.core import script as S
    from svsim.learn.payoff import evolve_parts
    from svsim.learn.roles import card_roles, recurring
    v = [float(defn.cost), float(defn.atk), float(defn.life)]
    v += [1.0 if defn.type == t else 0.0 for t in TYPES]
    v += [1.0 if defn.keywords & Keyword[k] else 0.0 for k in KEYWORDS]
    v += list(card_roles(defn))
    on_field = defn.is_follower or defn.type in (CardType.AMULET, CardType.COUNTDOWN_AMULET)
    v += list(recurring(defn, False)) if on_field else [0.0] * 3
    v += list(recurring(defn, True)) if defn.is_follower else [0.0] * 3
    if defn.is_follower:
        v += list(evolve_parts(defn, False)) + list(evolve_parts(defn, True))
    else:
        v += [0.0] * 4
    sc = S.script_for(defn.card_id)
    v += [1.0 if any(getattr(sc, h, None) is not None for h in hooks) else 0.0 for hooks in TAGS.values()]
    v += [1.0 if sc.enhance else 0.0,
          1.0 if defn.card_id in S.INVOKERS else 0.0,
          1.0 if defn.accelerate is not None else 0.0,
          1.0 if defn.crystallize is not None else 0.0,
          1.0 if sc.skybound else 0.0,
          1.0 if sc.fuse_filter is not None else 0.0,
          float(min(len(defn.related), 3)),
          1.0 if (sc.modes or sc.play_targets) else 0.0]
    out = _CARD[defn.card_id] = np.array(v, dtype=float)
    return out


def _roles_index():
    return [CARD_NAMES.index(f"role_{r}") for r in ROLES]


def deck_static(cards) -> np.ndarray:
    """A deck (its card definitions, 40 with repeats) as one vector: see `deck_names()`."""
    vecs = np.array([card_vector(c) for c in cards])
    out = [vecs.mean(axis=0)]
    ri = _roles_index()
    for lo, hi in BANDS:
        inband = [i for i, c in enumerate(cards) if lo <= c.cost <= hi]
        share = len(inband) / len(cards)
        roles = vecs[inband][:, ri].mean(axis=0) if inband else np.zeros(len(ri))
        out.append(np.concatenate([[share], roles]))
    traits = Counter(t for c in cards for t in set(c.traits))
    cohesion = np.mean([max((traits[t] - 1 for t in c.traits), default=0) / (len(cards) - 1) for c in cards])
    singles = len(set(c.card_id for c in cards)) / len(cards)
    out.append(np.array([cohesion, singles]))
    return np.concatenate(out)


def deck_names() -> list[str]:
    names = [f"mean_{n}" for n in CARD_NAMES]
    for lo, hi in BANDS:
        tag = f"{lo}-{hi}" if hi < 99 else f"{lo}+"
        names += [f"band{tag}_share"] + [f"band{tag}_{r}" for r in ROLES]
    return names + ["trait_cohesion", "distinct_share"]
