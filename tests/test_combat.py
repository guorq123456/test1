from svsim.cards import demo
from svsim.core.actions import Attack, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Keyword
from svsim.core.state import leader_uid

from helpers import give, put, set_pp, start


def attacks(state):
    return {(a.attacker, a.target) for a in legal_actions(state) if isinstance(a, Attack)}


def test_summoning_sickness_storm_and_rush():
    state = start(first=0)
    enemy = put(state, 1, demo.FOOTMAN)
    plain = put(state, 0, demo.FOOTMAN, ready=False)
    storm = put(state, 0, demo.RAIDER, ready=False)
    rush = put(state, 0, demo.LANCER, ready=False)
    legal = attacks(state)
    assert not any(a == plain.uid for a, _ in legal)
    assert (storm.uid, leader_uid(1)) in legal and (storm.uid, enemy.uid) in legal
    assert (rush.uid, enemy.uid) in legal and (rush.uid, leader_uid(1)) not in legal


def test_ward_redirects_attacks_unless_ambushed():
    state = start(first=0)
    attacker = put(state, 0, demo.FOOTMAN)
    ward = put(state, 1, demo.SHIELDBEARER)
    other = put(state, 1, demo.FOOTMAN)
    assert attacks(state) == {(attacker.uid, ward.uid)}
    ward.keywords |= Keyword.AMBUSH           # Ambush negates Ward
    assert attacks(state) == {(attacker.uid, other.uid), (attacker.uid, leader_uid(1))}


def test_ambush_untargetable_until_it_attacks():
    state = start(first=0)
    shade = put(state, 1, demo.SHADE)
    put(state, 0, demo.FOOTMAN)
    bolt = give(state, 0, demo.FIREBOLT)
    set_pp(state, 0, 5)
    assert all(a.target != shade.uid for a in legal_actions(state) if isinstance(a, Attack))
    assert not any(isinstance(a, PlayCard) and a.uid == bolt.uid
                   for a in legal_actions(state))   # no selectable target
    state.active = 1
    apply(state, Attack(shade.uid, leader_uid(0)))
    assert not shade.has(Keyword.AMBUSH)


def test_damage_exchange_and_destruction():
    state = start(first=0)
    a = put(state, 0, demo.LANCER)        # 3/2
    d = put(state, 1, demo.SHIELDBEARER)  # 1/3
    apply(state, Attack(a.uid, d.uid))
    assert a.life == 1 and d.fate == 1 and state.players[1].shadows == 1


def test_bane_drain_barrier():
    state = start(first=0)
    assassin = put(state, 0, demo.ASSASSIN)
    giant = put(state, 1, demo.GIANT)
    apply(state, Attack(assassin.uid, giant.uid))
    assert giant.fate == 1                          # Bane destroys regardless of damage

    leech = put(state, 0, demo.LEECH)
    state.players[0].leader_hp = 10
    apply(state, Attack(leech.uid, leader_uid(1)))
    assert state.players[0].leader_hp == 12 and state.players[1].leader_hp == 18

    angel = put(state, 1, demo.ANGEL)
    lancer = put(state, 0, demo.LANCER)
    apply(state, Attack(lancer.uid, angel.uid))
    assert angel.life == 3 and not angel.has(Keyword.BARRIER)
