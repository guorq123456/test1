"""State copying: clones share nothing mutable with the original."""
from dataclasses import fields

from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.state import CardInstance, PlayerState
from svsim.core.script import CardScript

from helpers import put, start


def test_card_copy_copies_every_field():
    state = start()
    card = put(state, 0, demo.GIANT)
    E.buff(state, card, 1, 1, until_turn=state.turn)
    E.add_cost(card, -1)
    E.counters(card)["seen"] = [1, 2]
    E.grant(card, CardScript())
    card.silenced = card.no_last_words = True
    clone = card.copy()
    for f in fields(CardInstance):
        assert getattr(clone, f.name) == getattr(card, f.name), f.name
    for name in ("counters", "grants", "cost_mods"):
        assert getattr(clone, name) is not getattr(card, name), name
    assert clone.counters["seen"] is not card.counters["seen"]


def test_player_copy_copies_every_zone():
    state = start()
    put(state, 0, demo.GIANT)
    p = state.players[0]
    clone = p.copy()
    for f in fields(PlayerState):
        value = getattr(p, f.name)
        assert getattr(clone, f.name) == value, f.name
        if isinstance(value, (list, set, dict)):
            assert getattr(clone, f.name) is not value, f.name


def test_clone_is_independent():
    state = start()
    giant = put(state, 0, demo.GIANT)
    twin = state.clone()
    twin.players[0].field[0].atk = 99
    twin.players[0].hand.clear()
    assert giant.atk == 5 and state.players[0].hand
