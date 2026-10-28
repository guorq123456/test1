"""Set 10 (Deicide in Nacreheim, 2026-10-28) Neutral cards: Exias, Dynames, Scene of Deicide, Kyrios, Rezeal and
Crest: Rezeal (Nacreheim and Divine Evidence: tests/test_clue.py)."""
from svsim.cards import demo, neutral
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import Keyword
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY

from helpers import count, give, put, set_pp, start, unlock_evolution


def fresh(pp=10):
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, pp)
    return state


def test_exias_adds_a_divine_evidence_and_has_rush():
    state = fresh()
    exias = give(state, 0, neutral.EXIAS)
    apply(state, PlayCard(exias.uid))
    assert count(state.players[0].hand, neutral.DIVINE_EVIDENCE) == 1 and exias.has(Keyword.RUSH)


def test_dynames_hits_and_adds_evidence_on_fanfare_and_again_on_evolve():
    state = fresh()
    a, b = put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.GIANT)      # 1/3, 5/5
    dynames = give(state, 0, neutral.DYNAMES)
    apply(state, PlayCard(dynames.uid, (a.uid,)))
    assert a.life == 1 and b.life == 5 and count(state.players[0].hand, neutral.DIVINE_EVIDENCE) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(dynames.uid, targets=(b.uid,)))
    assert b.life == 3 and a.life == 1 and count(state.players[0].hand, neutral.DIVINE_EVIDENCE) == 2


def test_scene_of_deicide_banishes_a_random_enemy_and_gives_them_a_divine_evidence():
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    scene = give(state, 0, neutral.SCENE_OF_DEICIDE)
    apply(state, PlayCard(scene.uid))
    assert scene.countdown == 3
    apply(state, EndTurn())
    assert enemy.fate == BANISHED and state.players[1].shadows == 0
    evidence = E.clue_amulet(state, 1)
    assert evidence is not None and evidence.defn is neutral.DIVINE_EVIDENCE and E.clues(state, 1) == 1
    assert E.clue_amulet(state, 0) is None


def test_scene_of_deicide_with_no_enemy_follower_still_summons_the_evidence():
    state = fresh()
    scene = give(state, 0, neutral.SCENE_OF_DEICIDE)
    apply(state, PlayCard(scene.uid))
    apply(state, EndTurn())
    assert E.clues(state, 1) == 1 and scene.fate == IN_PLAY


def test_kyrios_damages_all_enemy_followers_and_adds_two_evidence():
    state = fresh()
    a, b = put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.FOOTMAN)    # 1/3, 1/2
    mine = put(state, 0, demo.FOOTMAN)
    kyrios = give(state, 0, neutral.KYRIOS)
    apply(state, PlayCard(kyrios.uid))
    assert a.life == 1 and b.fate == DESTROYED and mine.life == 2
    assert count(state.players[0].hand, neutral.DIVINE_EVIDENCE) == 2 and kyrios.has(Keyword.WARD)


def test_rezeal_deals_nine_and_its_super_evolution_gains_the_crest():
    state = fresh()
    big = put(state, 1, demo.GIANT)
    big.life = big.max_life = 20
    rezeal = give(state, 0, neutral.REZEAL)
    apply(state, PlayCard(rezeal.uid, (big.uid,)))
    assert big.life == 11                                  # exactly 9 (the analysis line's review)
    unlock_evolution(state, 0)
    apply(state, Evolve(rezeal.uid))                       # a normal evolution: no crest
    assert E.leader_area_card(state, 0, neutral.REZEAL_CREST) is None
    other = put(state, 0, neutral.REZEAL)
    apply(state, Evolve(other.uid, super_=True))
    assert E.leader_area_card(state, 0, neutral.REZEAL_CREST) is not None


def test_rezeal_crest_gives_played_followers_a_copy_on_death_and_no_attack_this_turn():
    state = fresh()
    E.add_to_leader_area(state, 0, neutral.REZEAL_CREST)
    lancer = give(state, 0, demo.LANCER)                   # Rush: it could attack right away
    apply(state, PlayCard(lancer.uid))
    target = put(state, 1, demo.FOOTMAN)
    attacks = [a for a in legal_actions(state) if isinstance(a, Attack) and a.attacker == lancer.uid]
    assert attacks == []
    E.destroy(state, lancer)
    E.check_deaths(state)
    resolve_queue(state)
    copies = [c for c in state.players[0].followers if c.defn is demo.LANCER]
    assert len(copies) == 1 and copies[0] is not lancer
    copies[0].entered_turn = -1                            # the copy is a fresh card, not played: it can attack
    assert any(isinstance(a, Attack) and a.attacker == copies[0].uid for a in legal_actions(state))
    assert target.fate == IN_PLAY


def test_rezeal_crest_no_attack_lasts_until_the_end_of_the_turn_only():
    state = fresh()
    E.add_to_leader_area(state, 0, neutral.REZEAL_CREST)
    lancer = give(state, 0, demo.LANCER)
    apply(state, PlayCard(lancer.uid))
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert any(isinstance(a, Attack) and a.attacker == lancer.uid for a in legal_actions(state))


def test_rezeal_crest_ignores_spells_and_summoned_followers():
    state = fresh()
    E.add_to_leader_area(state, 0, neutral.REZEAL_CREST)
    summoned = put(state, 0, demo.LANCER)
    enemy = put(state, 1, demo.FOOTMAN)
    bolt = give(state, 0, demo.FIREBOLT)
    apply(state, PlayCard(bolt.uid, (enemy.uid,)))
    assert not summoned.grants and any(isinstance(a, Attack) and a.attacker == summoned.uid
                                       for a in legal_actions(state))
