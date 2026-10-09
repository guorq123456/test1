"""Candidate whole-turn plans (search.candidates): the kinds, their rules, the merging, the summary."""
import pytest

from test_handvalue import _positions

SPEC = "mcts:20+plan+learned+phased"


def _start():
    positions, records = _positions()
    return next((s, p) for s, p in positions[8:] if len(s.players[p].hand) >= 2), records


def _replay(state, actions):
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    s = state.clone()
    for a in actions:
        if isinstance(a, EndTurn):
            return after_end_of_turn(s)
        apply(s, a)
    return s


def test_each_plan_is_a_whole_turn_that_replays_to_its_turn_end_and_ends_are_distinct():
    from svsim.core.actions import EndTurn
    from svsim.search.lethal import state_key
    (state, player), _ = _start()
    cands = __import__("svsim.search.candidates", fromlist=["generate"]).generate(state, spec=SPEC, race_nodes=60)
    kinds = [c.kind for c in cands] + [k for c in cands for k in c.merged]
    assert "bot" in kinds and "end" in kinds and "race" in kinds
    assert len({c.key for c in cands}) == len(cands)                  # merged: no two plans end alike
    for c in cands:
        assert isinstance(c.actions[-1], EndTurn) or c.end.over
        assert state_key(_replay(state, c.actions)) == c.key
        assert set(c.times) == {c.kind, *c.merged}
    end = next(c for c in cands if "end" in [c.kind, *c.merged])
    assert end.kind != "end" or end.actions == [EndTurn()]


def test_the_resource_plans_keep_what_they_say():
    from svsim.core.actions import Evolve, PlayCard, UseBonusPP
    from svsim.core.engine import apply
    from svsim.core.actions import EndTurn
    from svsim.search.candidates import generate
    (state, player), _ = _start()
    cands = generate(state, spec=SPEC, kinds=("bot", "resource"), max_keeps=3)
    every = [(k, c) for c in cands for k in [c.kind, *c.merged]]
    assert any(k.startswith("keep:") or k in ("save", "noevo") for k, _ in every)
    for kind, c in every:
        s = state.clone()
        for a in c.actions:
            if isinstance(a, EndTurn):
                break
            if kind == "noevo":
                assert not isinstance(a, Evolve)
            if kind == "save":
                assert not isinstance(a, UseBonusPP)
            if kind.startswith("keep:") and isinstance(a, PlayCard):
                card = s.in_hand(s.active, a.uid)
                assert card is None or card.defn.card_id != int(kind.split(":")[1])
            apply(s, a)


def test_salem_s_turn_is_played_as_given_and_the_alternatives_are_other_first_moves():
    from svsim.search.candidates import generate, root_alternatives
    from svsim.search.mcts import action_key
    (state, player), _ = _start()
    bot = generate(state, spec=SPEC, kinds=("bot",))[0]
    both = generate(state, spec=SPEC, kinds=("bot", "salem"), salem=list(bot.actions))
    assert len(both) == 1 and both[0].merged == ["salem"]                # the same turn: merged into "bot"
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    alts = root_alternatives(state, SPEC, 0, 2)
    search = _search(make_agent(SPEC, 0))
    search.choose(state.clone())
    top = max(search.last_root.children.items(), key=lambda kv: kv[1].visits)[0]
    keys = [action_key(state, a) for a in alts]
    assert alts and all(a in legal_actions(state) for a in alts)
    assert len(set(keys)) == len(keys) and top not in keys          # other first moves than the most visited


def test_the_race_score_is_the_clock_then_the_evaluation():
    from svsim.search.candidates import ClockScore
    from svsim.search.evaluate import evaluate
    from svsim.search.race import clock
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    (state, player), _ = _start()
    base = _search(make_agent(SPEC, 0)).weights
    score = ClockScore(base, nodes=100)
    want = -24.0 * clock(state, player, 4, 100).turns + 0.25 * evaluate(state, player, base)
    assert score.score(state, player) == pytest.approx(want)


def test_the_summary_counts_times_by_kind_and_how_often_race_differs():
    from svsim.search.candidates import Candidate, summary
    a = Candidate("bot", [], None, ("a",), 1.0, ["race"], {"bot": 1.0, "race": 3.0})
    b = Candidate("bot", [], None, ("b",), 2.0, [], {"bot": 2.0})
    c = Candidate("race", [], None, ("c",), 5.0, [], {"race": 5.0})
    d = Candidate("keep:7", [], None, ("d",), 1.0, [], {"keep:7": 1.0})
    out = summary([[a], [b, c, d]])
    assert out["seconds"] == {"bot": 1.5, "race": 4.0, "keep": 1.0}
    assert out["race_differs"] == 0.5 and out["candidates"] == 2.0
