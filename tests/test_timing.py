"""Card timing learned from a player's games (svsim.learn.timing)."""
from svsim.agents.mulligan import PLAYER_RULES, mulligan
from svsim.cards import decks, forest, unlimited
from svsim.core.engine import new_game
from svsim.learn.timing import CardStats, Timed, Timing, load


def _timing():
    """Two cards: one the player plays at once, one they hold until turn 8."""
    t = Timing("rhino", "ramp", games=5)
    early, late = forest.SPROUTING_INITIATE.card_id, unlimited.BAYLE.card_id
    t.cards[early] = CardStats()
    t.cards[late] = CardStats()
    for turn in range(1, 11):
        t.cards[early].in_hand[turn] = 4
        t.cards[early].played[turn] = 3
        t.cards[late].in_hand[turn] = 4
        t.cards[late].played[turn] = 3 if turn >= 8 else 0
    t.cards[early].kept = [4, 1]
    t.cards[late].redrawn = [3, 2]
    return t, early, late


def test_hazard_hold_and_early_follow_the_counts():
    t, early, late = _timing()
    assert t.hazard(early, 2) > 0.6 and t.hazard(late, 2) < 0.2 and t.hazard(late, 9) > 0.5
    assert t.hold(early, 4) < 0.05 and t.hold(late, 4) > 0.5 and t.hold(late, 10) < t.hold(late, 4)
    assert t.early(early) > 0.9 > 0.5 > t.early(late)
    assert t.median_turn(late) == 9


def test_keep_uses_the_players_record_with_their_words_as_the_prior():
    t, early, late = _timing()
    assert t.keep_chance(early, 0, 0.5) > 0.5 > t.keep_chance(late, 0, 0.5)
    # The player said: keep one Bayle. Three redraws of a first copy still outweigh it.
    rules = PLAYER_RULES["rhino"]
    assert t.keep_chance(late, 0, 0.5, rules) < 0.5
    t.cards[late].redrawn = [0, 0]
    assert t.keep_chance(late, 0, 0.5, rules) > 0.5 > t.keep_chance(late, 1, 0.5, rules)


def test_the_saved_profile_reaches_the_ai_redraw_and_round_trips():
    t, _, _ = _timing()
    assert Timing.from_json(t.to_json()).to_json() == t.to_json()
    saved = load("rhino", "ramp")
    assert saved is not None and saved.games >= 10
    state = new_game(decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON), seed=0, first=0)
    p = state.players[0]
    assert mulligan(state).indices == saved.keep(p.hand, p.hand + p.deck, PLAYER_RULES["rhino"])


def test_holding_a_card_before_its_time_is_worth_something():
    from svsim.core.enums import Craft
    from svsim.core.actions import Mulligan
    from svsim.core.engine import apply
    from svsim.core import effects as E
    t, early, late = _timing()
    state = new_game(decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON), seed=0, first=0)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    state.players[0].hand.clear()
    state.players[0].turns_taken = 4
    timed = Timed(weight=2.0, profiles={(Craft.FOREST, Craft.DRAGON): t})
    holding_bayle, holding_sprout = state.clone(), state.clone()
    E.add_to_hand(holding_bayle, 0, unlimited.BAYLE)
    E.add_to_hand(holding_sprout, 0, forest.SPROUTING_INITIATE)
    assert timed.hold(holding_bayle, 0) > 0.5 > 0.05 > timed.hold(holding_sprout, 0)
    assert timed.score(holding_bayle, 0) > timed.score(holding_sprout, 0)
