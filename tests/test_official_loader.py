"""Checks against real official data. Skipped unless it has been fetched:

    python -m svsim.tools.fetch_cards --lang en
"""
from pathlib import Path

import pytest

from svsim.cards.official import load_cards, parse_keywords
from svsim.core.enums import CardType, Keyword

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
FILES = sorted(RAW.glob("set_*_en.json"))


def test_keyword_lines_only():
    text = ("<b><color=Keyword>Fanfare</color></b>: Give this follower "
            "<b><color=Keyword>Storm</color></b>.\n<hr><b><color=Keyword>Ward</color></b>"
            "<hr><ev><b><color=Keyword>Evolve</color></b>: Gain <b><color=Keyword>Rush</color></b></ev>")
    assert parse_keywords(text) == Keyword.WARD


@pytest.mark.skipif(not FILES, reason="official card data not fetched")
def test_official_cards_load():
    cards = load_cards(FILES)
    by_name = {c.name: c for c in cards.values()}
    assert by_name["Flashstep Quickblader"].keywords == Keyword.STORM
    assert by_name["Jailor of Antiquity"].keywords == Keyword.WARD
    assert by_name["Dragonewt Promoter"].keywords == Keyword.RUSH
    statue = by_name["Winged Statue"]
    assert statue.type == CardType.COUNTDOWN_AMULET and statue.countdown == 4
    assert by_name["Luminous Commander"].related
