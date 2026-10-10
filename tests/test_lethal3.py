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
    hp = state.players[1 - state.active].leader_hp
    p = combo.plan(state, 20000, **kw)
    if p.damage >= hp and p.steps:
        line = combo.realize(state, p.steps, face_first=p.face_first)
        if line and combo.verify(state, line):
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
