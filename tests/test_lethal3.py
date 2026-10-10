"""+lethal3 (opt-in, not in any level): the lethal package, +lethal2 (the planner's countdown amulets, near-lethal
2000 within 4, 3000 unscreened) with +plannerfix and +eot, behind one flag. The puzzle bank, an end-of-turn lethal
played by the agent, and Ramp's missed lethals replayed when step 1's data is at hand ($SVSIM_STEP1_DIR)."""
import json
import os
import sys
from pathlib import Path

import pytest

from svsim.tools.puzzles import facts, judge, play, puzzles

BANK = {name: (build, answer) for name, build, answer in puzzles()}
MISSES = Path(__file__).resolve().parents[1] / "analysis" / "speed" / "data" / "ramp_misses.jsonl"


def test_the_flag_sets_the_whole_package_and_its_own_screen():
    from svsim.tools.arena import make_agent
    a = make_agent("level-strong+lethal3", 0)
    assert a.tickers and a.plannerfix and a.eot and a.planner
    assert a.search.max_nodes == 3000 and a.search.near == (2000, 4) and a.search.screen == 200
    b = make_agent("level-strong", 0)
    assert not (b.tickers or b.plannerfix or b.eot) and b.search.max_nodes == 2000
    with pytest.raises(ValueError):
        make_agent("level-strong+lethal3+screen=1000", 0)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_puzzle_bank_lethal_is_solved_and_the_setup_still_has_none(seed):
    build, answer = BANK["pirate-flags-lethal"]
    end, me, _ = play(build, "level-strong+lethal3", seed)
    assert judge(answer, facts(end, me)) is True
    build, _ = BANK["pirate-flags-setup"]
    end, me, _ = play(build, "level-strong+lethal3", seed)
    assert end.winner != me                                  # no lethal exists there: none is claimed or played


def test_the_agent_wins_by_an_allied_followers_end_of_turn_damage():
    from svsim.cards import dragon
    from svsim.cards.pool import POOL
    from svsim.core import effects as E
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    from helpers import put, set_pp, start
    s = start()
    s.turn, s.players[0].turns_taken = 13, 7
    e = put(s, 0, POOL[dragon.ERNTZ.card_id])
    E.evolve(s, e)
    e.attacks_made = e.max_attacks                           # it has attacked: only its end of turn can win
    set_pp(s, 0, 0)
    s.players[1].leader_hp = 8
    plain = make_agent("level-strong", 0)
    plain.act(s.clone(), legal_actions(s))
    assert plain.planned == 0                                # the plain planner doesn't see it
    agent = make_agent("level-strong+lethal3", 0)
    a = agent.act(s, legal_actions(s))
    assert isinstance(a, EndTurn) and agent.lethals == 1 and agent.planned == 1
    apply(s, a)
    assert s.winner == 0


# The 20 Ramp starts +lethal2 still missed (analysis/speed/LETHAL.md): the lethal check of +lethal3 finds these, and
# the plain one (level-strong's) finds none of the 20 (analysis/speed/lethal3_eval.py, the same check).
FOUND = {60, 132, 151, 246, 329, 347, 361, 397, 400, 449, 451, 533, 806, 985}   # 9 planner measurement + 5 end of
# turn; the six left: discard-cost spells (181, 482, 658) and other planner gaps (109, 127, 546)


def _check(state, spec):
    from svsim.search import combo
    from svsim.search.lethal import LethalSearch
    kw = dict(tickers=True, fix=True, eot=True) if spec == "lethal3" else {}
    if combo.planned_lethal(state, 20000, **kw)[0]:
        return True
    nodes, near = ((3000, (2000, 4)) if spec == "lethal3" else (2000, (1000, 4)))
    return LethalSearch(max_nodes=nodes, screen=200, near=near, seed=0).solve(state.clone()).sure


@pytest.mark.skipif(not os.environ.get("SVSIM_STEP1_DIR"), reason="step 1's data not at hand")
def test_ramps_missed_lethals_replayed():
    d = os.environ["SVSIM_STEP1_DIR"]
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    rows = [json.loads(x) for x in open(MISSES)]
    assert len(rows) == 20
    found = set()
    for r in rows:
        state = SD._state_at(games[r["game"]], r["at"])
        assert not _check(state, "plain"), r["game"]
        if _check(state, "lethal3"):
            found.add(r["game"])
    assert found == FOUND


def _g14():
    """Pirate-t g14's turn 19 (lethal3_eval.py), rebuilt: 10/10 play points, two super-evolution points, three
    flags at countdowns 5, 5, 6; the enemy at 10 with a super-evolved Golden Knight 9/9. The ticker search plans 10
    through the flags that the engine can't play (Roughwater First Mate dies striking the Knight, and Severed Ties
    then has no ally to take); the plain plan, Beltezore, deals 12 and checks."""
    from svsim.cards import decks, sword
    from svsim.core import effects as E
    from svsim.core.actions import Mulligan
    from svsim.core.engine import apply, new_game
    from helpers import give, put, set_pp
    st = new_game(list(decks.build(decks.PIRATE_T)), list(decks.build(decks.PIRATE_T)), seed=1, first=0)
    apply(st, Mulligan(()))
    apply(st, Mulligan(()))
    me, op = st.players
    for p in st.players:
        p.hand.clear()
        p.field.clear()
    st.turn = 19
    me.turns_taken, op.turns_taken = 10, 9
    set_pp(st, 0, 10)
    me.leader_hp, op.leader_hp = 16, 10
    me.ep, me.sep = 0, 2
    for cd in (5, 5, 6):
        put(st, 0, sword.DREAD_PIRATES_FLAG).countdown = cd
    E.evolve(st, put(st, 1, sword.GOLDEN_KNIGHT), super_=True, notify=False)
    give(st, 0, sword.SEVERED_TIES)
    give(st, 0, sword.BELTEZORE)
    E.set_cost(give(st, 0, sword.SEVERED_TIES), 1)
    give(st, 0, sword.DEPTHS_OF_THE_ELD_SWORD)
    give(st, 0, sword.ROUGHWATER_FIRST_MATE)
    give(st, 0, sword.SPLENDOR_OF_THE_GOLDBLOOM)
    return st


def test_a_ticker_plan_the_engine_cant_play_falls_back_to_the_plain_plan():
    from svsim.search import combo
    st = _g14()
    p = combo.plan(st, 20000, tickers=True)
    assert p.tickers and p.damage >= 10
    line = combo.realize(st, p.steps, face_first=True)
    assert not (line and combo.verify(st, line))             # the countdown model is wrong here
    line, first = combo.planned_lethal(st, 20000, tickers=True, fix=True, eot=True)
    assert first.tickers and line and combo.verify(st, line)
    assert combo.planned_lethal(st, 20000)[0] == combo.planned_lethal(st, 20000, tickers=True)[0]
