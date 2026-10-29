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


def test_confirm_takes_a_clear_gain_at_the_cap(tmp_path):
    """A gain near H1 can leave the sequential test undecided at the cap: the fixed-sample test then takes it
    when it is clearly above 0, and leaves a gain within the noise undecided."""
    import argparse
    args = argparse.Namespace(out=str(tmp_path), seed=1, confirm=560, batch=70, h1=0.02, at_max=2.0,
                              min_nonzero=20)

    def run(pattern):
        s = deckbuild.Search(args)
        s.deals = lambda n, field: list(range(n))
        s.play = lambda decks, deals, tag: {"incumbent": [0.0] * len(deals),
                                            "v": [pattern[i % len(pattern)] for i in range(len(deals))]}
        return s.confirm([], [], "v", {}, "t")

    # 70 deals: 7 won, 6 lost by the variant, the rest even: mean +1/70, se about 0.4/sqrt(n)
    verdict, diff = run([1.0] * 7 + [-1.0] * 6 + [0.0] * 57)
    assert len(diff) == 560 and verdict == "undecided"
    verdict, diff = run([1.0] * 9 + [-1.0] * 6 + [0.0] * 55)    # mean +3/70 over 560: z about 2.9
    assert verdict.startswith("accepted")


def test_a_class_is_searched_against_the_other_classes(tmp_path):
    """The own class's incumbent is not an opponent: in the field its mirror is even whichever deck holds it."""
    import argparse
    args = argparse.Namespace(out=str(tmp_path), seed=1, variants=2)
    s = deckbuild.Search(args)
    rng = random.Random(3)
    s.st["field"] = {c.name: deckbuild.random_ids(c, rng) for c in deckbuild.CLASSES}
    seen = []

    def halving(cands, incumbent, field, tag, first=None):
        seen.append(set(field))
        return "v0", {"v0": [0.0], "incumbent": [1.0]}            # the incumbent stays: no confirmation
    s.halving = halving
    s.step("DRAGON")
    assert seen == [{c.name for c in deckbuild.CLASSES} - {"DRAGON"}]


def test_random_decks_can_start_from_the_new_set():
    rng = random.Random(4)
    for craft in deckbuild.CLASSES:
        prefer = [c for c in deckbuild.legal_cards(craft) if str(c.card_set) == "10010"]
        ids = deckbuild.random_ids(craft, rng, None, prefer, 0.6)
        assert _legal(ids, craft)
        assert sum(str(POOL[i].card_set) == "10010" for i in ids) >= 24
