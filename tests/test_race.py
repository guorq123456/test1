"""Race clocks (search.race) and the impact of a turn (search.impact)."""
import random

from svsim.cards import demo, dragon
from svsim.core.actions import EndTurn
from svsim.core.engine import apply
from svsim.search import impact, race

from helpers import give, put, set_pp, start


def _empty_hands(state):
    for p in state.players:
        p.hand.clear()


def test_advance_starts_the_sides_next_turn_with_nothing_in_between():
    state = start()
    _empty_hands(state)
    set_pp(state, 0, 3)
    s = race.advance(state.clone(), 0)
    p = s.players[0]
    assert s.active == 0 and s.turn == state.turn + 2
    assert p.max_pp == 4 and p.pp == 4 and len(p.hand) == 1 and p.turns_taken == state.players[0].turns_taken + 1
    assert s.players[1].turns_taken == state.players[1].turns_taken     # the opponent's turn didn't happen
    t = race.advance(state.clone(), 1)                                   # the other side: its next turn
    assert t.active == 1 and t.turn == state.turn + 1 and len(t.players[1].hand) == 1


def test_the_clock_counts_the_turns_until_the_damage_is_there():
    state = start()
    _empty_hands(state)
    state.players[1].leader_hp = 5
    give(state, 0, dragon.SAGATSUMATSU)                  # Storm, 5 attack, costs 7
    for pp, turns in ((7, 0), (5, 2), (3, 4)):
        set_pp(state, 0, pp)
        clock = race.clock(state, 0)
        assert clock.turns == turns, (pp, clock)
    state.players[1].leader_hp = 30
    assert race.clock(state, 0).turns == race.HORIZON + 1             # never, within the horizon


def test_followers_already_out_chip_in_on_the_turns_held():
    state = start()
    _empty_hands(state)
    put(state, 0, demo.RAIDER)                            # 2 a turn
    state.players[1].leader_hp = 6
    assert race.board_chip(state, 0) == 2
    assert race.clock(state, 0).turns == 2               # 2 + 2 + 2
    put(state, 1, demo.SHIELDBEARER)                      # Ward with 3 defense soaks it all up
    assert race.board_chip(state, 0) == 0


def test_whose_turn_it_is_matters():
    state = start()
    _empty_hands(state)
    put(state, 0, demo.RAIDER)
    state.players[1].leader_hp = 2
    assert race.clock(state, 0).turns == 0               # player 0 to act: it attacks now
    assert race.clock(state, 1).turns == race.HORIZON + 1
    apply(state, EndTurn())                               # player 1's turn: player 0 attacks on its next one
    assert race.clock(state, 0).turns == 0


def _race_position():
    state = start(deck=[demo.FOOTMAN] * 40)
    _empty_hands(state)
    set_pp(state, 0, 3)
    set_pp(state, 1, 3)
    state.players[0].leader_hp = 4
    for _ in range(2):
        put(state, 1, demo.RAIDER)                        # the opponent's board kills an unwarded player
    return state


def test_ending_the_turn_into_lethal_shows_up_as_killed():
    state = _race_position()
    wall = state.clone()
    put(wall, 0, demo.SHIELDBEARER)                       # a Ward in the way (as if it had been played)
    out = impact.assess(state, [state, wall], ["end", "ward"], samples=3, opponent="greedy")
    end, ward = out
    assert end["killed"] == 1.0 and end["race"] == 0.0 and end["value"] == 0.0
    assert ward["killed"] < 1.0
    assert end.turn["hand"] == 0 and end.turn["face"] == 0


def test_the_impact_does_not_depend_on_how_the_hidden_cards_lie():
    deck = [demo.FOOTMAN] * 20 + [demo.RAIDER] * 20
    a = start(deck=deck)
    b = a.clone()
    for s, seed in ((a, 1), (b, 2)):
        rng = random.Random(seed)
        rng.shuffle(s.players[0].deck)
        pool = s.players[1].hand + s.players[1].deck
        rng.shuffle(pool)
        n = len(s.players[1].hand)
        s.players[1].hand, s.players[1].deck = pool[:n], pool[n:]
    ra = impact.assess(a, [a], samples=2, opponent="greedy")[0]
    rb = impact.assess(b, [b], samples=2, opponent="greedy")[0]
    assert ra.totals == rb.totals and ra.clocks == rb.clocks


def test_the_table_lists_every_dimension():
    state = _race_position()
    out = impact.assess(state, [state], ["end"], samples=1, opponent="greedy")
    text = impact.table(out)
    for _, label, _ in impact.DIMENSIONS:
        assert label in text


def test_ramping_first_can_bring_the_kill_closer():
    # The player on Ramp Dragon: "3 into 5, 5 into 7, then the damage comes turn after turn".
    state = start()
    _empty_hands(state)
    state.players[1].leader_hp = 5
    set_pp(state, 0, 3)
    give(state, 0, dragon.DRAGONSIGN)                     # 3: gain 1 max play point
    give(state, 0, dragon.SAGATSUMATSU)                   # 7: Storm, 5 attack
    assert race.clock(state, 0, ramp=False).turns == 4     # 7 play points four turns from now
    clock = race.clock(state, 0)
    assert clock.turns == 3 and clock.how.startswith("ramp")
    s = state.clone()
    race.develop(s, 0)
    assert s.players[0].max_pp == 4 and len(s.players[0].hand) == 1


def test_an_accelerate_counts_as_ramp_when_it_is_the_way_the_card_is_played():
    state = start()
    _empty_hands(state)
    set_pp(state, 0, 3)
    give(state, 0, dragon.LUMIORE_AND_ARGENTE)            # 8 to play, Accelerate (3): gain 1 max play point
    s = state.clone()
    race.develop(s, 0)
    assert s.players[0].max_pp == 4 and not s.players[0].hand
    set_pp(state, 0, 8)                                    # at 8 it is the follower: not ramp
    s = state.clone()
    race.develop(s, 0)
    assert s.players[0].max_pp == 8 and len(s.players[0].hand) == 1


def test_a_burst_that_sets_up_next_turns_kill_is_played():
    # The player's two-turn finish: deal what you can now when it makes next turn's kill.
    from svsim.agents.lethal_agent import LethalAgent
    from svsim.agents.mcts_agent import MCTSAgent
    from svsim.core.engine import legal_actions
    state = start()
    _empty_hands(state)
    set_pp(state, 0, 2)
    state.players[1].leader_hp = 4
    give(state, 0, demo.RAIDER)                          # Storm 2/1 for 2: one now, the other next turn
    give(state, 0, demo.RAIDER)
    agent = LethalAgent(MCTSAgent(30, seed=1), seed=1, burst=True)
    line = agent._burst_line(state, legal_actions(state))
    assert line and line[0].__class__.__name__ == "PlayCard"
    state.players[1].leader_hp = 9                        # out of reach next turn either way: hold
    assert agent._burst_line(state, legal_actions(state)) == []
