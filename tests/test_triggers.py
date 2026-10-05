from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import EndTurn, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue

from helpers import give, put, set_pp, start


def plays(state, uid):
    return [a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == uid]


def test_fanfare_target_is_optional_but_spell_target_required():
    state = start(first=0)
    set_pp(state, 0, 5)
    archer = give(state, 0, demo.ARCHER)
    bolt = give(state, 0, demo.FIREBOLT)
    assert plays(state, archer.uid) == [PlayCard(archer.uid)]
    assert plays(state, bolt.uid) == []
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, PlayCard(archer.uid, (enemy.uid,)))
    assert enemy.life == 1 and state.players[0].pp == 3


def test_last_words_queue_in_destruction_order():
    state = start(first=0)
    bomber, totem = put(state, 1, demo.BOMBER), put(state, 1, demo.TOTEM)
    E.destroy(state, totem)
    E.destroy(state, bomber)
    assert [t.ctx.source.uid for t in state.queue] == [totem.uid, bomber.uid]   # FIFO
    resolve_queue(state)
    assert state.players[0].leader_hp == 18         # Bomber hits its opponent, player 0
    assert [c.defn for c in state.players[1].field] == [demo.WISP]


def test_simultaneous_deaths_queue_turn_player_then_oldest():
    state = start(first=0)
    mine = put(state, 0, demo.BOMBER)
    theirs_old = put(state, 1, demo.BOMBER)
    theirs_new = put(state, 1, demo.BOMBER)
    for c in (mine, theirs_old, theirs_new):
        c.life = 0
    E.check_deaths(state)
    assert [t.ctx.source.uid for t in state.queue] == [mine.uid, theirs_old.uid, theirs_new.uid]


def test_countdown_amulet():
    state = start(first=0)
    set_pp(state, 0, 2)
    totem = give(state, 0, demo.TOTEM)
    apply(state, PlayCard(totem.uid))
    assert totem.countdown == 2
    apply(state, EndTurn()); apply(state, EndTurn())
    assert totem.countdown == 1
    apply(state, EndTurn()); apply(state, EndTurn())
    assert totem.fate == 1
    assert [c.defn for c in state.players[0].field] == [demo.WISP]


def test_ally_enter_listener_and_rally():
    state = start(first=0)
    put(state, 0, demo.CAPTAIN)
    set_pp(state, 0, 5)
    footman = give(state, 0, demo.FOOTMAN)
    rally_before = state.players[0].rally
    apply(state, PlayCard(footman.uid))
    assert footman.atk == 2
    assert state.players[0].rally == rally_before + 1


def test_both_leaders_dying_at_once_turn_player_loses():
    state = start(first=0)
    for p in state.players:
        p.leader_hp = 3
    set_pp(state, 0, 1)
    card = give(state, 0, demo.BACKFIRE)
    apply(state, PlayCard(card.uid))
    assert state.over and state.winner == 1


def test_enhance_pays_highest_affordable_cost():
    state = start(first=0)
    set_pp(state, 0, 6)
    big, small = give(state, 0, demo.MAGE), give(state, 0, demo.MAGE)
    apply(state, PlayCard(big.uid))
    assert (big.atk, big.life) == (5, 5) and state.players[0].pp == 0
    set_pp(state, 0, 3)
    apply(state, PlayCard(small.uid))
    assert (small.atk, small.life) == (2, 2)


def test_modes_are_separate_actions():
    state = start(first=0)
    set_pp(state, 0, 2)
    oracle = give(state, 0, demo.ORACLE)
    assert {a.modes for a in plays(state, oracle.uid)} == {(0,), (1,)}
    state.players[0].leader_hp = 10
    apply(state, PlayCard(oracle.uid, modes=(1,)))
    assert state.players[0].leader_hp == 13
