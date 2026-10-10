"""Hard-coded card stats against the official database. Skipped unless it has been fetched:

    python -m svsim.tools.fetch_cards --lang en

Run after every balance patch: a buff or nerf shows up here as a mismatch.
"""
from pathlib import Path

import pytest

from svsim.cards import decks
from svsim.cards.official import load_cards

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
FILES = sorted(RAW.glob("set_*_en.json"))
FIELDS = ("name", "craft", "type", "cost", "atk", "life", "keywords", "countdown", "is_token")

pytestmark = pytest.mark.skipif(not FILES, reason="official card data not fetched")


@pytest.fixture(scope="module")
def official():
    return load_cards(FILES)


def test_hardcoded_stats_match_official_data(official):
    for card_id, mine in decks.KNOWN.items():
        theirs = official[card_id]
        for field in FIELDS:
            assert getattr(mine, field) == getattr(theirs, field), (mine.name, field)
        assert (mine.faith and mine.faith.card_id) == (theirs.faith and theirs.faith.card_id)
        assert (mine.accelerate and mine.accelerate.cost) == \
            (theirs.accelerate and theirs.accelerate.cost)


def test_every_starter_card_with_abilities_has_a_script(official):
    for counts in (decks.PIRATE_SWORD, decks.RAMP_DRAGON):
        deck = [official[c.card_id] for c in decks.build(counts)]
        tokens = {official[t] for c in deck for t in c.related if t in official}
        assert decks.unimplemented(deck + list(tokens)) == []
