"""Clue (set 10, Deicide in Nacreheim, 2026-10-28): the rule as Dengeki Online 10-27 reported the official stream
(the architecture thread 10-28) and the two Clue amulets' text. A Clue amulet enters with 1 clue; entering banishes
the allied Clue amulets already on the field and adds their clues to it. At 0 clues it is destroyed (not stated by
the source yet: as Earth Sigil, effects.CLUE_ZERO_DESTROYS)."""
from svsim.cards import neutral
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Engage, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY

from helpers import give, set_pp, start


def fresh(pp=10):
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, pp)
    return state


def test_a_clue_amulet_enters_with_one_clue():
    state = fresh()
    evidence = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(evidence.uid))
    assert E.is_clue(evidence) and E.clue_amulet(state, 0) is evidence
    assert E.counters(evidence)["clues"] == 1 and E.clues(state, 0) == 1 and E.clues(state, 1) == 0


def test_a_second_clue_amulet_banishes_the_first_and_takes_its_clues():
    state = fresh()
    p = state.players[0]
    first = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(first.uid))
    second = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(second.uid))
    assert first.fate == BANISHED and second.fate == IN_PLAY
    assert [c for c in p.field if E.is_clue(c)] == [second] and E.clues(state, 0) == 2
    assert p.shadows == 0                                  # banished: no shadow
    third = E.summon(state, 0, neutral.NACREHEIM)          # summoned ones merge too
    assert E.clues(state, 0) == 3 and E.clue_amulet(state, 0) is third and second.fate == BANISHED


def test_engage_draws_and_consumes_a_clue_and_the_amulet_goes_at_zero():
    state = fresh(pp=3)
    p = state.players[0]
    evidence = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(evidence.uid))
    assert not E.engaged_clue_this_turn(state, 0)
    hand = len(p.hand)
    apply(state, Engage(evidence.uid))
    assert len(p.hand) == hand + 1 and p.pp == 1
    assert evidence.fate == DESTROYED and E.clues(state, 0) == 0 and E.clue_amulet(state, 0) is None
    assert E.engaged_clue_this_turn(state, 0) and not E.engaged_clue_this_turn(state, 1)
    apply(state, EndTurn())
    assert not E.engaged_clue_this_turn(state, 0)


def test_with_two_clues_the_amulet_stays_after_one_engage():
    state = fresh(pp=5)
    for _ in range(2):
        apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))
    amulet = E.clue_amulet(state, 0)
    apply(state, Engage(amulet.uid))
    assert amulet.fate == IN_PLAY and E.clues(state, 0) == 1
    assert not any(isinstance(a, Engage) for a in legal_actions(state))   # once per turn


def test_nacreheim_heals_when_banished_also_by_a_merge():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    nacreheim = give(state, 0, neutral.NACREHEIM)
    apply(state, PlayCard(nacreheim.uid))
    assert E.clues(state, 0) == 1 and p.leader_hp == 10
    apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))   # inferred: the merge banishes it
    assert nacreheim.fate == BANISHED and p.leader_hp == 12 and E.clues(state, 0) == 2


def test_nacreheim_destroyed_at_zero_clues_does_not_heal():
    state = fresh(pp=3)
    p = state.players[0]
    p.leader_hp = 10
    nacreheim = give(state, 0, neutral.NACREHEIM)
    apply(state, PlayCard(nacreheim.uid))
    apply(state, Engage(nacreheim.uid))
    assert nacreheim.fate == DESTROYED and p.leader_hp == 10


def test_the_clue_engage_turn_is_copied_with_the_state():
    state = fresh(pp=3)
    apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))
    apply(state, Engage(E.clue_amulet(state, 0).uid))
    assert state.clone().players[0].clue_engaged_turn == state.turn
