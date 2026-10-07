"""Lethal search: finds lines, doesn't peek at luck or hidden cards, and the agent and
tools built on it. Synthetic cards use ids 7101+."""
from svsim.agents.lethal_agent import LethalAgent
from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import CardType, Craft
from svsim.core.script import CardScript, register
from svsim.core.state import leader_uid
from svsim.search.lethal import find_lethal, state_key
from svsim.tools import lethal as tool
from svsim.ui.text import describe_line, render_state

from helpers import give, put, set_pp, start, unlock_evolution

N, S, A = Craft.NEUTRAL, CardType.SPELL, CardType.AMULET
LUCKY_SHOT = CardDef(7101, "Lucky Shot", N, S, 1)        # 3 damage to a random enemy
SCOUT = CardDef(7102, "Scout's Report", N, S, 1)         # draw a card
FIREBALL = CardDef(7103, "Fireball", N, S, 1)            # 5 damage to the enemy leader
SIEGE = CardDef(7104, "Siege Engine", N, A, 2)           # end of turn: 2 damage to the enemy leader


@register(LUCKY_SHOT.card_id)
class LuckyShot(CardScript):
    def cast(self, ctx):
        enemies = list(ctx.opponent.followers) + [leader_uid(1 - ctx.controller)]
        E.damage(ctx.state, E.random_sample(ctx.state, enemies, 1), 3, ctx.source)


@register(SCOUT.card_id)
class Scout(CardScript):
    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(FIREBALL.card_id)
class Fireball(CardScript):
    def cast(self, ctx):
        E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 5, ctx.source)


@register(SIEGE.card_id)
class Siege(CardScript):
    def on_turn_end(self, ctx):
        E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 2, ctx.source)


def position(hp: int, pp: int = 0):
    """Player 0 to act on turn 1 with an empty hand and the opponent at `hp`."""
    state = start(first=0)
    state.players[0].hand.clear()
    state.players[1].leader_hp = hp
    set_pp(state, 0, pp)
    return state


def test_attacks_the_leader_for_lethal():
    state = position(3)
    lancer = put(state, 0, demo.LANCER)                     # 3/2
    r = find_lethal(state)
    assert r.sure and r.probability == 1 and r.line == [Attack(lancer.uid, leader_uid(1))]


def test_clears_ward_before_going_face():
    state = position(2)
    giant = put(state, 0, demo.GIANT)                       # 5/5
    raider = put(state, 0, demo.RAIDER)                     # 2/1 Storm
    wall = put(state, 1, demo.SHIELDBEARER)                 # 1/3 Ward
    r = find_lethal(state)
    assert r.sure and len(r.line) == 2 and isinstance(r.line[1], Attack)
    assert {a.attacker for a in r.line} == {giant.uid, raider.uid}
    assert r.line[0].target == wall.uid and r.line[1].target == leader_uid(1)
    assert not tool.face_only_wins(state)


def test_evolves_for_the_extra_damage():
    state = position(5)
    unlock_evolution(state, 0)
    lancer = put(state, 0, demo.LANCER)                     # 3/2, evolved 5/4
    r = find_lethal(state)
    assert r.sure and r.line[-1] == Attack(lancer.uid, leader_uid(1))
    assert any(isinstance(a, Evolve) and a.uid == lancer.uid for a in r.line)


def test_reports_no_lethal():
    state = position(20)
    put(state, 0, demo.LANCER)
    r = find_lethal(state)
    assert not r.sure and r.probability == 0 and r.complete


def test_random_damage_is_a_chance_not_a_sure_lethal():
    state = position(3, pp=1)
    put(state, 1, demo.FOOTMAN)
    put(state, 1, demo.FOOTMAN)
    give(state, 0, LUCKY_SHOT)                              # hits the leader 1 time in 3
    r = find_lethal(state, samples=16)
    assert not r.sure and 0 < r.probability < 1
    assert len(r.line) == 1 and isinstance(r.line[0], PlayCard)


def test_prefers_a_sure_line_to_a_lucky_one():
    state = position(3, pp=1)
    put(state, 1, demo.FOOTMAN)
    give(state, 0, LUCKY_SHOT)
    lancer = put(state, 0, demo.LANCER)
    r = find_lethal(state)
    assert r.sure and r.line == [Attack(lancer.uid, leader_uid(1))]


def test_does_not_peek_at_the_deck():
    state = position(5, pp=2)
    give(state, 0, SCOUT)
    state.players[0].deck.append(state.new_instance(FIREBALL, 0))   # on top: the simulator would draw it
    r = find_lethal(state, samples=16)
    assert not r.sure and r.probability < 0.5


def test_end_of_turn_damage_and_deck_out_count():
    state = position(2)
    put(state, 0, SIEGE)
    r = find_lethal(state)
    assert r.sure and r.line == [EndTurn()]
    state = position(20)
    state.players[1].deck.clear()                           # the opponent can't draw next turn
    assert find_lethal(state).line == [EndTurn()]


def test_search_leaves_the_state_untouched():
    state = position(2)
    put(state, 0, demo.GIANT)
    put(state, 1, demo.SHIELDBEARER)
    give(state, 0, LUCKY_SHOT)
    before, rng = state_key(state), state.rng.getstate()
    find_lethal(state)
    assert state_key(state) == before and state.rng.getstate() == rng


class Passer:
    def act(self, state, actions):
        return EndTurn()


def test_lethal_agent_plays_the_line_out():
    state = position(2)
    put(state, 0, demo.GIANT)
    put(state, 0, demo.RAIDER)
    put(state, 1, demo.SHIELDBEARER)
    agent = LethalAgent(Passer())
    while not state.over and state.active == 0:
        apply(state, agent.act(state, legal_actions(state)))
    assert state.winner == 0 and agent.lethals == 1


def test_lethal_agent_defers_without_lethal():
    state = position(20)
    put(state, 0, demo.GIANT)
    agent = LethalAgent(Passer())
    assert agent.act(state, legal_actions(state)) == EndTurn()


def test_text_rendering_names_cards_and_targets():
    state = position(2)
    put(state, 0, demo.GIANT)
    put(state, 0, demo.RAIDER)
    put(state, 1, demo.SHIELDBEARER)
    steps = describe_line(state, find_lethal(state).line)
    assert steps[0].endswith("攻击敌方场上的「Shieldbearer」")
    assert steps[1] == "「Raider」攻击敌方主战者"
    text = render_state(state)
    assert "主战者 2/20" in text and "守护" in text and "疾驰" in text


def test_saved_positions_replay_exactly():
    for i, (state, record) in enumerate(tool.turn_starts("starter", 1, seed=3)):
        if i == 6:
            assert state_key(tool.replay(record)) == state_key(state)
            break


def test_damage_estimate_counts_attacks_cards_and_evolution():
    from svsim.search.lethal import damage_estimate
    state = position(20, pp=2)
    put(state, 0, demo.LANCER)                              # 3 to the face
    put(state, 0, demo.LANCER, ready=False)                 # just played: can't hit the leader
    give(state, 0, demo.RAIDER)                             # 2-cost 2/1 Storm: +2
    assert damage_estimate(state) == 5
    unlock_evolution(state, 0)
    assert damage_estimate(state) == 8                      # super-evolving the ready Lancer: +3


def test_screening_only_shortens_hopeless_searches():
    state = position(2)
    put(state, 0, demo.GIANT)
    put(state, 0, demo.RAIDER)
    put(state, 1, demo.SHIELDBEARER)
    r = find_lethal(state, screen=50)
    assert r.sure and not r.screened                        # 5 + 2 face damage >= 2
    state = position(20)
    put(state, 0, demo.LANCER)
    r = find_lethal(state, screen=50)
    assert r.screened and not r.sure and r.nodes <= 50
