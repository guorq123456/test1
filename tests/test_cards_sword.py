"""Swordcraft cards beyond the Pirate Sword starter deck (sets 10009 to 10004 and Basic)."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, demo, sword
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import DESTROYED, FIELD_LIMIT, HAND_LIMIT, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution

WALL = CardDef(7901, "Wall", Craft.NEUTRAL, CardType.FOLLOWER, 5, 0, 20)   # 0/20, no ability
RUSH, WARD, STORM = Keyword.RUSH, Keyword.WARD, Keyword.STORM
BANE, DRAIN, BARRIER = Keyword.BANE, Keyword.DRAIN, Keyword.BARRIER


def can_attack(state, uid) -> bool:
    return any(isinstance(a, Attack) and a.attacker == uid for a in legal_actions(state))


def put_settled(state, player, defn, ready=True):
    """put(), then resolve the triggers it queued (listeners reacting to it entering)."""
    inst = put(state, player, defn, ready)
    resolve_queue(state)
    return inst


def play(state, defn, pp, targets=(), modes=()):
    """Give player 0 a card and play it with exactly `pp` play points."""
    set_pp(state, 0, pp)
    card = give(state, 0, defn)
    apply(state, PlayCard(card.uid, tuple(targets), tuple(modes)))
    return card


def damage_taken(*followers) -> int:
    return sum(f.max_life - f.life for f in followers)


# --- set 10009 ---------------------------------------------------------------------------

def test_phalanx_summons_warded_knights():
    for pp, knights in ((2, 1), (6, 5)):
        state = start()
        p = state.players[0]
        play(state, sword.PHALANX, pp)
        assert count(p.field, sword.STEELCLAD_KNIGHT) == knights
        assert all(f.has(WARD) for f in p.field) and p.pp == 0


def test_ferocious_commander():
    state = start()
    p = state.players[0]
    commander = play(state, sword.FEROCIOUS_COMMANDER, 5)
    knights = [f for f in p.field if f is not commander]
    assert [k.defn for k in knights] == [sword.STEELCLAD_KNIGHT] * 2
    assert all((k.atk, k.has(RUSH)) == (2, False) for k in knights) and commander.atk == 4

    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    commander = play(state, sword.FEROCIOUS_COMMANDER, 7)        # Enhance (7)
    knights = [f for f in p.field if f is not commander]
    assert all((k.atk, k.life) == (5, 2) and k.has(RUSH) for k in knights)
    assert (commander.atk, commander.life) == (7, 4)
    assert Attack(commander.uid, enemy.uid) in legal_actions(state)


# --- set 10008 ---------------------------------------------------------------------------

def test_naht_and_vince_fanfare_and_super_evolve():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    enemies = [put(state, 1, demo.GIANT) for _ in range(2)]             # 5/5
    nv = play(state, sword.NAHT_AND_VINCE, 7)
    assert count(p.field, sword.NAHTS_HENCHMAN) == 1 and [e.life for e in enemies] == [2, 2]
    apply(state, Evolve(nv.uid, super_=True))
    assert count(p.field, sword.NAHTS_HENCHMAN) == 2
    assert all(e.fate == DESTROYED for e in enemies)


def test_naht_and_vince_plain_evolve_does_not_replicate():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    nv = put(state, 0, sword.NAHT_AND_VINCE)
    enemy = put(state, 1, demo.GIANT)
    apply(state, Evolve(nv.uid))
    assert count(p.field, sword.NAHTS_HENCHMAN) == 0 and enemy.life == 5


def test_shaili_evolve_stops_an_enemy_attacking_for_a_turn():
    state = start()
    unlock_evolution(state, 0)
    shaili = put(state, 0, sword.SHAILI)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Evolve(shaili.uid, targets=(enemy.uid,)))
    apply(state, EndTurn())
    assert not can_attack(state, enemy.uid)              # opponent's turn: locked
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert can_attack(state, enemy.uid)                  # the next one: free again


def test_sasha_knights():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    sasha = play(state, sword.SASHA, 4)
    first = p.field[-1]
    assert first.defn == sword.STEELCLAD_KNIGHT and first.has(RUSH) and not first.has(WARD)
    apply(state, Evolve(sasha.uid))
    second = p.field[-1]
    assert second.defn == sword.STEELCLAD_KNIGHT and second.has(WARD) and not second.has(RUSH)


def test_katze_once_per_turn_and_gold():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    katze = put(state, 0, sword.KATZE)
    wall = put(state, 1, WALL)
    play(state, demo.FOOTMAN, 1)                          # not a spell
    assert wall.life == 20
    play(state, sword.GILDED_GOBLET, 1)
    play(state, sword.GILDED_GOBLET, 1)
    assert wall.life == 18                               # only the first spell this turn
    apply(state, EndTurn())
    apply(state, EndTurn())
    play(state, sword.GILDED_GOBLET, 1)
    assert wall.life == 16                               # again on the next turn
    apply(state, Evolve(katze.uid))
    assert p.hand[-1].defn == sword.GLITTERING_GOLD


def test_oda_nobunaga():
    state = start()
    giant, wall = put(state, 1, demo.GIANT), put(state, 1, WALL)
    oda = play(state, sword.ODA_NOBUNAGA, 10)
    assert giant.fate == DESTROYED and wall.life == 14 and oda.has(Keyword.INTIMIDATE)


def test_shared_existence():
    state = start()
    p = state.players[0]
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    play(state, sword.SHARED_EXISTENCE, 4)
    assert big.fate == DESTROYED and small.life == 2 and count(p.field, sword.WRETCH) == 0

    state = start()
    p = state.players[0]
    wall = put(state, 1, WALL)
    play(state, sword.SHARED_EXISTENCE, 6)               # Enhance (6): also 3 Wretches
    assert (wall.atk, wall.life) == (0, 10)
    wretches = [f for f in p.field if f.defn == sword.WRETCH]
    assert len(wretches) == 3 and all(w.has(RUSH) for w in wretches)


def test_okita_evolves_itself_once_super_evolution_is_unlocked():
    state = start()
    okita = play(state, sword.OKITA_SOUJI, 3)
    assert not okita.evolved

    state = start()
    unlock_evolution(state, 0)
    okita = play(state, sword.OKITA_SOUJI, 3)
    assert okita.evolved and not okita.super_evolved and (okita.atk, okita.life) == (4, 3)
    assert state.players[0].ep == 2                      # costs no evolution point


def test_okita_follower_strike():
    state = start()
    okita = put(state, 0, sword.OKITA_SOUJI)
    wall = put(state, 1, WALL)
    apply(state, Attack(okita.uid, wall.uid))
    assert wall.life == 20 - 3 - 2                       # strike once, then combat

    state = start()
    okita = put(state, 0, sword.OKITA_SOUJI)
    E.evolve(state, okita)
    wall = put(state, 1, WALL)
    apply(state, Attack(okita.uid, wall.uid))
    assert wall.life == 20 - 9 - 4                       # evolved: 3 separate hits of 3

    state = start()
    okita = put(state, 0, sword.OKITA_SOUJI)
    E.evolve(state, okita)
    angel = put(state, 1, demo.ANGEL)                    # 2/3 Barrier: blocks only the first hit
    apply(state, Attack(okita.uid, angel.uid))
    assert angel.fate == DESTROYED and okita.life == 3

    state = start()
    okita = put(state, 0, sword.OKITA_SOUJI)
    apply(state, Attack(okita.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 18              # Follower Strike only


def test_slice_of_domesticity_modes_and_all_with_two_cards():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    card = give(state, 0, sword.SLICE_OF_DOMESTICITY)
    assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}
    put(state, 0, demo.FOOTMAN)
    assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}
    put(state, 0, sword.DREAD_PIRATES_FLAG)              # amulets count as cards
    assert [a.modes for a in plays(state, card.uid)] == [(0, 1)]
    enemy = put(state, 1, demo.FOOTMAN)
    p.leader_hp = 10
    apply(state, PlayCard(card.uid, modes=(0, 1)))
    assert enemy.fate == DESTROYED and p.leader_hp == 12


def test_bunny_and_baron_rally_counts_the_summoned_copy():
    for rally, damage in ((18, 0), (19, 4)):
        state = start()
        p = state.players[0]
        p.rally = rally
        play(state, sword.BUNNY_AND_BARON, 5)
        assert count(p.field, sword.BUNNY_AND_BARON) == 2
        assert state.players[1].leader_hp == 20 - damage and p.rally == rally + 2


def test_bunny_and_baron_evolve_and_desperados_shot():
    state = start()
    p = state.players[0]
    p.hand.clear()
    unlock_evolution(state, 0)
    bb = put(state, 0, sword.BUNNY_AND_BARON)
    apply(state, Evolve(bb.uid))
    shot = p.hand[-1]
    assert shot.defn == sword.DESPERADOS_SHOT
    walls = put(state, 1, WALL), put(state, 1, WALL)
    set_pp(state, 0, 1)
    apply(state, PlayCard(shot.uid))
    assert damage_taken(*walls) == 8


def test_mars_powers_up_officers():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    enemy = put(state, 1, demo.FOOTMAN)
    mars = play(state, sword.MARS, 8)
    knights = [f for f in p.field if f.defn == sword.KNIGHT]
    assert len(knights) == 3 and all((k.atk, k.life) == (3, 1) and k.has(RUSH) for k in knights)
    assert mars.atk == 1 + 3
    assert Attack(knights[0].uid, enemy.uid) in legal_actions(state)
    apply(state, Evolve(mars.uid, super_=True))         # +3/+3, then a 4th Knight
    assert count(p.field, sword.KNIGHT) == 4 and mars.atk == 1 + 3 + 3 + 1


def test_mars_ignores_non_officers():
    state = start()
    mars = put_settled(state, 0, sword.MARS)
    footman = put_settled(state, 0, demo.FOOTMAN)
    assert mars.atk == 1 and footman.atk == 1
    knight = put_settled(state, 0, sword.STEELCLAD_KNIGHT)
    assert mars.atk == 2 and knight.atk == 4 and knight.has(RUSH)
    enemy_knight = put_settled(state, 1, sword.STEELCLAD_KNIGHT)
    assert mars.atk == 2 and enemy_knight.atk == 2


# --- set 10007 ---------------------------------------------------------------------------

def test_bombastic_bombardier_gets_cheap_on_super_evolution():
    state = start()
    unlock_evolution(state, 0)
    bomb = give(state, 0, sword.BOMBASTIC_BOMBARDIER)
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(a.uid))
    assert bomb.cost == 3                                # plain evolution: no change
    apply(state, EndTurn())
    apply(state, EndTurn())
    apply(state, Evolve(b.uid, super_=True))
    assert bomb.cost == 1
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 1)
    apply(state, PlayCard(bomb.uid, (enemy.uid,)))
    assert enemy.life == 2


def test_bombastic_bombardier_counts_effect_super_evolution():
    state = start()
    bomb = give(state, 0, sword.BOMBASTIC_BOMBARDIER)
    play(state, sword.GOLDEN_KNIGHT, 6, modes=(0,))      # super-evolves itself
    assert bomb.cost == 1


def test_high_strung_liaison():
    state = start()
    p = state.players[0]
    play(state, sword.HIGH_STRUNG_LIAISON, 3)
    assert count(p.field, sword.KNIGHT) == 1 and p.hand[-1].defn == sword.STEELCLAD_KNIGHT


def test_measured_attunement_rally_locks_the_target():
    for rally, locked in ((9, False), (10, True)):
        state = start()
        state.players[0].rally = rally
        enemy = put(state, 1, demo.GIANT)
        play(state, sword.MEASURED_ATTUNEMENT, 1, targets=(enemy.uid,))
        assert enemy.life == 2
        apply(state, EndTurn())
        assert can_attack(state, enemy.uid) == (not locked)


def test_sharp_eared_operative():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    operative = put(state, 0, sword.SHARP_EARED_OPERATIVE)
    enemy = put(state, 1, demo.GIANT)
    apply(state, Evolve(operative.uid, targets=(enemy.uid,)))
    assert enemy.life == 2
    E.destroy(state, operative)
    resolve_queue(state)
    assert count(p.field, sword.KNIGHT) == 1


def test_metronomic_medic():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    hand = len(p.hand)
    medic = play(state, sword.METRONOMIC_MEDIC, 5)
    assert len(p.hand) == hand + 2 and count(p.field, sword.KNIGHT) == 2
    enemy = put(state, 1, demo.GIANT)
    apply(state, Evolve(medic.uid, targets=(enemy.uid,)))
    assert enemy.life == 2


def test_knellclaw_lieutenant_modes():
    for mode in (0, 1):
        state = start()
        p = state.players[0]
        ally = put(state, 0, demo.FOOTMAN)               # 1/2
        lieutenant = play(state, sword.KNELLCLAW_LIEUTENANT, 5, modes=(mode,))
        knights = [f for f in p.field if f.defn == sword.KNIGHT]
        assert len(knights) == 3
        if mode == 0:
            assert (ally.atk, ally.life) == (2, 2) and ally.has(RUSH)
            assert all((k.atk, k.life) == (2, 1) and k.has(RUSH) for k in knights)
        else:
            assert (ally.atk, ally.life) == (1, 3) and ally.has(WARD)
            assert all((k.atk, k.life) == (1, 2) and k.has(WARD) for k in knights)
        assert (lieutenant.atk, lieutenant.life) == (3, 2)
        assert not lieutenant.has(RUSH) and not lieutenant.has(WARD)


def test_caesura_al_fine():
    for rally, splash in ((9, 0), (10, 3)):
        state = start()
        p = state.players[0]
        for _ in range(3):
            put(state, 0, demo.FOOTMAN)
        p.rally = rally
        target, other = put(state, 1, WALL), put(state, 1, WALL)
        play(state, sword.CAESURA_AL_FINE, 3, targets=(target.uid,))
        assert target.life == 20 - 6 - splash and other.life == 20 - splash


def test_gildaria_gives_rush_during_your_turn():
    state = start()
    p = state.players[0]
    p.rally = 0
    gildaria = play(state, sword.GILDARIA, 4)
    assert not gildaria.evolved and E.leader_area_card(state, 0, sword.GILDARIA_CREST) is None
    play(state, sword.PHALANX, 2)
    knight = p.field[-1]
    assert knight.has(RUSH) and knight.has(WARD)
    apply(state, EndTurn())
    late = put_settled(state, 0, sword.STEELCLAD_KNIGHT)     # during the opponent's turn
    assert not late.has(RUSH)


def test_gildaria_rally_twenty_crest_and_evolution():
    state = start()
    p = state.players[0]
    p.rally = 20
    gildaria = play(state, sword.GILDARIA, 4)
    assert gildaria.evolved and (gildaria.atk, gildaria.life) == (6, 6) and p.ep == 2
    knights = [f for f in p.field if f.defn == sword.STEELCLAD_KNIGHT]
    assert len(knights) == 2 and all(k.has(RUSH) for k in knights)
    assert state.players[1].leader_hp == 18             # the crest: 1 damage per Knight
    assert E.leader_area_card(state, 0, sword.GILDARIA_CREST).countdown == 1
    apply(state, EndTurn())
    put_settled(state, 0, sword.STEELCLAD_KNIGHT)        # opponent's turn: no damage
    assert state.players[1].leader_hp == 18
    apply(state, EndTurn())
    assert E.leader_area_card(state, 0, sword.GILDARIA_CREST) is None


def test_gildaria_point_evolution_summons_knights():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    gildaria = put(state, 0, sword.GILDARIA)
    apply(state, Evolve(gildaria.uid))
    knights = [f for f in p.field if f.defn == sword.STEELCLAD_KNIGHT]
    assert len(knights) == 2 and all(k.has(RUSH) for k in knights)


def test_cesar_fanfare_buffs_other_swordcraft_followers():
    state = start()
    p = state.players[0]
    blade = put(state, 0, sword.FLASHSTEP_QUICKBLADER)  # Swordcraft 1/1
    footman = put(state, 0, demo.FOOTMAN)               # Neutral 1/2
    cesar = play(state, sword.CESAR, 7)
    knights = [f for f in p.field if f.defn == sword.STEELCLAD_KNIGHT]
    assert len(knights) == 2 and all((k.atk, k.life) == (3, 5) and k.has(WARD) for k in knights)
    assert (blade.atk, blade.life) == (2, 4) and blade.has(WARD)
    assert (footman.atk, footman.life) == (1, 2) and not footman.has(WARD)
    assert (cesar.atk, cesar.life) == (5, 7)


def test_cesar_super_evolve_destroys():
    for super_, destroyed in ((False, False), (True, True)):
        state = start()
        unlock_evolution(state, 0)
        cesar = put(state, 0, sword.CESAR)
        enemy = put(state, 1, WALL)
        apply(state, Evolve(cesar.uid, super_=super_, targets=(enemy.uid,)))
        assert (enemy.fate == DESTROYED) == destroyed


# --- set 10006 ---------------------------------------------------------------------------

def test_fearless_soldier_enhance():
    for pp, stats in ((2, (2, 2)), (3, (3, 3))):
        state = start()
        soldier = play(state, sword.FEARLESS_SOLDIER, pp)
        assert (soldier.atk, soldier.life) == stats and soldier.has(RUSH)


def test_idle_maid_returns_a_card_and_draws_swordcraft_followers():
    deck = [demo.FOOTMAN] * 30 + [sword.OPEN_SEA_SCOUT] * 10
    state = start(deck=deck)
    p = state.players[0]
    p.hand.clear()
    junk = give(state, 0, demo.FOOTMAN)
    deck_size = len(p.deck)
    play(state, sword.IDLE_MAID, 4, targets=(junk.uid,))
    assert any(c is junk for c in p.deck)
    assert [c.defn for c in p.hand] == [sword.OPEN_SEA_SCOUT] * 2
    assert len(p.deck) == deck_size + 1 - 2


def test_way_of_the_maid_returned_card_keeps_its_effects():
    """Official Q&A: a Rusty given Storm keeps it after going back to the deck."""
    state = start()
    p = state.players[0]
    p.hand.clear()
    rusty = give(state, 0, sword.RUSTY)
    E.give_keywords(rusty, STORM)
    play(state, sword.WAY_OF_THE_MAID, 2, targets=(rusty.uid,))
    assert p.hand == [rusty] and rusty.has(STORM)        # the only Swordcraft follower there


def test_way_of_the_maid_needs_another_card():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 2)
    way = give(state, 0, sword.WAY_OF_THE_MAID)
    assert plays(state, way.uid) == []


def test_advent_of_the_eld_sword():
    for pp, stats in ((5, (2, 2)), (7, (4, 4))):
        state = start()
        p = state.players[0]
        play(state, sword.ADVENT_OF_THE_ELD_SWORD, pp)
        soldiers = [f for f in p.field if f.defn == sword.FEARLESS_SOLDIER]
        assert len(soldiers) == 3 and all((s.atk, s.life) == stats for s in soldiers)


def test_loyal_guard():
    for pp, stats in ((3, (3, 3)), (4, (5, 5))):
        state = start()
        guard = play(state, sword.LOYAL_GUARD, pp)
        assert (guard.atk, guard.life) == stats and guard.has(WARD)
    unlock_evolution(state, 0)
    enemy = put(state, 1, demo.GIANT)
    apply(state, Evolve(guard.uid, targets=(enemy.uid,)))
    assert enemy.life == 2


def test_navy_cat_destroys_one_defense_enemies():
    state = start()
    raider, footman = put(state, 1, demo.RAIDER), put(state, 1, demo.FOOTMAN)   # 2/1, 1/2
    hurt = put(state, 1, demo.GIANT)
    hurt.life = 1
    cat = play(state, sword.NAVY_CAT, 8)
    assert raider.fate == DESTROYED and hurt.fate == DESTROYED and footman.life == 2
    assert Attack(cat.uid, leader_uid(1)) in legal_actions(state)


def test_majestic_conquest_crest_summons_on_enhanced_cards():
    state = start()
    p = state.players[0]
    play(state, sword.MAJESTIC_CONQUEST, 1)
    crest = E.leader_area_card(state, 0, sword.MAJESTIC_CONQUEST_CREST)
    assert crest.countdown == 2
    play(state, sword.FEARLESS_SOLDIER, 2)               # not Enhanced
    assert count(p.field, sword.FEARLESS_SOLDIER) == 1
    play(state, sword.FEARLESS_SOLDIER, 3)               # Enhanced: the crest adds one
    assert count(p.field, sword.FEARLESS_SOLDIER) == 3
    play(state, sword.MAJESTIC_CONQUEST, 3)              # Enhanced: delays it and triggers it
    assert crest.countdown == 4 and count(p.field, sword.FEARLESS_SOLDIER) == 4


def test_majestic_conquest_enhanced_new_crest():
    state = start()
    p = state.players[0]
    play(state, sword.MAJESTIC_CONQUEST, 3)
    assert E.leader_area_card(state, 0, sword.MAJESTIC_CONQUEST_CREST).countdown == 4
    assert count(p.field, sword.FEARLESS_SOLDIER) == 0   # gained mid-resolution: no reaction


def test_heartless_strategist():
    for pp, soldiers, left in ((4, 0, 0), (6, 1, 3)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        enemy = put(state, 1, WALL)
        play(state, sword.HEARTLESS_STRATEGIST, pp, targets=(enemy.uid,))
        assert enemy.fate == DESTROYED
        assert count(p.hand, sword.FEARLESS_SOLDIER) == soldiers and p.pp == left


def test_ruthless_eld_sword():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 1)
    card = give(state, 0, sword.RUTHLESS_ELD_SWORD)
    assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}
    set_pp(state, 0, 3)
    assert [a.modes for a in plays(state, card.uid)] == [(0, 1)]
    wall = put(state, 1, WALL)
    hand = len(p.hand)
    apply(state, PlayCard(card.uid, modes=(0, 1)))
    assert wall.life == 17 and len(p.hand) == hand       # played one, drew one


def test_noel_iv_enhance_tiers():
    mask = BANE | DRAIN | STORM
    for pp, keywords in ((6, [BANE]), (7, [BANE, DRAIN]), (8, [BANE, DRAIN, STORM])):
        state = start()
        p = state.players[0]
        play(state, sword.NOEL_IV, pp)
        soldiers = [f for f in p.field if f.defn == sword.FEARLESS_SOLDIER]
        assert [s.keywords & mask for s in soldiers] == keywords
        assert all((s.atk, s.life) == (2, 2) and s.has(RUSH) for s in soldiers) and p.pp == 0


def test_noel_iv_super_evolve():
    state = start()
    unlock_evolution(state, 0)
    noel = put(state, 0, sword.NOEL_IV)
    ally = put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(noel.uid, super_=True))
    assert (ally.atk, ally.life) == (2, 3) and (noel.atk, noel.life) == (7, 8)


# --- set 10005 ---------------------------------------------------------------------------

def test_altruistic_aristocrat():
    for discarded, healed in ((sword.GILDED_GOBLET, 6), (demo.FOOTMAN, 3)):
        state = start()
        p = state.players[0]
        p.leader_hp = 10
        junk = give(state, 0, discarded)
        play(state, sword.ALTRUISTIC_ARISTOCRAT, 6, targets=(junk.uid,))
        assert not any(c is junk for c in p.hand) and p.shadows == 1
        assert p.leader_hp == 10 + healed


def test_smoke_shrouded_beauty():
    for spells, buffed in ((1, False), (2, True)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        for _ in range(spells):
            give(state, 0, sword.GLITTERING_GOLD)
        beauty = play(state, sword.SMOKE_SHROUDED_BEAUTY, 3)
        assert ((beauty.atk, beauty.life) == (4, 4)) == buffed and beauty.has(WARD) == buffed
    unlock_evolution(state, 0)
    apply(state, Evolve(beauty.uid))
    assert count(p.hand, sword.GLITTERING_GOLD) == 3


def test_extravagance_of_the_goldbloom():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 2)
    card = give(state, 0, sword.EXTRAVAGANCE_OF_THE_GOLDBLOOM)
    give(state, 0, demo.FOOTMAN)
    assert plays(state, card.uid) == []                  # needs a spell to discard
    gold = give(state, 0, sword.GLITTERING_GOLD)
    walls = put(state, 1, WALL), put(state, 1, WALL)
    apply(state, PlayCard(card.uid, (gold.uid,)))
    assert p.shadows == 2 and damage_taken(*walls) == 6  # the Gold, then the spell itself


def test_swift_staffmaster_is_cheap_on_the_turn_it_is_drawn():
    state = start()
    p = state.players[0]
    staff = state.new_instance(sword.SWIFT_STAFFMASTER, 0)
    p.deck.append(staff)                                 # top of the deck
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert p.hand[-1] is staff and staff.cost == 3
    p.leader_hp = 10
    hand = len(p.hand)
    set_pp(state, 0, 3)
    apply(state, PlayCard(staff.uid))
    assert p.leader_hp == 13 and len(p.hand) == hand and staff.has(RUSH)

    late = state.new_instance(sword.SWIFT_STAFFMASTER, 0)
    p.deck.append(late)
    E.draw(state, 0)
    resolve_queue(state)
    assert late.cost == 3
    apply(state, EndTurn())
    assert late.cost == 6
    assert give(state, 0, sword.SWIFT_STAFFMASTER).cost == 6   # added, not drawn


def test_amphibian_goldmuncher():
    for spells, hit in ((1, False), (2, True)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        put(state, 0, sword.AMPHIBIAN_GOLDMUNCHER)
        wall = put(state, 1, WALL)
        for _ in range(spells):
            give(state, 0, sword.GLITTERING_GOLD)
        apply(state, EndTurn())
        assert wall.life == (15 if hit else 20)
    unlock_evolution(state, 1)
    state.players[1].hand.clear()
    muncher = put(state, 1, sword.AMPHIBIAN_GOLDMUNCHER)
    apply(state, Evolve(muncher.uid))
    assert count(state.players[1].hand, sword.GLITTERING_GOLD) == 2


def test_amphibian_goldmuncher_ignores_unkei_crest_gold():
    """Official Q&A: Crest: Unkei and 1 spell in hand: Goldmuncher doesn't activate."""
    state = start()
    p = state.players[0]
    p.hand.clear()
    put(state, 0, sword.AMPHIBIAN_GOLDMUNCHER)
    E.add_to_leader_area(state, 0, sword.UNKEI_CREST)
    wall = put(state, 1, WALL)
    give(state, 0, sword.GLITTERING_GOLD)
    apply(state, EndTurn())
    assert count(p.hand, sword.GLITTERING_GOLD) == 2 and wall.life == 20
    apply(state, EndTurn())
    apply(state, EndTurn())                              # now 2 Golds were already in hand
    assert wall.life == 15


def test_serenitys_shield():
    for pp, knights in ((2, 2), (4, 4)):
        state = start()
        play(state, sword.SERENITYS_SHIELD, pp)
        assert count(state.players[0].field, sword.KNIGHT) == knights


def test_unmoving_tactician():
    state = start()
    p = state.players[0]
    tactician = put(state, 0, sword.UNMOVING_TACTICIAN)
    put(state, 1, demo.FOOTMAN)
    assert not can_attack(state, tactician.uid)
    apply(state, EndTurn())
    assert count(p.field, sword.STEELCLAD_KNIGHT) == 1
    apply(state, EndTurn())
    unlock_evolution(state, 0)
    apply(state, Evolve(tactician.uid, super_=True))
    knight = p.field[-1]
    assert (knight.atk, knight.life) == (5, 5) and (tactician.atk, tactician.life) == (8, 9)
    assert not can_attack(state, tactician.uid)


def test_oluon_unevolved_hits_all_enemy_followers():
    state = start()
    put(state, 0, sword.OLUON)
    walls = put(state, 1, WALL), put(state, 1, WALL)
    apply(state, EndTurn())
    assert [w.life for w in walls] == [13, 13] and state.players[1].leader_hp == 20


def test_oluon_evolved_hits_three_random_targets():
    """Official Q&A: each hit picks among the remaining followers and both leaders."""
    leaders_hit = set()
    for seed in range(30):
        state = start(seed=seed)
        p0, p1 = state.players
        oluon = put(state, 0, sword.OLUON)
        E.evolve(state, oluon)
        fairies = [put(state, 1, demo.FOOTMAN) for _ in range(3)]
        resolve_queue(state)
        apply(state, EndTurn())
        destroyed = sum(f.fate == DESTROYED for f in fairies)
        own, enemy = (20 - p0.leader_hp) // 7, (20 - p1.leader_hp) // 7
        assert destroyed + own + enemy == 3 and oluon.life == 9
        leaders_hit |= {side for side, n in ((0, own), (1, enemy)) if n}
    assert leaders_hit == {0, 1}


# --- set 10000 (Basic) -------------------------------------------------------------------

def test_arms_peddler_last_words_draws():
    state = start()
    p = state.players[0]
    peddler = put(state, 0, sword.ARMS_PEDDLER)
    hand = len(p.hand)
    E.destroy(state, peddler)
    resolve_queue(state)
    assert len(p.hand) == hand + 1


def test_royal_coachwoman_last_words_summons_a_knight():
    state = start()
    p = state.players[0]
    coachwoman = put(state, 0, sword.ROYAL_COACHWOMAN)
    E.destroy(state, coachwoman)
    resolve_queue(state)
    assert [f.defn for f in p.field] == [sword.KNIGHT]


def test_rusty_super_evolve_draws_every_rusty_with_storm():
    for super_, drawn in ((False, 0), (True, 2)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        for i in (0, 10):
            p.deck.insert(i, state.new_instance(sword.RUSTY, 0))
        unlock_evolution(state, 0)
        rusty = put(state, 0, sword.RUSTY)
        apply(state, Evolve(rusty.uid, super_=super_))
        rustys = [c for c in p.hand if c.defn == sword.RUSTY]
        assert len(rustys) == drawn and all(c.has(STORM) for c in rustys)
        assert count(p.deck, sword.RUSTY) == 2 - drawn


def test_ancestral_crown():
    state = start()
    crown = play(state, sword.ANCESTRAL_CROWN, 4)
    assert crown.countdown == 4
    footman = play(state, demo.FOOTMAN, 1)
    assert (footman.atk, footman.life) == (2, 3)
    play(state, sword.SERENITYS_SHIELD, 2)
    assert [(k.atk, k.life) for k in state.players[0].field if k.defn == sword.KNIGHT] == [(2, 2)] * 2
    enemy = put_settled(state, 1, demo.FOOTMAN)
    assert (enemy.atk, enemy.life) == (1, 2)


# --- set 10004 ---------------------------------------------------------------------------

def test_randall_enhance_storm():
    for pp, storm in ((2, False), (5, True)):
        state = start()
        randall = play(state, sword.RANDALL, pp)
        assert randall.has(STORM) == storm
        assert (Attack(randall.uid, leader_uid(1)) in legal_actions(state)) == storm


def test_arthur_and_mordred_summon_each_other():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    arthur = put(state, 0, sword.ARTHUR)
    apply(state, Evolve(arthur.uid))
    mordred = p.field[-1]
    assert mordred.defn == sword.MORDRED and mordred.has(STORM)
    apply(state, EndTurn())
    apply(state, EndTurn())
    apply(state, Evolve(mordred.uid))
    assert p.field[-1].defn == sword.ARTHUR and p.field[-1].has(WARD)


def test_aglovale():
    state = start()
    giant, wall = put(state, 1, demo.GIANT), put(state, 1, WALL)
    play(state, sword.AGLOVALE, 6)
    assert giant.life == 2 and wall.life == 17


def test_knightly_ardor_attack_twice_goes_to_the_leftmost_swordcraft_follower():
    state = start()
    footman = put(state, 0, demo.FOOTMAN)
    first = put(state, 0, sword.FLASHSTEP_QUICKBLADER)
    second = put(state, 0, sword.FLASHSTEP_QUICKBLADER)
    play(state, sword.KNIGHTLY_ARDOR, 5, modes=(0,))
    assert (footman.max_attacks, first.max_attacks, second.max_attacks) == (1, 2, 1)
    hit = Attack(first.uid, leader_uid(1))
    apply(state, hit)
    assert hit in legal_actions(state)
    apply(state, hit)
    assert hit not in legal_actions(state)
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert first.max_attacks == 2                        # permanent


def test_knightly_ardor_other_modes():
    state = start()
    p = state.players[0]
    footman = put(state, 0, demo.FOOTMAN)
    blade = put(state, 0, sword.FLASHSTEP_QUICKBLADER)
    play(state, sword.KNIGHTLY_ARDOR, 5, modes=(1,))
    assert (blade.atk, blade.life) == (2, 2) and blade.has(BARRIER)
    assert (footman.atk, footman.life) == (1, 2) and not footman.has(BARRIER)

    p.ep = 0
    play(state, sword.KNIGHTLY_ARDOR, 5, modes=(2,))
    assert p.pp == 2 and p.ep == 1

    p.leader_hp = 10
    play(state, sword.KNIGHTLY_ARDOR, 5, modes=(3,))
    assert p.leader_hp == 16


def test_seofon_skybound_art():
    for turns, evolved, super_ in ((9, False, False), (10, True, False), (15, True, True)):
        state = start()
        p = state.players[0]
        ally = put(state, 0, demo.FOOTMAN)
        p.turns_taken = turns
        seofon = play(state, sword.SEOFON, 4)
        for f in (ally, seofon):
            assert (f.evolved, f.super_evolved) == (evolved, super_)
        assert (p.ep, p.sep) == (2, 2)


def test_seofon_gauge_counts_evolutions_in_hand():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)                           # 8 turns
    p.turns_taken = 9
    seofon = give(state, 0, sword.SEOFON)
    ally = put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(ally.uid))                       # gauge 9 + 1
    other = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 4)
    apply(state, PlayCard(seofon.uid))
    assert other.evolved and seofon.evolved and not seofon.super_evolved


# --- fuzz ------------------------------------------------------------------------------

def random_sword_deck(rng: random.Random) -> list:
    """A legal 40-card deck of Swordcraft and Neutral cards that are scripted or need no script."""
    no_script = {c.card_id for c in sword.NO_SCRIPT}
    usable = [c for c in collectible(Craft.SWORD) if has_script(c.card_id) or c.card_id in no_script]
    deck = []
    while len(deck) < decks.DECK_SIZE:
        c = rng.choice(usable)
        if deck.count(c) < decks.MAX_COPIES:
            deck.append(c)
    return deck


def check_invariants(state, action):
    assert not state.queue
    for p in state.players:
        assert len(p.field) <= FIELD_LIMIT and len(p.hand) <= HAND_LIMIT
        assert p.leader_hp <= p.leader_max_hp and 0 <= p.pp <= p.max_pp + 1
        assert all(c.life > 0 for c in p.followers), action


def test_random_swordcraft_decks_play_out():
    for g in range(100):
        rng = random.Random(g)
        deck0, deck1 = random_sword_deck(rng), random_sword_deck(rng)
        assert decks.validate(deck0, Craft.SWORD) == [] and decks.validate(deck1, Craft.SWORD) == []
        state = new_game(deck0, deck1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        winner = play_game(state, agents, on_action=check_invariants)
        assert state.over and winner in (0, 1, -1)
