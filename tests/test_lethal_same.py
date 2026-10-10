"""The lethal search, made faster, returns exactly what it returned before (tests/lethal_reference.py, cefd7c1):
the probability, the line, whether it is sure, the nodes searched, completeness and screening, on every decision of
the golden games (tests/golden_search.py) with the lethal agent's settings, and on step 1's turn starts when their
data is at hand ($SVSIM_STEP1_DIR: RC 6f11111's analysis/turn-level/step1 with the analysis line's readers in ana/)."""
import os
import sys

import pytest

import lethal_reference as REF
from golden_search import GAMES

SETTINGS = [dict(max_nodes=2000, screen=200, near=(1000, 4)), dict(max_nodes=400, screen=None),
            dict(max_nodes=300, sure_only=True)]


def _same(state, seed):
    from svsim.search.lethal import LethalSearch
    for kw in SETTINGS:
        a = REF.LethalSearch(seed=seed, **kw).solve(state.clone())
        b = LethalSearch(seed=seed, **kw).solve(state.clone())
        got = (b.probability, repr(b.line), b.sure, b.nodes, b.complete, b.screened)
        want = (a.probability, repr(a.line), a.sure, a.nodes, a.complete, a.screened)
        assert got == want, kw


def _golden_states(deck, opponent, seed, limit):
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    from golden_search import SPEC
    agents = [make_agent(SPEC, 2 * seed), make_agent(SPEC, 2 * seed + 1)]
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
    n = 0
    while not state.over and n < limit:
        if state.phase == Phase.MAIN:
            yield state
        action = agents[state.active].act(state, legal_actions(state))
        apply(state, action)
        n += 1


@pytest.mark.parametrize("deck,opponent,seed,limit", GAMES)
def test_the_lethal_search_is_unchanged_on_the_golden_games(deck, opponent, seed, limit):
    for k, state in enumerate(_golden_states(deck, opponent, seed, limit)):
        _same(state, k)


@pytest.mark.skipif(not os.environ.get("SVSIM_STEP1_DIR"), reason="step 1's data not at hand")
def test_the_lethal_search_is_unchanged_on_step_1s_turn_starts():
    d = os.environ["SVSIM_STEP1_DIR"]
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.core.engine import legal_actions
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = list(SD._lines(f"{d}/starts.jsonl"))[:120]
    n = 0
    for k, r in enumerate(starts):
        state = SD._state_at(games[r["game"]], r["at"])
        if len(legal_actions(state)) > 1:
            _same(state, k)
            n += 1
    assert n == 116
