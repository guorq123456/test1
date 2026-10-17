"""Resource-flow lethal planning (search/combo.py) on Rhinoceroach Forest cards."""
from svsim.cards import demo, forest, unlimited as U
from svsim.core.actions import Fuse
from svsim.core.engine import apply
from svsim.core.enums import Keyword
from svsim.search.lethal import find_lethal
from svsim.search.combo import engage_profile, evolve_profile, leave_discount, plan, profile, recovery, solve

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
    assert recovery(U.BABY_CARBUNCLE, True) == 3
    assert recovery(forest.MIROKU, True) == 2                        # replicate: recover 2
    # How damage to enemy followers lands, measured against two enemy followers.
    assert (bug[0].hit, bug[0].spread) == (2, "random")
    (bayle,) = profile(U.BAYLE)
    assert (bayle[0].hit, bayle[0].spread) == (4, "target")
    (arrow,) = profile(U.ERADICATING_ARROW)
    assert (arrow[0].hit, arrow[0].hit_per_combo, arrow[0].spread) == (0, 1, "random")   # Combo times -0/-1
    assert arrow[0].pierce and not bayle[0].pierce and not bug[0].pierce   # -0/-1 isn't damage: Barrier can't stop it
    assert {(e[0].hit, e[0].spread) for e in profile(forest.MIROKU)} >= {(3, "split")}
    (glade,) = [e for e in evolve_profile(U.GLADE, False) if e.hit_per_hand]
    assert (glade.hit, glade.hit_per_hand, glade.spread) == (0, 1, "split")   # X = cards in hand
    assert [e.drawn for e in profile(U.GLADE)[0]] == [2, 2, 2]
    assert [e.drawn for e in profile(U.GARDENS_ALLURE)[0]] == [1, 1, 1]
    assert [e.drawn for e in profile(U.GARDENS_ALLURE, fused=True)[0]] == [2, 2, 2]
    # Storm: the leader at once; Rush (Sprouting Initiate, Fairy): followers only; Miroku: neither.
    reach = [profile(d)[0][0].reach for d in (forest.SPROUTING_INITIATE, U.FAIRY, forest.MIROKU)]
    assert rhino[0].reach == 2 and reach == [1, 1, 0]
    assert leave_discount(U.BAYLE) == 1 and leave_discount(U.KILLER_RHINOCEROACH) == 0


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


def test_clears_ward_before_going_face():
    # A 1/3 Ward: three Rush Fairies take it down, then Rhinoceroach hits for 7.
    # Exhaustive search agrees there's nothing better: 8 is the most this hand deals.
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(8, 10, hand)
    put(state, 1, demo.SHIELDBEARER)
    result = solve(state)
    assert result.sure and result.decided_by == "plan"
    assert sum(1 for step in plan(state).steps if step[0] == "strike") == 3
    state = combo_position(10, 10, hand)
    put(state, 1, demo.SHIELDBEARER)
    result = solve(state)
    assert result.decided_by == "ceiling" and result.ceiling == 8


def test_fuses_a_dead_card_to_make_room_in_a_full_hand():
    # The player's idea: with a full hand, fuse a Glade (天宫) to Garden's Allure so
    # both Fairies from Fairy Convocation fit. Convocation, two Fairies,
    # Rhinoceroach for 4, Bug Alert it back, again for 6: 10 damage with 10 play
    # points. Without the Allure only one Fairy fits and 8 is the most there is
    # (exhaustive search agrees: no lethal on 9).
    base = [U.KILLER_RHINOCEROACH, forest.BUG_ALERT, U.FAIRY_CONVOCATION] + [U.GLADE] * 5
    state = combo_position(10, 10, base + [U.GARDENS_ALLURE])
    result = solve(state)
    assert result.sure and result.decided_by == "plan"
    fuse = next(a for a in result.line if isinstance(a, Fuse))
    assert [state.in_hand(0, uid).defn for uid in fuse.cards] == [U.GLADE]
    without = combo_position(9, 10, base + [demo.GIANT])
    assert plan(without).damage == 8 and not find_lethal(without, max_nodes=50000).sure


def test_falls_back_to_search_when_the_engine_rejects_the_plan():
    # The model doesn't know a leader damage cap: it plans Rhinoceroach for 4 and 6,
    # the engine caps each hit at 3, the plan fails and exact search takes over.
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(7, 10, hand)
    state.players[1].damage_cap = 3
    result = solve(state, search_nodes=5000)
    assert result.decided_by == "search" and not result.sure and result.ceiling >= 7


def test_barrier_takes_one_hit():
    # A 1/3 Ward with Barrier needs four Fairy hits, not three: 6 damage, not 7.
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH]
    state = combo_position(6, 10, hand)
    ward = put(state, 1, demo.SHIELDBEARER)
    ward.keywords |= Keyword.BARRIER
    assert plan(state).damage == 6
    assert sum(1 for step in plan(state).steps if step[0] == "strike") == 4
    assert solve(state).decided_by == "plan"


def test_random_damage_counts_only_with_one_place_to_land():
    # Two Rush Fairies hit the 1/3 Ward for 2, Eradicating Arrow at Combo 3 (three
    # random -0/-1) finishes it, Rhinoceroach comes down at Combo 4: 4 damage.
    # With the Ward the only enemy follower the Arrow can't miss, so the plan is a
    # sure lethal; exact search can't tell, a random effect is a chance node to it.
    hand = [U.FAIRY, U.FAIRY, U.ERADICATING_ARROW, U.KILLER_RHINOCEROACH]
    state = combo_position(4, 6, hand)
    put(state, 1, demo.SHIELDBEARER)
    result = solve(state)
    assert result.sure and result.decided_by == "plan"
    assert not find_lethal(state, max_nodes=20000).sure
    # Next to a 5/5 the Arrow can miss the Ward: the model doesn't count on it.
    put(state, 1, demo.GIANT)
    result = solve(state)
    assert not result.sure and result.decided_by == "ceiling" and result.ceiling == 0


def test_the_players_formula_counts_like_a_player():
    from svsim.search.formula import estimate
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    e = estimate(combo_position(10, 10, hand))
    assert e.damage == 10 and e.pattern == "2 虫（手出 1、回手 1）"
    assert ("先打的垫牌 3 张（其中 0 费 0 张），每张 ×2", 6) in e.terms
    # Two Rhinoceroaches from hand beat one returned to hand by 1 for the same play points.
    two = estimate(combo_position(30, 10, [U.KILLER_RHINOCEROACH, U.KILLER_RHINOCEROACH] + [U.FAIRY] * 4))
    loop = estimate(combo_position(30, 10, [U.KILLER_RHINOCEROACH, forest.BUG_ALERT] + [U.FAIRY] * 4))
    assert (two.damage, loop.damage) == (11, 10)


def test_formula_counts_evolving_the_last_rhinoceroach():
    from svsim.search.formula import estimate
    from helpers import unlock_evolution
    state = combo_position(30, 10, [U.KILLER_RHINOCEROACH, U.KILLER_RHINOCEROACH] + [U.FAIRY] * 4)
    unlock_evolution(state, 0)
    e = estimate(state)
    assert e.damage == 14 and ("超进化最后一只破魔虫", 3) in e.terms


def test_solve_reports_the_quick_count():
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    result = solve(combo_position(10, 10, hand))
    assert result.estimate.damage == 10 and "打得死" in result.estimate.text(10)


def test_lethal_agent_with_the_planner_plays_the_combo_turn():
    from svsim.agents.lethal_agent import LethalAgent
    from svsim.core.actions import EndTurn
    from svsim.core.engine import legal_actions

    class Passer:
        def act(self, state, actions):
            return EndTurn()

    base = [U.KILLER_RHINOCEROACH, forest.BUG_ALERT, U.FAIRY_CONVOCATION] + [U.GLADE] * 5
    state = combo_position(10, 10, base + [U.GARDENS_ALLURE])
    agent = LethalAgent(Passer(), max_nodes=500, planner=True)
    played = []
    while not state.over and state.active == 0:
        action = agent.act(state, legal_actions(state))
        played.append(action)
        apply(state, action)
    assert state.winner == 0 and agent.lethals == agent.planned == 1
    assert any(isinstance(a, Fuse) for a in played)
    # Without the planner the exact search (500 nodes) doesn't find this turn.
    state = combo_position(10, 10, base + [U.GARDENS_ALLURE])
    plain = LethalAgent(Passer(), max_nodes=500)
    assert plain.act(state, legal_actions(state)) == EndTurn() and plain.lethals == 0


def test_formula_counts_the_ward_first():
    from svsim.search.formula import estimate
    # The three Ward positions above, whose true maximum exact search confirmed.
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(8, 10, hand)
    put(state, 1, demo.SHIELDBEARER)
    e = estimate(state)
    assert e.damage == 8 and e.pattern.endswith("对手有守护，先拆")
    assert e.terms[0][0].startswith("拆守护（3 血）") and "妖精（回手再打）" in e.terms[0][0]
    state = combo_position(4, 6, [U.FAIRY, U.FAIRY, U.ERADICATING_ARROW, U.KILLER_RHINOCEROACH])
    put(state, 1, demo.SHIELDBEARER)
    e = estimate(state)
    assert e.damage == 4 and "驱逐的死矢 3" in e.terms[0][0]      # played last: Combo 3, three hits
    put(state, 1, demo.GIANT)                                    # now the Arrow can miss
    assert estimate(state).damage == 0
    state = combo_position(6, 10, [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH])
    ward = put(state, 1, demo.SHIELDBEARER)
    ward.keywords |= Keyword.BARRIER
    e = estimate(state)
    assert e.damage == 6 and e.terms[0][0].startswith("拆守护（4 血）")   # Barrier: one more hit


def test_formula_picks_filler_exactly():
    from svsim.search.formula import estimate
    # 4 play points after the Rhinoceroach: Convocation + one Fairy + Lambent Cairn + its
    # free Deepwood Bounty is 4 cards; Convocation + both Fairies would be 3.
    hand = [U.KILLER_RHINOCEROACH, U.FAIRY_CONVOCATION, U.LAMBENT_CAIRN]
    e = estimate(combo_position(30, 7, hand))
    assert ("先打的垫牌 4 张（其中 0 费 1 张），每张 ×1", 4) in e.terms
    assert e.damage == 1 + 4 + 1                                 # Combo 5, Cairn engaged for +1
    assert plan(combo_position(30, 7, hand)).damage == 6


def test_next_turn_potential_counts_what_the_hand_can_do():
    from svsim.search.combo import next_turn_damage, next_turn_position
    from svsim.search.evaluate import DEFAULT, THREAT, evaluate
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(10, 9, hand)
    state.players[0].max_pp = 9
    pp, cap, combo = next_turn_position(state, 0)[:3]
    assert (pp, cap, combo) == (10, 10, 0)                   # one more play point, Combo from 0
    assert next_turn_damage(state, 0) == 10                  # the 10-damage loop needs all 10
    # The evaluation can value it: 0.5 per point up to the defense, and 6 for lethal.
    assert abs(evaluate(state, 0, THREAT) - evaluate(state, 0, DEFAULT) - (0.5 * 10 + 6.0)) < 1e-9
    # A follower already on the field counts, unless only the hand is asked for.
    put(state, 0, demo.GIANT).entered_turn = -1
    assert next_turn_damage(state, 0) > next_turn_damage(state, 0, board=False) == 10


def test_macro_agent_returns_legal_moves():
    from svsim.agents.lethal_agent import LethalAgent
    from svsim.agents.mcts_agent import MCTSAgent
    from svsim.core.engine import legal_actions
    from svsim.search.combo import _legal
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(30, 10, hand)                     # no lethal: 30 defense
    agent = LethalAgent(MCTSAgent(20, seed=1), max_nodes=300, planner=True, macro=True)
    for _ in range(12):
        if state.over or state.active != 0:
            break
        action = agent.act(state, legal_actions(state))
        assert _legal(state, action)
        apply(state, action)
    assert agent.lethals == 0


def test_potential_with_all_ten_play_points_shows_what_the_hand_builds_towards():
    from svsim.search.combo import next_turn_damage
    hand = [U.FAIRY_CONVOCATION, U.FAIRY, U.FAIRY, U.KILLER_RHINOCEROACH, forest.BUG_ALERT]
    state = combo_position(30, 3, hand)
    state.players[0].max_pp = 3                              # next turn: 4 play points
    assert next_turn_damage(state, 0, board=False) < next_turn_damage(state, 0, board=False, pp=10) == 10
