"""search.foresight: the chance of a sure lethal at the start of our next turn, after the opponent's reply."""
from svsim.cards import demo
from svsim.core.actions import EndTurn
from svsim.core.engine import apply
from svsim.search.evaluate import after_end_of_turn
from svsim.search.foresight import next_lethal_prob

from helpers import give, put, set_pp, start


def _ended(state):
    apply(state, EndTurn())                 # the engine ends our turn and starts the opponent's
    return state


def test_a_lethal_nothing_can_stop_counts_one_on_every_sample():
    s = start()                              # Footmen only: the opponent can't heal or stop a spell to the face
    give(s, 0, demo.BACKFIRE)                # 3 damage to both leaders
    s.players[1].leader_hp = 3
    set_pp(s, 0, 3)
    r = next_lethal_prob(_ended(s), k=4, seed=1, reply_spec="level-strong")
    assert r["p"] == 1.0 and r["samples"] == [1.0] * 4 and r["ends"] == ["lethal"] * 4
    assert r["incomplete"] == 0 and r["ms"] > 0


def test_no_reach_counts_zero_and_dying_in_their_turn_counts_zero():
    s = start()
    r = next_lethal_prob(_ended(s), k=3, seed=2, reply_spec="greedy")
    assert r["p"] == 0.0 and r["ends"] == ["no lethal"] * 3
    s = start()
    s.players[0].leader_hp = 1
    put(s, 1, demo.RAIDER)                   # ready on their side: it hits our leader in their turn
    r = next_lethal_prob(_ended(s), k=3, seed=2, reply_spec="greedy")
    assert r["p"] == 0.0 and r["ends"] == ["died"] * 3


def test_a_turn_end_before_the_opponents_turn_starts_works_too():
    s = start()
    give(s, 0, demo.BACKFIRE)
    s.players[1].leader_hp = 3
    set_pp(s, 0, 3)
    end = after_end_of_turn(s)               # a candidate plan's turn end: their turn not started yet
    r = next_lethal_prob(end, k=3, seed=1, reply_spec="greedy", opponent_started=False)
    assert r["samples"] == [1.0] * 3
    s.players[1].deck = []                   # ... and they lose at their own draw
    end = after_end_of_turn(s)
    r = next_lethal_prob(end, k=2, seed=1, reply_spec="greedy", opponent_started=False)
    assert r["ends"] == ["won"] * 2


def test_the_same_seed_gives_the_same_samples():
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    s = start(deck=demo.demo_deck())
    agents = [make_agent("greedy", 0), make_agent("greedy", 1)]
    while s.turn < 9 and not s.over:          # a few turns of a real game, then our turn ends
        apply(s, agents[s.active].act(s, legal_actions(s)))
    assert not s.over
    while s.active != 0:
        apply(s, agents[s.active].act(s, legal_actions(s)))
    _ended(s)
    a = next_lethal_prob(s, k=4, seed=7, reply_spec="greedy")
    b = next_lethal_prob(s, k=4, seed=7, reply_spec="greedy")
    assert a["samples"] == b["samples"] and a["ends"] == b["ends"]
