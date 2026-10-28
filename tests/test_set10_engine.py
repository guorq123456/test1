"""Engine hooks set 10 needs (asked by the analysis line, 2026-10-28): a Clue cost (consume_clues), the
on_card_banished and on_ally_fuse listeners, "if you've Engaged an amulet this turn", and a countdown card's
start-of-turn ability on the turn its count reaches 0."""
from svsim.cards import demo, neutral, portal
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Engage, Fuse, PlayCard
from svsim.core.engine import apply, resolve_queue
from svsim.core.script import CardScript
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY

from helpers import give, put, set_pp, start


def fresh(pp=10):
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, pp)
    return state


class _Log(CardScript):
    """A granted listener that records what it heard."""

    def __init__(self):
        self.heard = []

    def on_card_banished(self, ctx):
        self.heard.append(("banished", ctx.controller, ctx.other))

    def on_ally_fuse(self, ctx):
        self.heard.append(("fuse", ctx.controller, ctx.other, ctx.cards))

    def on_turn_start(self, ctx):
        self.heard.append(("start", ctx.source.countdown))


def test_consume_clues_needs_enough_clues_like_earth_rite():
    state = fresh()
    assert not E.consume_clues(state, 0, 1)                       # no Clue amulet
    for _ in range(3):
        apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))
    amulet = E.clue_amulet(state, 0)
    assert not E.consume_clues(state, 0, 4) and E.clues(state, 0) == 3
    assert E.consume_clues(state, 0, 2) and E.clues(state, 0) == 1 and amulet.fate == IN_PLAY
    assert E.consume_clues(state, 0, 1) and amulet.fate == DESTROYED


def test_on_card_banished_fires_on_both_sides_for_followers_and_amulets_and_on_a_merge():
    state = fresh()
    mine, theirs = _Log(), _Log()
    E.grant(put(state, 0, demo.FOOTMAN), mine)
    E.grant(put(state, 1, demo.FOOTMAN), theirs)
    enemy = put(state, 1, demo.GIANT)
    E.banish(state, enemy)
    resolve_queue(state)
    first = E.summon(state, 0, neutral.DIVINE_EVIDENCE)
    E.summon(state, 0, neutral.DIVINE_EVIDENCE)                 # the merge banishes the first
    resolve_queue(state)
    assert first.fate == BANISHED
    assert [(h[1], h[2]) for h in mine.heard] == [(0, enemy), (0, first)]
    assert [(h[1], h[2]) for h in theirs.heard] == [(1, enemy), (1, first)]
    E.destroy(state, put(state, 1, demo.GIANT))                  # destroyed is not banished
    resolve_queue(state)
    assert len(mine.heard) == 2


def test_on_ally_fuse_tells_the_fusing_players_cards():
    state = fresh()
    mine, theirs = _Log(), _Log()
    E.grant(put(state, 0, demo.FOOTMAN), mine)
    E.grant(put(state, 1, demo.FOOTMAN), theirs)
    ambition = give(state, 0, portal.GEAR_OF_AMBITION)
    remembrance = give(state, 0, portal.GEAR_OF_REMEMBRANCE)
    apply(state, Fuse(ambition.uid, (remembrance.uid,)))
    assert mine.heard == [("fuse", 0, ambition, (remembrance,))] and theirs.heard == []


def test_engaged_amulet_this_turn_outlives_the_amulet():
    state = fresh(pp=3)
    evidence = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(evidence.uid))
    assert not E.engaged_amulet_this_turn(state, 0)
    apply(state, Engage(evidence.uid))
    assert evidence.fate == DESTROYED and E.engaged_amulet_this_turn(state, 0)
    assert not E.engaged_amulet_this_turn(state, 1)
    assert state.clone().players[0].amulet_engaged_turn == state.turn
    apply(state, EndTurn())
    assert not E.engaged_amulet_this_turn(state, 0)


def test_a_countdown_cards_start_of_turn_ability_also_activates_when_the_count_reaches_zero():
    state = fresh()
    log = _Log()
    totem = put(state, 0, demo.TOTEM)                            # Countdown (2)
    E.grant(totem, log)
    for _ in range(4):
        apply(state, EndTurn())
    assert log.heard == [("start", 1), ("start", 0)] and totem.fate == DESTROYED
