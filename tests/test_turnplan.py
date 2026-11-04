"""Whole-turn planning (search.turnplan)."""
from svsim.cards import demo, dragon
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.state import leader_uid
from svsim.search.turnplan import TurnPlanAgent, TurnPlanner
from svsim.tools.arena import make_agent

from helpers import give, put, set_pp, start, unlock_evolution


def _saga_ready():
    state = start()
    unlock_evolution(state, 0)
    state.players[0].hand.clear()
    saga = put(state, 0, dragon.SAGATSUMATSU)
    return state, saga


def test_the_plan_evolves_before_attacking_and_the_agent_follows_it():
    state, saga = _saga_ready()
    plan = TurnPlanner().plan(state)
    assert plan.complete and isinstance(plan.line[0], Evolve) and plan.line[0].uid == saga.uid
    assert plan.line[1] == Attack(saga.uid, leader_uid(1)) and isinstance(plan.line[-1], EndTurn)
    agent, s, played = TurnPlanAgent(), state.clone(), []
    while s.active == 0 and not s.over:
        action = agent.act(s, legal_actions(s))
        played.append(action)
        apply(s, action)
    assert played == plan.line and agent.plans == 1          # one plan for the whole (luck-free) turn
    assert s.players[1].leader_hp <= 20 - (saga.atk + 2)


def _drawing_position(top):
    """Max play points 9 and Dragonsign in hand: playing it reaches 10 and draws."""
    deck = [demo.FOOTMAN] * 30 + [demo.LANCER] * 10
    state = start(deck=deck)
    set_pp(state, 0, 9)
    p = state.players[0]
    p.hand.clear()
    give(state, 0, dragon.DRAGONSIGN)
    give(state, 0, demo.RAIDER)
    p.deck.sort(key=lambda c: (c.defn is not top))           # the hidden order: `top` is next
    return state


def test_luck_is_averaged_and_the_hidden_order_never_matters():
    a = TurnPlanner(seed=3).plan(_drawing_position(demo.LANCER))
    b = TurnPlanner(seed=3).plan(_drawing_position(demo.FOOTMAN))
    assert a.value == b.value and a.line == b.line            # same plan whatever card is on top
    # The line stops at the draw: what comes after depends on the card.
    state = _drawing_position(demo.LANCER)
    sign = state.players[0].hand[0]
    assert sign.defn is dragon.DRAGONSIGN and a.line[-1] == PlayCard(sign.uid)
    agent = TurnPlanAgent(seed=3)
    while state.active == 0 and not state.over:
        apply(state, agent.act(state, legal_actions(state)))
    assert agent.plans == 2                                    # once more after seeing the card


def test_a_small_budget_still_gives_a_legal_plan():
    state, _ = _saga_ready()
    put(state, 0, demo.LANCER)
    put(state, 0, demo.RAIDER)
    plan = TurnPlanner(max_nodes=2).plan(state)
    assert not plan.complete and plan.line and plan.line[0] in legal_actions(state)


def test_turn_planning_agents_play_whole_games():
    from svsim.cards import decks
    from svsim.core.engine import new_game
    for spec in ("turn:300", "turn:300+plan+learned"):
        s = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4)
        agents = [make_agent(spec, 1), make_agent("greedy", 2)]
        for _ in range(3000):
            if s.over:
                break
            actions = legal_actions(s)
            action = agents[s.active].act(s, actions)
            assert action in actions
            apply(s, action)
        assert s.over
