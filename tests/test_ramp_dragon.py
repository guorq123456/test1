"""Ramp Dragon cards and tokens."""
from svsim.cards import demo, dragon, neutral
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import Keyword
from svsim.core.state import DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution


def test_vorlalai_evolve_and_super_evolve():
    for super_, depths in ((False, 1), (True, 3)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        unlock_evolution(state, 0)
        vorlalai = put(state, 0, dragon.VORLALAI)
        apply(state, Evolve(vorlalai.uid, super_=super_))
        assert count(p.hand, dragon.DEPTHS_OF_THE_ELD_BLADES) == depths


def test_depths_of_the_eld_blades_cast_and_discard():
    state = start()
    p = state.players[0]
    p.hand.clear()
    p.leader_hp = 10
    set_pp(state, 0, 2)
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    apply(state, PlayCard(depths.uid))
    assert state.players[1].leader_hp == 19 and p.leader_hp == 11
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    E.discard(state, depths)
    resolve_queue(state)
    assert state.players[1].leader_hp == 18 and p.leader_hp == 12


def test_dragonewt_promoter_enhance():
    for pp, promoters in ((2, 1), (4, 3)):
        state = start()
        set_pp(state, 0, pp)
        card = give(state, 0, dragon.DRAGONEWT_PROMOTER)
        apply(state, PlayCard(card.uid))
        assert count(state.players[0].field, dragon.DRAGONEWT_PROMOTER) == promoters
        assert state.players[0].pp == 0


def test_kimika_evolve_replicates_the_fanfare():
    state = start()
    p = state.players[0]
    p.hand.clear()
    unlock_evolution(state, 0)
    kimika = put(state, 0, dragon.KIMIKA)
    vorlalai = give(state, 0, dragon.VORLALAI)
    apply(state, Evolve(kimika.uid, targets=(vorlalai.uid,)))
    assert count(p.field, dragon.VORLALAI) == 1 and len(p.hand) == 1


def test_sloth_hits_twice_and_goes_face_in_overflow():
    for max_pp, face in ((6, 0), (7, 2)):
        state = start()
        a, b = put(state, 1, demo.RAIDER), put(state, 1, demo.RAIDER)   # 2/1 each
        set_pp(state, 0, max_pp)
        sloth = give(state, 0, dragon.SLOTH_OF_THE_CRESTPETAL)
        apply(state, PlayCard(sloth.uid))
        assert a.fate == DESTROYED and b.fate == DESTROYED
        assert state.players[1].leader_hp == 20 - face


def test_dragonsign():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 3)
    card = give(state, 0, dragon.DRAGONSIGN)
    hand = len(p.hand)
    apply(state, PlayCard(card.uid))
    assert (p.max_pp, p.pp, len(p.hand)) == (4, 0, hand - 1)    # the new point is empty
    set_pp(state, 0, 9)
    card = give(state, 0, dragon.DRAGONSIGN)
    hand = len(p.hand)
    apply(state, PlayCard(card.uid))
    assert (p.max_pp, len(p.hand)) == (10, hand)                # 10 max PP: draw


def test_lazing_flame():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    for max_pp, hp, drew in ((3, 13, 0), (7, 16, 1)):
        set_pp(state, 0, max_pp)
        card = give(state, 0, dragon.LAZING_FLAME)
        hand = len(p.hand)
        apply(state, PlayCard(card.uid))
        assert p.leader_hp == hp and len(p.hand) == hand - 1 + drew


def test_roar_of_prominence_counts_every_follower():
    state = start()
    mine = put(state, 0, demo.CAPTAIN)                # 3/4
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    roar = give(state, 0, dragon.ROAR_OF_PROMINENCE)
    apply(state, PlayCard(roar.uid))
    assert small.fate == DESTROYED and (mine.life, big.life) == (1, 2)   # X = 3


def test_fate_of_the_world():
    state = start()
    p = state.players[0]
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    card = give(state, 0, neutral.FATE_OF_THE_WORLD)
    hand = len(p.hand)
    apply(state, PlayCard(card.uid))
    assert big.fate == DESTROYED and small.fate == IN_PLAY and len(p.hand) == hand + 1
    set_pp(state, 0, 10)
    card = give(state, 0, neutral.FATE_OF_THE_WORLD)
    apply(state, PlayCard(card.uid))                  # Enhance (10): also 4 to all enemies
    assert small.fate == DESTROYED and state.players[1].leader_hp == 16


def test_zooey():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 5)
    zooey = give(state, 0, dragon.ZOOEY)
    apply(state, PlayCard(zooey.uid))
    assert p.max_pp == 6 and not zooey.has(Keyword.STORM)


def test_zooey_enhanced_trades_max_defense_for_a_turn_of_safety():
    state = start(first=0)
    p = state.players[0]
    set_pp(state, 0, 10)
    zooey = give(state, 0, dragon.ZOOEY)
    apply(state, PlayCard(zooey.uid))
    assert (p.leader_hp, p.leader_max_hp) == (1, 1)
    assert Attack(zooey.uid, leader_uid(1)) in legal_actions(state)     # Storm
    apply(state, EndTurn())                           # opponent's turn: no damage gets through
    raider = put(state, 1, demo.RAIDER)
    apply(state, Attack(raider.uid, leader_uid(0)))
    assert p.leader_hp == 1 and not state.over
    apply(state, EndTurn())
    assert p.damage_cap is None


def test_sagatsumatsu():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 7)
    saga = give(state, 0, dragon.SAGATSUMATSU)
    vorlalai = give(state, 0, dragon.VORLALAI)
    apply(state, PlayCard(saga.uid, (vorlalai.uid,)))
    assert count(p.hand, dragon.SPILLING_RED) == 2 and count(p.field, dragon.VORLALAI) == 1
    assert Attack(saga.uid, leader_uid(1)) in legal_actions(state)     # Storm


def test_normagdala_draw_and_heal_mode():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    set_pp(state, 0, 7)
    card = give(state, 0, dragon.NORMAGDALA)
    hand = len(p.hand)
    apply(state, PlayCard(card.uid, modes=(0,)))
    assert p.leader_hp == 13 and len(p.hand) == hand


def test_lumiore_discards_two_and_hits_all_enemies():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 8)
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    depths, vorlalai = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES), give(state, 0, dragon.VORLALAI)
    enemy = put(state, 1, demo.GIANT)
    assert plays(state, lumiore.uid) == [PlayCard(lumiore.uid, (depths.uid, vorlalai.uid))]
    apply(state, PlayCard(lumiore.uid, (depths.uid, vorlalai.uid)))
    # 4 to every enemy, then the discarded Depths deals 1 more to the leader
    assert enemy.life == 1 and state.players[1].leader_hp == 15
    assert count(p.field, dragon.VORLALAI) == 1


def test_lumiore_super_evolve_draws_three():
    state = start()
    p = state.players[0]
    p.hand.clear()
    unlock_evolution(state, 0)
    lumiore = put(state, 0, dragon.LUMIORE_AND_ARGENTE)
    apply(state, Evolve(lumiore.uid, super_=True))
    assert len(p.hand) == 3


def test_burnite_clears_the_enemy_board():
    state = start()
    giant, shield = put(state, 1, demo.GIANT), put(state, 1, demo.SHIELDBEARER)
    set_pp(state, 0, 9)
    burnite = give(state, 0, dragon.BURNITE)
    apply(state, PlayCard(burnite.uid))
    assert giant.fate == DESTROYED and shield.fate == DESTROYED


def test_burnite_crest_punishes_the_opponent():
    state = start(first=0)
    unlock_evolution(state, 0)
    burnite = put(state, 0, dragon.BURNITE)
    apply(state, Evolve(burnite.uid, super_=True))
    enemy = state.players[1]
    assert E.leader_area_card(state, 1, dragon.BURNITE_CREST) is not None
    assert E.add_to_leader_area(state, 1, dragon.BURNITE_CREST) is None   # official Q&A: no duplicates
    apply(state, EndTurn())                           # start of their turn: 2 damage
    assert enemy.leader_hp == 18
    enemy.leader_hp = 10
    E.heal_leader(state, 1, 5)                        # 15, then the crest deals 1
    resolve_queue(state)
    E.heal_leader(state, 1, 5)                        # once per turn: no second hit
    resolve_queue(state)
    assert enemy.leader_hp == 19


def test_burnite_crest_triggers_on_zero_restoration():
    """Official Q&A on the set 1 Burnite's identical crest: restoring 0 still counts."""
    state = start(first=0)
    E.add_to_leader_area(state, 1, dragon.BURNITE_CREST)
    apply(state, EndTurn())
    enemy = state.players[1]
    enemy.leader_hp = 20
    E.heal_leader(state, 1, 3)
    resolve_queue(state)
    assert enemy.leader_hp == 19


def test_erntz_unevolved_end_of_turn():
    state = start(first=0)
    p = state.players[0]
    put(state, 0, dragon.ERNTZ)
    victims = [put(state, 1, demo.GIANT) for _ in range(3)]
    p.leader_hp = 5
    apply(state, EndTurn())
    assert sum(v.fate == DESTROYED for v in victims) == 2 and p.leader_hp == 13


def test_erntz_evolved():
    state = start(first=0)
    unlock_evolution(state, 0)
    erntz = put(state, 0, dragon.ERNTZ)
    apply(state, Evolve(erntz.uid))
    assert not erntz.has(Keyword.WARD) and erntz.has(Keyword.INTIMIDATE)
    apply(state, EndTurn())
    assert state.players[1].leader_hp == 12


def test_lyria_enhanced_draws_a_big_follower_and_recovers_pp():
    state = start()
    p = state.players[0]
    p.deck.insert(0, state.new_instance(dragon.BURNITE, 0))   # the only 7+ cost follower
    set_pp(state, 0, 8)
    lyria = give(state, 0, neutral.LYRIA)
    apply(state, PlayCard(lyria.uid))
    assert p.hand[-1].defn == dragon.BURNITE and p.pp == 7
    assert lyria.has(Keyword.BARRIER)
