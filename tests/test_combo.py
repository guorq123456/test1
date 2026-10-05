"""Resource-flow lethal planning (search/combo.py) on Rhinoceroach Forest cards."""
from svsim.cards import demo, forest, unlimited as U
from svsim.core.engine import apply
from svsim.search.combo import engage_profile, evolve_profile, plan, profile, solve

from helpers import give, put, set_pp, start


def test_profiles_are_measured_not_written():
    (rhino,) = profile(U.KILLER_RHINOCEROACH)
    assert all((e.per_combo, e.attacks, e.paid) == (1, 1, 3) for e in rhino)
    (bug,) = profile(forest.BUG_ALERT)
    assert bug[0].bounce and bug[0].paid == 1
    (cairn,) = profile(U.LAMBENT_CAIRN)
    assert [len(e.added) for e in cairn] == [1, 2, 2]      # Combo (3): a Deepwood Bounty too
    assert engage_profile(U.GODWOOD_STAFF).bounce and engage_profile(U.GODWOOD_STAFF).gone
    assert engage_profile(U.LAMBENT_CAIRN).buff == 1
    assert evolve_profile(U.BABY_CARBUNCLE, True).recovered == 3
    assert evolve_profile(forest.MIROKU, True).recovered == 2        # replicate: recover 2


def combo_position(hp: int, pp: int, hand):
    state = start(first=0)
    for p in state.players:
        p.hand.clear()
    state.players[1].leader_hp = hp
    set_pp(state, 0, pp)
    for defn in hand:
        give(state, 0, defn)
    return state


def test_plans_the_rhinoceroach_loop_and_the_engine_confirms_it():
    # 10 play points: three 1-cost cards, Rhinoceroach for 4, Bug Alert it back, again for 6.
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(10, 10, hand)
    p = plan(state)
    assert p.damage >= 10
    result = solve(state)
    assert result.sure and result.decided_by == "plan"
    s = state.clone()
    for action in result.line:
        apply(s, action)
    assert s.winner == 0


def test_resource_ceiling_rules_out_hopeless_turns_quickly():
    hand = [U.FAIRY_CONVOCATION, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(20, 10, hand)
    result = solve(state)
    assert not result.sure and result.decided_by == "ceiling" and result.ceiling < 20
    assert result.seconds < 5


def test_the_model_respects_the_hand_limit():
    # A full hand of 9 and 6 play points (not enough to play a Giant first and make
    # room): Fairy Convocation leaves room for only one of its two Fairies, so
    # Rhinoceroach comes down at Combo 3 (3 damage), not 4. With 10 play points the
    # planner does play a Giant first, then gets both Fairies: 4 damage.
    hand = [U.FAIRY_CONVOCATION, U.KILLER_RHINOCEROACH] + [demo.GIANT] * 7
    assert plan(combo_position(4, 6, hand)).damage == 3
    assert plan(combo_position(4, 10, hand)).damage == 4


def test_falls_back_to_search_when_the_plan_meets_ward():
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(10, 10, hand)
    put(state, 1, demo.SHIELDBEARER)                        # Ward: the planned line can't hit the leader
    result = solve(state, search_nodes=3000)
    assert result.decided_by == "search"
