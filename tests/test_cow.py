"""Deck cards shared between clones, copied on write (core.state.PlayerState.deck): a clone's changes never reach
the original or another clone, and the check mode catches a shared card that changed."""
import pytest

from svsim.cards import demo
from svsim.core import state as ST

from helpers import start


def _with_deck():
    s = start()
    for p in s.players:
        p.deck = [s.new_instance(demo.GIANT, p.index) for _ in range(5)]
    return s


def test_a_clone_shares_deck_cards_until_it_changes_one():
    s = _with_deck()
    t = s.clone()
    assert t.players[0].deck_view()[0] is s.players[0].deck_view()[0]     # shared
    t.players[0].deck[0].atk = 99                                          # `deck`: the clone's own copies first
    assert s.players[0].deck_view()[0].atk == demo.GIANT.atk
    s.players[0].deck[1].cost = 0                                          # the original also copies first
    assert t.players[0].deck_view()[1].cost == demo.GIANT.cost


def test_a_card_drawn_from_a_shared_deck_is_the_drawers_own():
    s = _with_deck()
    t = s.clone()
    top = s.players[0].deck_view()[-1]
    card = t.players[0].draw_top()
    assert card is not top and card.uid == top.uid and len(t.players[0].deck_view()) == 4
    card.atk = 42
    assert top.atk == demo.GIANT.atk and len(s.players[0].deck_view()) == 5


def test_the_check_mode_catches_a_shared_card_changed_in_place(monkeypatch):
    monkeypatch.setattr(ST, "CHECK", True)
    monkeypatch.setattr(ST, "_SHARED", {})
    s = _with_deck()
    t = s.clone()
    t.players[0].deck_view()[0].atk = 7                  # a bug: changed through the read-only view
    with pytest.raises(AssertionError):
        ST.verify_state(s)
    with pytest.raises(AssertionError):
        s.clone()
    with pytest.raises(AssertionError):
        ST.sweep()
