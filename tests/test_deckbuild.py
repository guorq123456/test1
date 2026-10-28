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
    ids = deckbuild.random_ids(Craft.DRAGON, rng)
    assert deckbuild.legalize(ids, Craft.DRAGON, rng) == ids      # already legal: unchanged, slot for slot
    foreign = deckbuild.legal_cards(Craft.SWORD)
    foreign = next(c.card_id for c in foreign if c.craft == Craft.SWORD)
    fixed = deckbuild.legalize([foreign] + ids[1:], Craft.DRAGON, rng)
    assert _legal(fixed, Craft.DRAGON) and fixed[1:] == ids[1:]
    assert deckbuild.legalize(ids[:30], Craft.DRAGON, rng)[:30] == ids[:30]   # short lists are filled


def test_tournament_seeds_are_legal_after_legalize():
    # the 2026-10-07 lists predate card set 10: cards that left Rotation give their slots to legal ones
    from pathlib import Path
    path = Path(__file__).parent.parent / "analysis" / "deckbuild" / "seeds-tournament-2026-10-07.txt"
    rng = random.Random(4)
    for _, ids in deckbuild.read_seeds(str(path)):
        craft = deckbuild.craft_of_ids(ids)
        assert _legal(deckbuild.legalize(ids, craft, rng), craft)


def test_variant_respects_three_copies():
    rng = random.Random(3)
    craft = Craft.FOREST
    ids = deckbuild.random_ids(craft, rng)
    for _ in range(200):
        ids = deckbuild.variant(ids, craft, rng)
        assert max(Counter(ids).values()) <= decks.MAX_COPIES


def test_the_search_refuses_a_registered_deck():
    import pytest
    from types import SimpleNamespace
    face = [c.card_id for c in decks.build(decks.FACE_DRAGON)]
    search = deckbuild.Search.__new__(deckbuild.Search)
    search.args = SimpleNamespace(agent="mcts:1+plan")
    with pytest.raises(ValueError, match="registered deck"):
        search.play({"x": face}, [(1, face)], "t")
