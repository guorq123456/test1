from svsim.cards import deckcode, decks, dragon, sword
from svsim.core.enums import Craft

# Highlander Portal (Game8, 2026-09-30), as decoded by the official deck API.
HIGHLANDER_PORTAL = (
    "1.7.cQnG.cR2I.dhqc.di4E.dygu.dyjs.dyzU.dzA8.e4Gg.e4IE.eKuk.eL8M.eLN-.ejG6.ejVk.ejYs"
    ".ejlM.ej--.erJk.f5jk.f5wE.f6PU.fC_W.fDkO.fUaM.fUp-.fUq8.fbPs.fbS-.fbwg.fc8k.fsVc"
    ".fslE.fsoM.fs-s.ft1-.ftEU.ftEU.ftEU.ftEe")


def test_starter_decks_are_legal():
    for counts in (decks.PIRATE_SWORD, decks.RAMP_DRAGON):
        assert decks.validate(decks.build(counts)) == []


def test_validate_catches_problems():
    deck = decks.build(decks.PIRATE_SWORD)            # last card is the single Beltezore
    assert decks.validate(deck + [sword.BELTEZORE])   # 41 cards
    assert any("4 copies" in p for p in decks.validate(deck[:-1] + [sword.FLASHSTEP_QUICKBLADER]))
    assert any("token" in p for p in decks.validate(deck[:-1] + [sword.GLITTERING_GOLD]))
    assert any("not Sword" in p
               for p in decks.validate(deck[:-1] + [dragon.ZOOEY], Craft.SWORD))


def test_card_tokens():
    assert deckcode.encode_card(10161210) == "cmmw"
    assert deckcode.decode_card("cmmw") == 10161210


def test_deck_hash_round_trip():
    for counts in (decks.PIRATE_SWORD, decks.RAMP_DRAGON):
        deck = decks.build(counts)
        assert decks.from_hash(decks.to_hash(deck)) == deck


def test_decode_published_hash():
    battle_format, craft, ids = deckcode.decode_deck(HIGHLANDER_PORTAL)
    assert (battle_format, craft, len(ids), len(set(ids))) == (1, 7, 40, 38)
    assert all(str(i)[0] == "1" and str(i)[3] in "07" for i in ids)   # collectible Portal / Neutral
