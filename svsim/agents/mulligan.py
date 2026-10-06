"""Opening-hand redraws (every agent uses `mulligan`).

Three layers, the first that applies wins:

1. The player's rules for a deck they know (`PLAYER_RULES`, their words):
   Rhinoceroach Forest (2026-10-06): its only cards of 5 or more are Glade and
   Bayle. Glade draws, clears and evolves in one card (against midrange decks
   a must-keep); Bayle is only strong once it costs 0, so keeping one is
   usually right (a 0-cost Bayle refills the board mid-game or adds to the
   Rhinoceroach turn) and a second is not wanted. Some cheap cards should go
   back: Baby Carbuncle only pays off after the super-evolution turns, and
   Lambent Cairn, Eradicating Arrow and Virid Lieutenant look cheap but are
   mid-game cards.
2. A deck built around ramp (one card in eight or more raises max play
   points, search.race.ramps) keeps the ramp and redraws the rest, all of it
   if there is none: the player's way with Ramp Dragon against Rhinoceroach
   Forest ("留牌围着跳费走，很多时候全换找跳费").
3. Otherwise, redraw what costs 5 or more.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from svsim.cards import decks, forest, unlimited
from svsim.core.actions import Mulligan


@dataclass(frozen=True)
class Rules:
    redraw: frozenset = frozenset()       # card ids always sent back
    keep: frozenset = frozenset()         # card ids always kept, whatever they cost
    at_most: dict = field(default_factory=dict)   # card id -> copies worth keeping


PLAYER_RULES = {
    "rhino": Rules(
        redraw=frozenset(c.card_id for c in (unlimited.BABY_CARBUNCLE, unlimited.LAMBENT_CAIRN,
                                              unlimited.ERADICATING_ARROW, forest.VIRID_LIEUTENANT)),
        keep=frozenset({unlimited.GLADE.card_id, unlimited.BAYLE.card_id}),
        at_most={unlimited.BAYLE.card_id: 1}),
}
_DECK_KEYS: dict = {}


def _deck_key(cards) -> str | None:
    """Which of the known decks these 40 cards are, if any."""
    if not _DECK_KEYS:
        listings = {"rhino": decks.RHINO_FOREST, "ramp": decks.RAMP_DRAGON, "pirate": decks.PIRATE_SWORD}
        for key, listing in listings.items():
            _DECK_KEYS[tuple(sorted(c.card_id for c in decks.build(listing)))] = key
    return _DECK_KEYS.get(tuple(sorted(c.defn.card_id for c in cards)))


def by_rules(hand, rules: Rules, threshold: int = 5) -> tuple:
    redraw, kept = [], {}
    for i, c in enumerate(hand):
        cid = c.defn.card_id
        if cid in rules.redraw:
            redraw.append(i)
        elif cid in rules.at_most and kept.get(cid, 0) >= rules.at_most[cid]:
            redraw.append(i)
        elif cid in rules.keep or c.cost < threshold:
            kept[cid] = kept.get(cid, 0) + 1
        else:
            redraw.append(i)
    return tuple(redraw)


def mulligan(state, threshold: int = 5) -> Mulligan:
    from svsim.search.race import ramps
    p = state.players[state.active]
    cards = p.hand + p.deck
    rules = PLAYER_RULES.get(_deck_key(cards))
    if rules is not None:
        return Mulligan(by_rules(p.hand, rules, threshold))
    if 8 * sum(ramps(c.defn) for c in cards) >= len(cards):
        return Mulligan(tuple(i for i, c in enumerate(p.hand) if not ramps(c.defn)))
    return Mulligan(tuple(i for i, c in enumerate(p.hand) if c.cost >= threshold))
