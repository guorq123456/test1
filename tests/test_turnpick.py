"""The whole-turn pick (agents.turnpick_agent): plans as keys that replay, deduped, the bot's first; a turn it doesn't
switch is the base agent's, step for step; a restriction's veto reaches the lethal search; a game won during the turn
scores 1; the switching rule; the +pick option."""
import pytest

from test_handvalue import _positions

BASE = "mcts:20+plan+learned+phased"


def _start():
    positions, _ = _positions()
    return next((s, p) for s, p in positions[8:] if len(s.players[p].hand) >= 2)


def _agent(extra="pickd2i10", seed=0):
    from svsim.tools.arena import make_agent
    return make_agent(f"{BASE}+{extra}", seed)


def test_plans_are_deduped_bot_first_and_their_keys_replay_on_the_guess():
    from svsim.learn.contrast import replay_turn
    from svsim.search.lethal import state_key
    state, me = _start()
    agent = _agent().base
    plans = agent.plans(state)
    assert plans[0][0] == "bot"
    assert len({k for k, _ in plans}) == len(plans)
    assert all(len(keys) > 0 for _, keys in plans)
    # the same keys on two shared determinizations: every plan scored on each, in [0, 1]
    vals = agent.values(state, plans)
    assert set(vals) == {k for k, _ in plans}
    assert all(len(v) == 2 and all(0.0 <= x <= 1.0 for x in v) for v in vals.values())
    # a plan's keys replay it exactly on the position it was played on
    from svsim.search.candidates import generate
    from svsim.agents.turnpick_agent import keys_of
    for c in generate(state, spec=BASE, kinds=("bot", "second", "end")):
        _, again = replay_turn(state, keys_of(state, c.actions))
        assert state_key(again) == c.key


def test_a_turn_it_does_not_switch_is_the_base_agents_step_for_step():
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    state, me = _start()

    def play(agent, turns=3):
        s, seen, out = state.clone(), 0, []
        opp = make_agent(BASE, 99)
        while not s.over and seen < turns:
            mover = agent if s.active == me else opp
            a = mover.act(s, legal_actions(s))
            out.append((s.active, repr(a)))
            if s.active != me and type(a).__name__ == "EndTurn":
                seen += 1
            apply(s, a)
        return out
    never = make_agent(f"{BASE}+pickd2i10m9", 5)             # margin 9: no plan can win by that much
    assert play(never) == play(make_agent(BASE, 5))
    assert never.base.turns >= 2 and set(never.base.picked) == {"bot"}


def test_a_picked_restriction_keeps_its_veto_on_the_search_the_lethal_search_reads_until_the_next_turn():
    from svsim.core.engine import legal_actions
    from svsim.agents.crossturn_agent import forbids
    state, me = _start()
    agent = _agent("pickd2i10")
    inner = agent.base
    card = state.players[me].hand[0].defn.card_id
    kind = f"keep:{card}"
    inner.choose_plan = lambda s: (kind, [("T",)])
    agent.act(state, legal_actions(state))
    veto = agent._veto()
    assert veto is not None and veto is inner.search.veto
    for a in legal_actions(state):
        assert veto(state, a) == forbids(kind)(state, a)
    nxt = state.clone()
    nxt.turn += 2
    inner.choose_plan = lambda s: ("bot", None)
    agent.act(nxt, legal_actions(nxt))
    assert inner.search.veto is inner._own_veto


def test_a_game_won_during_the_turn_scores_its_result():
    from svsim.agents.turnpick_agent import turn_value
    from svsim.core.enums import Phase
    state, me = _start()
    over = state.clone()
    over.winner, over.phase = me, Phase.OVER
    assert turn_value(over, me, None) == 1.0
    over.winner = 1 - me
    assert turn_value(over, me, None) == 0.0


def test_the_switching_rule_needs_the_margin_and_z_paired_standard_errors():
    from svsim.agents.turnpick_agent import paired_better
    base = [0.5, 0.5, 0.5, 0.5]
    assert paired_better([0.6, 0.6, 0.6, 0.6], base, 0.0, 1.0)         # a sure gain (no spread)
    assert not paired_better([0.6, 0.6, 0.6, 0.6], base, 0.2, 1.0)     # under the margin
    assert not paired_better([0.9, 0.3, 0.9, 0.3], base, 0.0, 1.0)     # mean 0.1, se 0.17: not past 1 se
    assert paired_better([0.9, 0.3, 0.9, 0.3], base, 0.0, 0.5)


def test_the_pick_option():
    from svsim.agents.turnpick_agent import TurnPickAgent
    a = _agent("pickd4i50m0.01z2ksk")
    inner = a.base
    assert isinstance(inner, TurnPickAgent)
    assert (inner.samples, inner.margin, inner.z) == (4, 0.01, 2.0)
    assert inner.kinds == ("bot", "second", "keep")
    assert inner.plan_spec == "mcts:50+plan+learned+phased"
    d = _agent("pick").base
    assert (d.samples, d.margin, d.z, d.kinds) == (8, 0.0, 1.0, ("bot", "second", "third", "race"))
    with pytest.raises(ValueError):
        _agent("pick+cross")
    with pytest.raises(ValueError):
        _agent("pickq")
