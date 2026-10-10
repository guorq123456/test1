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


def _crossroads():
    """Our turn: a ready Lancer, two Footmen in hand and 2 play points; the enemy at 12 with two small followers."""
    from svsim.cards import demo as D
    s = start()
    s.turn, s.players[0].turns_taken = 7, 4
    put(s, 0, D.LANCER)
    put(s, 1, D.FOOTMAN)
    put(s, 1, D.ASSASSIN)
    give(s, 0, D.FOOTMAN)
    give(s, 0, D.FOOTMAN)
    set_pp(s, 0, 2)
    s.players[1].leader_hp = 12
    return s


def test_each_direction_plays_its_own_way():
    from svsim.search.candidates import play_turn
    from svsim.search.foresight import DIRECTIONS, direction_agent
    ends = {}
    for d in DIRECTIONS:
        agent = direction_agent(d, "greedy", 3, nodes=200)
        _, ends[d] = play_turn(_crossroads(), lambda st, legal: agent.act(st, legal))
    stats = {d: sum(f.atk + f.life for f in e.players[1].followers) for d, e in ends.items()}
    assert ends["race"].players[1].leader_hp < 12                        # race hits the leader
    assert stats["clear"] < stats["race"]                                 # clear leaves their board weaker
    me_c, me_d = ends["conserve"].players[0], ends["default"].players[0]
    assert len(me_c.hand) > len(me_d.hand) and me_c.pp > me_d.pp          # conserve keeps cards and play points


def test_rollouts_repeat_for_a_seed_and_a_won_position_is_won():
    from svsim.search.foresight import direction_rollout
    s = _crossroads()
    _ended(s)
    a = direction_rollout(s, ["race", "default"], k=2, seed=3, opp_spec="greedy", our_spec="greedy", nodes=60)
    b = direction_rollout(s, ["race", "default"], k=2, seed=3, opp_spec="greedy", our_spec="greedy", nodes=60)
    assert {d: (r["samples"], r["turns"]) for d, r in a.items()} == {d: (r["samples"], r["turns"]) for d, r in b.items()}
    assert all(0.0 <= r["win"] <= 1.0 and r["turns"] > 0 for r in a.values())
    s = _crossroads()
    s.players[1].deck = []                   # they lose at their own draw
    won = direction_rollout(after_end_of_turn(s), "all", k=2, seed=1, opp_spec="greedy", our_spec="greedy",
                            opponent_started=False, nodes=60)
    assert all(r["win"] == 1.0 and r["samples"] == [1.0, 1.0] for r in won.values())
