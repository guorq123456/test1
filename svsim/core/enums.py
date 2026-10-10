"""Enumerations shared across the engine.

Numeric values of CardType and Craft match the official card database
(`type` and `class` fields), so imported data needs no remapping.
"""
from enum import IntEnum, IntFlag


class CardType(IntEnum):
    FOLLOWER = 1
    AMULET = 2
    COUNTDOWN_AMULET = 3
    SPELL = 4
    # Not official `type` values: leader-area objects, which the official data
    # lists under `specific_effect_card_info` (1 = crest, 4 = faith).
    CREST = 11
    FAITH = 12


class Craft(IntEnum):
    NEUTRAL = 0
    FOREST = 1
    SWORD = 2
    RUNE = 3
    DRAGON = 4
    ABYSS = 5
    HAVEN = 6
    PORTAL = 7


class Keyword(IntFlag):
    """Static keywords a card instance can currently have.

    Trigger keywords (Fanfare, Last Words, Strike, ...) are not flags: they are
    hooks on the card's script.
    """
    NONE = 0
    WARD = 1 << 0
    STORM = 1 << 1
    RUSH = 1 << 2
    BANE = 1 << 3
    DRAIN = 1 << 4
    AMBUSH = 1 << 5
    BARRIER = 1 << 6
    INTIMIDATE = 1 << 7
    AURA = 1 << 8

    # & and | by table (_KW): the same members IntFlag's own operators return (checked over every pair,
    # tests/test_enums.py), several times faster in Python 3.11, and search tests keywords a lot.
    def __and__(self, other):
        if other.__class__ is Keyword or other.__class__ is int:
            return _KW[int.__and__(self, other)]     # self >= 0: the bits are a subset of self's
        return IntFlag.__and__(self, other)

    __rand__ = __and__

    def __or__(self, other):
        if other.__class__ is Keyword or other.__class__ is int:
            v = int.__or__(self, other)
            if 0 <= v < len(_KW):
                return _KW[v]
        return IntFlag.__or__(self, other)

    __ror__ = __or__


_KW = [Keyword(i) for i in range(1 << 9)]   # every combination of the nine keywords


# English keyword names as they appear in official card text.
KEYWORD_NAMES = {
    "Ward": Keyword.WARD,
    "Storm": Keyword.STORM,
    "Rush": Keyword.RUSH,
    "Bane": Keyword.BANE,
    "Drain": Keyword.DRAIN,
    "Ambush": Keyword.AMBUSH,
    "Barrier": Keyword.BARRIER,
    "Intimidate": Keyword.INTIMIDATE,
    "Aura": Keyword.AURA,
}


class Phase(IntEnum):
    MULLIGAN = 0
    MAIN = 1
    OVER = 2


DRAW = -1  # GameState.winner value for a drawn game
