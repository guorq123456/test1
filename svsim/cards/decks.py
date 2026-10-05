"""Decklists and deck validation.

The starter decklists are Game8's (Pirate Sword 2026-09-30, Ramp Dragon
2026-10-05), decoded through the official deck API.
"""
from collections import Counter
import random

from svsim.core.carddef import CardDef
from svsim.core.enums import Craft
from svsim.core.script import has_script

from . import deckcode, dragon, neutral, sword
from .pool import POOL, collectible

DECK_SIZE = 40
MAX_COPIES = 3

PIRATE_SWORD = {
    sword.FLASHSTEP_QUICKBLADER: 3, sword.ORCHESTRATED_SILENCE: 3, sword.YIDMETRA: 3,
    sword.OPEN_SEA_SCOUT: 3, sword.WHIRLPOOL_GUNNER: 3, sword.SPLENDOR_OF_THE_GOLDBLOOM: 3,
    sword.SEVERED_TIES: 3, sword.ZETA_AND_BEA: 3, sword.LAGE_DOR: 3, sword.UNKEI: 3,
    sword.ROUGHWATER_FIRST_MATE: 3, sword.GOLDEN_KNIGHT: 3, sword.BARBAROS: 3,
    sword.BELTEZORE: 1,
}

RAMP_DRAGON = {
    neutral.LYRIA: 3, dragon.VORLALAI: 3, dragon.DRAGONEWT_PROMOTER: 3, dragon.KIMIKA: 2,
    dragon.SLOTH_OF_THE_CRESTPETAL: 3, dragon.DRAGONSIGN: 3, dragon.LAZING_FLAME: 1,
    dragon.ROAR_OF_PROMINENCE: 2, neutral.FATE_OF_THE_WORLD: 2, dragon.ZOOEY: 3,
    dragon.SAGATSUMATSU: 3, dragon.NORMAGDALA: 3, dragon.LUMIORE_AND_ARGENTE: 3,
    dragon.BURNITE: 3, dragon.ERNTZ: 3,
}

# Every card the simulator knows, by id (deck cards, tokens, leader-area objects).
KNOWN: dict[int, CardDef] = POOL


def build(counts: dict[CardDef, int]) -> list[CardDef]:
    return [card for card, n in counts.items() for _ in range(n)]


def craft_of(deck: list[CardDef]) -> Craft:
    crafts = {c.craft for c in deck} - {Craft.NEUTRAL}
    return crafts.pop() if len(crafts) == 1 else Craft.NEUTRAL


def validate(deck: list[CardDef], craft: Craft | None = None) -> list[str]:
    """Problems that make a deck illegal (empty list = legal)."""
    craft = craft_of(deck) if craft is None else craft
    problems = []
    if len(deck) != DECK_SIZE:
        problems.append(f"{len(deck)} cards, need {DECK_SIZE}")
    for card, n in Counter(deck).items():
        if n > MAX_COPIES:
            problems.append(f"{n} copies of {card.name}")
        if card.is_token:
            problems.append(f"{card.name} is a token")
        if card.craft not in (Craft.NEUTRAL, craft):
            problems.append(f"{card.name} is not {craft.name.title()} or Neutral")
        if card.card_set and not card.rotation and not card.is_token:
            problems.append(f"{card.name} is not legal in Rotation")
    return problems


def unimplemented(cards) -> list[CardDef]:
    """Cards with abilities but no script. Keyword-only and vanilla cards are fine
    without one; anything else silently playing as a vanilla card would be wrong."""
    return sorted({c for c in cards if c.has_ability and not has_script(c.card_id)},
                  key=lambda c: c.card_id)


def random_deck(craft: Craft, rng: random.Random, implemented_only: bool = True) -> list[CardDef]:
    """A random legal Rotation deck for `craft` (class and Neutral cards, up to 3
    copies each). With `implemented_only`, cards still missing a script are left out."""
    options = [c for c in collectible(craft)
               if not (implemented_only and c.has_ability and not has_script(c.card_id))]
    if len(options) * MAX_COPIES < DECK_SIZE:
        raise ValueError(f"only {len(options)} usable {craft.name.title()} cards")
    deck: list[CardDef] = []
    while len(deck) < DECK_SIZE:
        card = rng.choice(options)
        if deck.count(card) < MAX_COPIES:
            deck.append(card)
    return deck


def from_hash(deck_hash: str, pool: dict[int, CardDef] | None = None) -> list[CardDef]:
    """Build a deck from an official deck hash. Card ids missing from `pool`
    (default: the implemented cards) raise KeyError."""
    pool = KNOWN if pool is None else pool
    _, _, ids = deckcode.decode_deck(deck_hash)
    return [pool[i] for i in ids]


def to_hash(deck: list[CardDef], battle_format: int = deckcode.ROTATION) -> str:
    return deckcode.encode_deck(battle_format, int(craft_of(deck)), [c.card_id for c in deck])
