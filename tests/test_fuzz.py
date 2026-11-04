"""Random self-play: no crashes, invariants hold, and games replay deterministically."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks
from svsim.cards.demo import demo_deck
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.state import FIELD_LIMIT, HAND_LIMIT, LEADER_AREA_LIMIT, MAX_PP
from svsim.core.view import determinize


def check_invariants(state, action):
    assert not state.queue
    for p in state.players:
        assert len(p.field) <= FIELD_LIMIT and len(p.hand) <= HAND_LIMIT
        assert len(p.leader_area) <= LEADER_AREA_LIMIT
        assert p.leader_hp <= p.leader_max_hp
        assert 0 <= p.max_pp <= MAX_PP and 0 <= p.pp <= p.max_pp + 1
        assert p.ep >= 0 and p.sep >= 0
        assert all(c.life > 0 for c in p.followers), action
        assert len(p.deck) + len(p.hand) + len(p.field) <= 80


def agents(seed):
    return [RandomAgent(seed, end_turn_weight=0.2), RandomAgent(seed + 1, end_turn_weight=0.2)]


def test_random_games_hold_invariants():
    deck = demo_deck()
    for g in range(200):
        state = new_game(deck, deck, seed=g)
        winner = play_game(state, agents(g), on_action=check_invariants)
        assert winner in (0, 1, -1)


def test_starter_decks_random_games():
    pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
    for g in range(150):
        d0, d1 = (pirate, ramp) if g % 2 == 0 else (ramp, pirate)
        state = new_game(d0, d1, seed=1000 + g)
        assert play_game(state, agents(g), on_action=check_invariants) in (0, 1, -1)


def test_starter_decks_replay_deterministically():
    pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
    logs = []
    for _ in range(2):
        log = []
        state = new_game(pirate, ramp, seed=99)
        play_game(state, agents(5), on_action=lambda s, a: log.append(a))
        logs.append((log, state.winner, repr(state.players)))
    assert logs[0] == logs[1]


def test_same_seed_same_game():
    deck = demo_deck()
    logs = []
    for _ in range(2):
        log = []
        state = new_game(deck, deck, seed=42)
        play_game(state, agents(7), on_action=lambda s, a: log.append(a))
        logs.append((log, state.winner))
    assert logs[0] == logs[1]


def test_clone_branches_independently():
    deck = demo_deck()
    state = new_game(deck, deck, seed=3)
    rng = random.Random(0)
    for _ in range(40):
        apply(state, rng.choice(legal_actions(state)))
    copy = state.clone()
    snapshot = repr(state.players)
    play_game(copy, agents(11))
    assert repr(state.players) == snapshot           # original untouched
    again = state.clone()
    play_game(again, agents(11))
    assert again.winner == copy.winner and again.turn == copy.turn


def test_determinize_keeps_known_information():
    deck = demo_deck()
    state = new_game(deck, deck, seed=5)
    rng = random.Random(0)
    for _ in range(30):
        apply(state, rng.choice(legal_actions(state)))
    sample = determinize(state, 0, random.Random(1))
    me, opp = state.players
    s_me, s_opp = sample.players
    assert [c.uid for c in s_me.hand] == [c.uid for c in me.hand]
    assert [c.uid for c in s_me.field] == [c.uid for c in me.field]
    assert len(s_opp.hand) == len(opp.hand) and len(s_opp.deck) == len(opp.deck)
    assert sorted(c.uid for c in s_opp.hand + s_opp.deck) == sorted(c.uid for c in opp.hand + opp.deck)
