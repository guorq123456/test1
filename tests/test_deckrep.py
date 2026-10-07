from svsim.cards import decks, library  # noqa: F401
from svsim.learn.deckrep import CARD_NAMES, card_vector, deck_names, deck_static


def test_shapes_and_no_identity():
    ramp = decks.build(decks.RAMP_DRAGON)
    pirate = decks.build(decks.PIRATE_SWORD)
    assert len(card_vector(ramp[0])) == len(CARD_NAMES)
    a, b = deck_static(ramp), deck_static(pirate)
    assert len(a) == len(deck_names()) == len(b)
    assert abs(a - b).sum() > 0
    # the same 40 cards in another order are the same deck
    assert (deck_static(list(reversed(ramp))) == a).all()
