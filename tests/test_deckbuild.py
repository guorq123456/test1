import random
from collections import Counter

from svsim.cards import decks
from svsim.cards.pool import POOL
from svsim.core.enums import Craft
from svsim.tools import deckbuild


def _legal(ids, craft):
    return decks.validate([POOL[i] for i in ids], craft) == []


def test_random_decks_and_variants_are_legal():
    rng = random.Random(1)
    for craft in deckbuild.CLASSES:
        ids = deckbuild.random_ids(craft, rng)
        assert _legal(ids, craft)
        for _ in range(20):
            v = deckbuild.variant(ids, craft, rng)
            assert _legal(v, craft)
            changed = sum(a != b for a, b in zip(ids, v))
            assert 1 <= changed <= 3                    # slots keep their places: the shuffle pairs them


def test_legalize_keeps_legal_slots_and_fixes_the_rest():
    rng = random.Random(2)
    _, _, ids = decks.deckcode.decode_deck("".join(decks.RAMP_T_HASH))
    out = deckbuild.legalize(ids, Craft.DRAGON, rng)
    assert out == ids                                   # already legal: unchanged, slot for slot
    foreign = [i for i in decks.deckcode.decode_deck("".join(decks.PIRATE_T_HASH))[2]
               if POOL[i].craft == Craft.SWORD][0]
    bad = [foreign] + ids[1:]
    fixed = deckbuild.legalize(bad, Craft.DRAGON, rng)
    assert _legal(fixed, Craft.DRAGON) and fixed[1:] == ids[1:]
    assert deckbuild.legalize(ids[:30], Craft.DRAGON, rng)[:30] == ids[:30]   # short lists are filled


def test_variant_respects_three_copies():
    rng = random.Random(3)
    craft = Craft.FOREST
    ids = deckbuild.random_ids(craft, rng)
    for _ in range(200):
        ids = deckbuild.variant(ids, craft, rng)
        assert max(Counter(ids).values()) <= decks.MAX_COPIES
