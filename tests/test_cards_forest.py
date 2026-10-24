"""Forestcraft cards, their tokens, crests and faith."""
import importlib
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import demo, forest
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution
from test_fuzz import check_invariants

importlib.import_module("svsim.cards.neutral")     # register the neutral scripts for the fuzz decks


def fresh(first: int = 0, deck=None, deck1=None):
    """A started game with an empty hand for player 0."""
    state = start(first=first, deck=deck, deck1=deck1)
    state.players[0].hand.clear()
    return state


def play(state, card, targets=(), modes=()):
    apply(state, PlayCard(card.uid, tuple(targets), tuple(modes)))


def enemy_hp(state, player: int = 1) -> int:
    return state.players[player].leader_hp


# --- tokens --------------------------------------------------------------------------------

def test_springbloom_fairy_evolves_at_end_of_turn():
    state = fresh()
    fairy = put(state, 0, forest.SPRINGBLOOM_FAIRY)
    assert fairy.has(Keyword.WARD)
    apply(state, EndTurn())
    assert fairy.evolved and (fairy.atk, fairy.life) == (3, 3)
    assert state.players[0].ep == 2                       # an effect evolution costs no points


def test_deepwood_bounty_restores_one():
    state = fresh()
    state.players[0].leader_hp = 15
    bounty = give(state, 0, forest.DEEPWOOD_BOUNTY)
    set_pp(state, 0, 0)
    play(state, bounty)
    assert state.players[0].leader_hp == 16


def test_depths_of_the_eld_lance_evolves_an_unevolved_ally_without_evolve_abilities():
    state = fresh(deck=[demo.FOOTMAN] * 40)
    p = state.players[0]
    tanuki = put(state, 0, forest.PRUDENT_TANUKI)
    done = put(state, 0, demo.FOOTMAN)
    E.evolve(state, done)
    depths = give(state, 0, forest.DEPTHS_OF_THE_ELD_LANCE)
    set_pp(state, 0, 1)
    assert plays(state, depths.uid) == [PlayCard(depths.uid, (tanuki.uid,))]
    play(state, depths, [tanuki.uid])
    assert tanuki.evolved and len(p.hand) == 0             # Tanuki's "Evolve: draw" doesn't fire


# --- leader area ---------------------------------------------------------------------------

def test_starry_sky_crest_needs_combo_5_and_returns_a_starry_sky():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    sky = give(state, 0, forest.STARRY_SKY)
    set_pp(state, 0, 1)
    p.combo = 4
    play(state, sky)
    assert enemy.life == 3
    crest = E.leader_area_card(state, 0, forest.STARRY_SKY_CREST)
    assert crest is not None and crest.countdown == 1
    apply(state, EndTurn())
    apply(state, EndTurn())                                # countdown runs out: Last Words
    assert E.leader_area_card(state, 0, forest.STARRY_SKY_CREST) is None
    assert enemy_hp(state) == 19 and count(p.hand, forest.STARRY_SKY) == 1


def test_starry_sky_without_combo_gains_no_crest():
    state = fresh()
    sky = give(state, 0, forest.STARRY_SKY)
    set_pp(state, 0, 1)
    play(state, sky)
    assert state.players[0].leader_area == []


def test_yuel_crest_evolves_the_first_follower_played_each_turn():
    state = fresh()
    E.add_to_leader_area(state, 0, forest.YUEL_CREST)
    a, b = give(state, 0, demo.FOOTMAN), give(state, 0, demo.FOOTMAN)
    spell = give(state, 0, forest.DEEPWOOD_BOUNTY)
    set_pp(state, 0, 5)
    play(state, spell)                                     # spells don't use it up
    play(state, a)
    play(state, b)
    assert a.evolved and not b.evolved


def test_sathanid_faith_counts_evolutions_and_sathanid_spends_it():
    deck = [forest.SATHANID] + [demo.FOOTMAN] * 39
    state = start(first=0, deck=deck)
    p = state.players[0]
    faith = E.leader_area_card(state, 0, forest.SATHANID_FAITH)
    assert faith is not None                               # placed at match start
    for _ in range(3):
        E.evolve(state, put(state, 0, demo.FOOTMAN))
    resolve_queue(state)
    assert E.faith_value(state, 0, forest.SATHANID_FAITH) == 3
    p.hand.clear()
    sathanid = give(state, 0, forest.SATHANID)
    set_pp(state, 0, 3)
    play(state, sathanid)                                  # not enough faith: nothing
    assert p.hand == [] and E.faith_value(state, 0, forest.SATHANID_FAITH) == 3
    E.change_faith(state, 0, forest.SATHANID_FAITH, 8)     # 11
    p.field.clear()
    second = give(state, 0, forest.SATHANID)
    play(state, second)
    assert E.faith_value(state, 0, forest.SATHANID_FAITH) == 1
    depths = p.hand[-1]
    assert depths.defn == forest.DEPTHS_OF_THE_ELD_LANCE
    assert second.has(Keyword.DRAIN)
    play(state, depths, [second.uid])                      # the evolution pings the enemy leader
    assert enemy_hp(state) == 19 and E.faith_value(state, 0, forest.SATHANID_FAITH) == 2


def test_minimized_anxiety_and_magnified_malice_cycle_through_crests():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    anxiety = give(state, 0, forest.MINIMIZED_ANXIETY)
    set_pp(state, 0, 1)
    p.combo = 2
    play(state, anxiety)
    assert p.leader_hp == 11
    assert E.leader_area_card(state, 0, forest.MINIMIZED_ANXIETY_CREST) is not None
    apply(state, EndTurn())
    apply(state, EndTurn())
    malice = [c for c in p.hand if c.defn == forest.MAGNIFIED_MALICE]
    assert len(malice) == 1 and p.leader_area == []
    enemy = put(state, 1, demo.GIANT)
    p.combo = 2
    play(state, malice[0])
    assert enemy.life == 3
    assert E.leader_area_card(state, 0, forest.MAGNIFIED_MALICE_CREST) is not None
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert count(p.hand, forest.MINIMIZED_ANXIETY) == 1


def test_thestae_crest_buffs_followers_in_the_deck_with_combo():
    state = fresh()
    p = state.players[0]
    E.add_to_leader_area(state, 0, forest.THESTAE_CREST)
    apply(state, EndTurn())                                # combo 0: nothing
    assert all((c.atk, c.life) == (1, 2) for c in p.deck if c.defn == demo.FOOTMAN)
    apply(state, EndTurn())
    spell = E.put_into_deck(state, 0, forest.DEEPWOOD_BOUNTY)
    p.combo = 3
    apply(state, EndTurn())
    assert all((c.atk, c.life) == (2, 3) for c in p.deck if c.defn == demo.FOOTMAN)
    assert spell in p.deck and (spell.atk, spell.life) == (0, 0)     # only followers


def test_great_hart_crest_adds_deepwood_bounty_with_combo():
    state = fresh()
    p = state.players[0]
    E.add_to_leader_area(state, 0, forest.GREAT_HART_CREST)
    p.combo = 3
    apply(state, EndTurn())
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 1


# --- set 10009 -------------------------------------------------------------------------------

def test_sprouting_initiate_combo_draw():
    state = fresh()
    p = state.players[0]
    a, b = give(state, 0, forest.SPROUTING_INITIATE), give(state, 0, forest.SPROUTING_INITIATE)
    set_pp(state, 0, 2)
    play(state, a)
    assert len(p.hand) == 1
    p.combo = 2
    play(state, b)
    assert len(p.hand) == 1 and p.hand[0].defn == demo.FOOTMAN    # drew a card
    assert b.has(Keyword.RUSH)


def test_trap_in_the_woods_destroys_the_entering_follower_and_itself():
    state = fresh(first=0)
    trap = put(state, 0, forest.TRAP_IN_THE_WOODS)
    apply(state, EndTurn())
    footman = give(state, 1, demo.FOOTMAN)
    play(state, footman)
    assert footman.fate == DESTROYED and trap.fate == DESTROYED


def test_trap_in_the_woods_only_hits_the_first_of_several_followers():
    """Official Q&A: followers summoned at once - only the first is destroyed."""
    state = fresh(first=0)
    trap = put(state, 0, forest.TRAP_IN_THE_WOODS)
    apply(state, EndTurn())
    advent = give(state, 1, forest.ADVENT_OF_THE_ELD_LANCE)
    set_pp(state, 1, 7)
    play(state, advent)
    fairies = [c for c in state.players[1].field if c.defn == forest.SPRINGBLOOM_FAIRY]
    assert trap.fate == DESTROYED and len(fairies) == 1


def test_leafshadow_assassin_fairy_gets_bane_with_combo():
    state = fresh()
    p = state.players[0]
    a, b = give(state, 0, forest.LEAFSHADOW_ASSASSIN), give(state, 0, forest.LEAFSHADOW_ASSASSIN)
    set_pp(state, 0, 4)
    play(state, a)
    first = p.hand[-1]
    assert first.defn == forest.FAIRY and not first.has(Keyword.BANE)
    p.combo = 2
    play(state, b)
    assert p.hand[-1].has(Keyword.BANE | Keyword.RUSH)


def test_primate_plotters_copies_a_random_opponent_hand_card():
    state = fresh()
    p = state.players[0]
    opp = state.players[1]
    opp.hand.clear()
    give(state, 1, forest.HIEN)
    plotters = give(state, 0, forest.PRIMATE_PLOTTERS)
    set_pp(state, 0, 3)
    play(state, plotters)
    assert [c.defn for c in p.hand] == [forest.HIEN] and p.hand[0].owner == 0
    assert len(opp.hand) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(plotters.uid))
    assert count(p.hand, forest.HIEN) == 2


def test_verdant_ring_kindred_modes_and_combo_all():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    kindred = give(state, 0, forest.VERDANT_RING_KINDRED)
    set_pp(state, 0, 4)
    assert {a.modes for a in plays(state, kindred.uid)} == {(0,), (1,)}
    play(state, kindred, modes=(1,))
    assert [c.defn for c in p.hand] == [forest.DEEPWOOD_BOUNTY, forest.FAIRY] and enemy.life == 5
    p.hand.clear()
    second = give(state, 0, forest.VERDANT_RING_KINDRED)
    p.combo = 2
    assert [a.modes for a in plays(state, second.uid)] == [(0, 1)]
    play(state, second, modes=(0, 1))
    assert enemy.life == 1 and len(p.hand) == 2


def test_virid_lieutenant_combo_draw_and_evolve_buff():
    state = fresh()
    p = state.players[0]
    ally = put(state, 0, demo.FOOTMAN)
    lieutenant = give(state, 0, forest.VIRID_LIEUTENANT)
    set_pp(state, 0, 2)
    p.combo = 2
    play(state, lieutenant)
    assert len(p.hand) == 2
    unlock_evolution(state, 0)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == lieutenant.uid]
    assert {a.targets for a in evolves} == {(ally.uid,)}           # "another" allied follower
    apply(state, Evolve(lieutenant.uid, False, (ally.uid,)))
    assert (ally.atk, ally.life) == (2, 3) and ally.has(Keyword.RUSH)


def test_crimson_incense_gets_cheaper_at_end_of_turn_with_combo_and_destroys():
    state = fresh()
    p = state.players[0]
    incense = give(state, 0, forest.CRIMSON_INCENSE)
    apply(state, EndTurn())
    assert incense.cost == 4
    apply(state, EndTurn())
    p.combo = 3
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert incense.cost == 3
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    hand = len(p.hand)
    play(state, incense, [enemy.uid])
    assert enemy.fate == DESTROYED and len(p.hand) == hand        # -1 played, +1 drawn


def test_magachiyo_single_target_or_all_with_combo():
    state = fresh()
    p = state.players[0]
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    first = give(state, 0, forest.MAGACHIYO)
    set_pp(state, 0, 6)
    assert {x.targets for x in plays(state, first.uid)} == {(a.uid,), (b.uid,)}
    play(state, first, [a.uid])
    assert (a.life, b.life) == (1, 5)
    second = give(state, 0, forest.MAGACHIYO)
    p.combo = 2
    assert [x.targets for x in plays(state, second.uid)] == [()]  # no selection with Combo (3)
    play(state, second)
    assert a.fate == DESTROYED and b.life == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(second.uid, True))
    assert second.has(Keyword.STORM)
    assert Attack(second.uid, leader_uid(1)) in legal_actions(state)


def test_hien_cost_drops_per_card_played_this_turn_then_resets():
    state = fresh()
    p = state.players[0]
    hien = give(state, 0, forest.HIEN)
    for _ in range(3):
        give(state, 0, forest.DEEPWOOD_BOUNTY)
    set_pp(state, 0, 6)
    for bounty in [c for c in p.hand if c.defn == forest.DEEPWOOD_BOUNTY]:
        play(state, bounty)
    assert hien.cost == 6
    enemy = put(state, 1, demo.GIANT)
    play(state, hien, [enemy.uid])
    assert enemy.life == 1 and p.pp == 0
    E.destroy(state, hien)
    resolve_queue(state)
    assert count(p.field, forest.HIEN) == 1                       # Last Words: summon a Hien


def test_hien_reduction_expires_at_end_of_turn():
    state = fresh()
    p = state.players[0]
    hien = give(state, 0, forest.HIEN)
    bounty = give(state, 0, forest.DEEPWOOD_BOUNTY)
    play(state, bounty)
    assert hien.cost == 8
    apply(state, EndTurn())
    assert hien.cost == 9 and hien in p.hand


# --- set 10008 -------------------------------------------------------------------------------

def test_marlone_qa_five_fairies_and_no_allies_destroys_four():
    """Official Q&A: 5 enemy Fairies, no allied followers -> X = 4 (Marlone counts)."""
    state = fresh()
    for _ in range(5):
        put(state, 1, forest.FAIRY)
    marlone = give(state, 0, forest.MARLONE)
    set_pp(state, 0, 7)
    play(state, marlone)
    assert len(state.players[1].followers) == 1


def test_marlone_does_nothing_when_allies_outnumber():
    state = fresh()
    put(state, 0, demo.FOOTMAN)
    put(state, 1, demo.FOOTMAN)
    marlone = give(state, 0, forest.MARLONE)
    set_pp(state, 0, 7)
    play(state, marlone)
    assert len(state.players[1].followers) == 1


def test_citrus_summons_fairies_and_again_on_evolve():
    state = fresh()
    citrus = give(state, 0, forest.CITRUS)
    set_pp(state, 0, 3)
    play(state, citrus)
    assert count(state.players[0].field, forest.FAIRY) == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(citrus.uid))
    assert count(state.players[0].field, forest.FAIRY) == 4


def test_moelle_returns_a_card_to_the_deck_and_draws():
    state = fresh()
    p = state.players[0]
    hart = give(state, 0, forest.GREAT_HART)
    moelle = give(state, 0, forest.MOELLE)
    set_pp(state, 0, 1)
    deck = len(p.deck)
    play(state, moelle, [hart.uid])
    assert len(p.hand) == 1 and len(p.deck) == deck              # +1 to deck, -1 drawn
    assert moelle.has(Keyword.WARD)


def test_ruflet_summons_a_fairy_once_per_own_turn_when_buffed():
    state = fresh(first=0)
    p = state.players[0]
    ruflet = put(state, 0, forest.RUFLET)
    E.buff(state, ruflet, 1, 0)
    resolve_queue(state)
    E.buff(state, ruflet, 0, 1)
    resolve_queue(state)
    assert count(p.field, forest.FAIRY) == 1
    E.buff(state, ruflet, 0, -1)                                  # a debuff isn't "given +"
    apply(state, EndTurn())
    E.buff(state, ruflet, 1, 1)                                   # opponent's turn: no
    resolve_queue(state)
    assert count(p.field, forest.FAIRY) == 1
    E.destroy(state, ruflet)
    resolve_queue(state)
    assert count(p.hand, forest.FAIRY) == 1                       # Last Words


def test_lycoris_and_michelle_summon_each_other():
    state = fresh()
    p = state.players[0]
    lycoris = give(state, 0, forest.LYCORIS)
    set_pp(state, 0, 10)
    play(state, lycoris)
    assert [c.defn for c in p.field] == [forest.LYCORIS, forest.MICHELLE]
    assert lycoris.has(Keyword.RUSH | Keyword.BANE)
    p.field.clear()
    footman = put(state, 0, demo.FOOTMAN)
    michelle = give(state, 0, forest.MICHELLE)
    play(state, michelle)
    assert [c.defn for c in p.field] == [demo.FOOTMAN, forest.MICHELLE, forest.LYCORIS]
    assert all(c.has(Keyword.BARRIER) for c in p.field) and footman.has(Keyword.BARRIER)


def test_peaceful_solitude_needs_a_target():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    solitude = give(state, 0, forest.PEACEFUL_SOLITUDE)
    set_pp(state, 0, 4)
    assert plays(state, solitude.uid) == []
    enemy = put(state, 1, demo.GIANT)
    play(state, solitude, [enemy.uid])
    assert enemy.fate == DESTROYED and p.leader_hp == 12


def test_curiosity_abounds_summons_two_different_cheap_followers_and_buffs():
    deck = [forest.FAIRY_TAMER] * 10 + [forest.MAY] * 10 + [forest.MACROBEAR] * 20
    state = fresh(deck=deck)
    p = state.players[0]
    curiosity = give(state, 0, forest.CURIOSITY_ABOUNDS)
    set_pp(state, 0, 5)
    play(state, curiosity)
    assert sorted(c.defn.name for c in p.field) == sorted([forest.FAIRY_TAMER.name, forest.MAY.name])
    assert all(c.atk == c.defn.atk + 1 and c.life == c.defn.life + 1 for c in p.field)


def test_setus_and_maisha_destroys_and_buffs_others():
    state = fresh()
    ally = put(state, 0, demo.FOOTMAN)
    enemy = put(state, 1, demo.GIANT)
    setus = give(state, 0, forest.SETUS_AND_MAISHA)
    set_pp(state, 0, 7)
    play(state, setus, [enemy.uid])
    assert enemy.fate == DESTROYED and (ally.atk, ally.life) == (2, 3)
    assert (setus.atk, setus.life) == (4, 6)
    assert Attack(setus.uid, leader_uid(1)) in legal_actions(state)


def test_tia_enhance_buffs_everyone_and_earns_one_eve():
    state = fresh()
    p = state.players[0]
    ally = put(state, 0, demo.FOOTMAN)
    tia = give(state, 0, forest.TIA)
    set_pp(state, 0, 4)
    play(state, tia)
    assert (ally.atk, ally.life) == (2, 3) and (tia.atk, tia.life) == (3, 3)
    assert count(p.hand, forest.EVE) == 1
    E.buff(state, tia, 1, 1)
    resolve_queue(state)
    assert count(p.hand, forest.EVE) == 1                         # once per turn
    plain = give(state, 0, forest.TIA)
    set_pp(state, 0, 2)
    play(state, plain)
    assert (plain.atk, plain.life) == (2, 2) and count(p.hand, forest.EVE) == 1


# --- set 10007 -------------------------------------------------------------------------------

def test_macrobear_copies_itself_and_caps_damage():
    state = fresh()
    p = state.players[0]
    bear = give(state, 0, forest.MACROBEAR)
    set_pp(state, 0, 8)
    play(state, bear)
    assert count(p.field, forest.MACROBEAR) == 2
    copy = p.field[1]
    assert copy is not bear and copy.has(Keyword.WARD | Keyword.RUSH)
    E.damage(state, [copy], 10)
    assert copy.life == 3


def test_elven_trapper_returns_a_card_and_adds_two_fairies():
    state = fresh()
    p = state.players[0]
    other = give(state, 0, demo.GIANT)
    trapper = give(state, 0, forest.ELVEN_TRAPPER)
    set_pp(state, 0, 1)
    play(state, trapper, [other.uid])
    assert other in p.deck and [c.defn for c in p.hand] == [forest.FAIRY, forest.FAIRY]


def test_cognitive_shift_needs_two_cards_and_cycles_them():
    state = fresh()
    p = state.players[0]
    shift = give(state, 0, forest.COGNITIVE_SHIFT)
    a = give(state, 0, forest.GREAT_HART)
    set_pp(state, 0, 1)
    assert plays(state, shift.uid) == []
    b = give(state, 0, forest.MARLONE)
    play(state, shift, [a.uid, b.uid])
    assert a in p.deck or a in p.hand
    assert len(p.hand) == 2


def test_virewind_fencer_storm_with_combo():
    state = fresh()
    p = state.players[0]
    fencer = give(state, 0, forest.VIREWIND_FENCER)
    set_pp(state, 0, 2)
    p.combo = 2
    play(state, fencer)
    assert Attack(fencer.uid, leader_uid(1)) in legal_actions(state)
    other = give(state, 0, forest.VIREWIND_FENCER)
    p.combo = 0
    set_pp(state, 0, 2)
    play(state, other)
    assert not other.has(Keyword.STORM)


def test_hawkeyed_tactician_damages_and_increases_combo():
    state = fresh()
    p = state.players[0]
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    hawk = give(state, 0, forest.HAWKEYED_TACTICIAN)
    set_pp(state, 0, 5)
    play(state, hawk, [a.uid])
    assert a.life == 1 and p.combo == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(hawk.uid, False, (b.uid,)))
    assert b.life == 1 and p.combo == 3


def test_frostbow_sniper_deals_its_attack_and_draws_with_combo():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    sniper = give(state, 0, forest.FROSTBOW_SNIPER)
    set_pp(state, 0, 3)
    play(state, sniper, [enemy.uid])
    assert enemy.life == 2
    p.combo = 3
    p.hand.clear()
    apply(state, EndTurn())
    assert len(p.hand) == 1


def test_thestae_shrinks_by_its_attack_and_evolve_gains_crest():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    thestae = give(state, 0, forest.THESTAE)
    set_pp(state, 0, 4)
    play(state, thestae, [enemy.uid])
    assert (enemy.life, enemy.max_life) == (2, 2) and p.combo == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(thestae.uid))
    crest = E.leader_area_card(state, 0, forest.THESTAE_CREST)
    assert crest is not None and crest.countdown == 3


def test_great_hart_bounties_split_damage_and_crest():
    state = fresh()
    p = state.players[0]
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)     # 1/2, 5/5
    hart = give(state, 0, forest.GREAT_HART)
    set_pp(state, 0, 6)
    play(state, hart)
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 2
    apply(state, EndTurn())                                           # 5 split: 2 then 3
    assert a.fate == DESTROYED and b.life == 2
    apply(state, EndTurn())
    unlock_evolution(state, 0)
    apply(state, Evolve(hart.uid, True))
    assert E.leader_area_card(state, 0, forest.GREAT_HART_CREST) is not None


# --- set 10006 -------------------------------------------------------------------------------

def test_motherly_forestdweller():
    state = fresh()
    p = state.players[0]
    mother = give(state, 0, forest.MOTHERLY_FORESTDWELLER)
    set_pp(state, 0, 4)
    play(state, mother)
    assert [c.defn for c in p.hand] == [forest.SPRINGBLOOM_FAIRY]
    unlock_evolution(state, 0)
    apply(state, Evolve(mother.uid))
    assert count(p.field, forest.SPRINGBLOOM_FAIRY) == 1


def test_monkey_of_paradise_evolves_with_combo_for_free():
    state = fresh()
    p = state.players[0]
    monkey = give(state, 0, forest.MONKEY_OF_PARADISE)
    set_pp(state, 0, 3)
    p.combo = 2
    play(state, monkey)
    assert monkey.evolved and (monkey.atk, monkey.life) == (5, 5) and p.ep == 2
    plain = give(state, 0, forest.MONKEY_OF_PARADISE)
    p.combo, p.pp = 0, 3
    play(state, plain)
    assert not plain.evolved


def test_advent_of_the_eld_lance_and_kindly_executor():
    state = fresh()
    p = state.players[0]
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    advent = give(state, 0, forest.ADVENT_OF_THE_ELD_LANCE)
    set_pp(state, 0, 9)
    play(state, advent)
    assert a.fate == DESTROYED and b.life == 1
    assert count(p.field, forest.SPRINGBLOOM_FAIRY) == 2
    executor = give(state, 0, forest.KINDLY_EXECUTOR)
    play(state, executor)
    assert [c.defn for c in p.hand] == [forest.SPRINGBLOOM_FAIRY]


def test_floral_offering_gets_cheaper_per_allied_evolution():
    state = fresh()
    offering = give(state, 0, forest.FLORAL_OFFERING)
    footman = put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(footman.uid))
    E.evolve(state, put(state, 0, demo.FOOTMAN))
    E.evolve(state, put(state, 1, demo.FOOTMAN))                 # enemy evolutions don't count
    resolve_queue(state)
    assert offering.cost == 3
    set_pp(state, 0, 3)
    play(state, offering)
    assert len(state.players[0].hand) == 2


def test_merciful_attendant_heals_on_every_allied_evolution():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    attendant = give(state, 0, forest.MERCIFUL_ATTENDANT)
    set_pp(state, 0, 5)
    play(state, attendant)
    fairy = p.field[-1]
    assert fairy.defn == forest.SPRINGBLOOM_FAIRY
    apply(state, EndTurn())                                       # the fairy evolves: +1
    assert fairy.evolved and p.leader_hp == 11
    apply(state, EndTurn())
    unlock_evolution(state, 0)
    apply(state, Evolve(attendant.uid))                            # itself: +1
    assert p.leader_hp == 12


def test_nurturing_eld_lance_modes():
    state = fresh()
    p = state.players[0]
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    lance = give(state, 0, forest.NURTURING_ELD_LANCE)
    set_pp(state, 0, 6)
    assert {a.modes for a in plays(state, lance.uid)} == {(0,), (1,)}
    play(state, lance, modes=(0,))
    assert big.fate == DESTROYED and small.fate == IN_PLAY
    second = give(state, 0, forest.NURTURING_ELD_LANCE)
    play(state, second, modes=(1,))
    assert count(p.field, forest.SPRINGBLOOM_FAIRY) == 1


def test_althenia_fairies_two_attacks_and_super_evolve_destroy():
    state = fresh()
    p = state.players[0]
    althenia = give(state, 0, forest.ALTHENIA)
    set_pp(state, 0, 8)
    play(state, althenia)
    assert count(p.field, forest.SPRINGBLOOM_FAIRY) == 3
    enemy = put(state, 1, demo.GIANT)
    althenia.entered_turn = -1
    unlock_evolution(state, 0)
    apply(state, Evolve(althenia.uid, True, (enemy.uid,)))
    assert enemy.fate == DESTROYED and (althenia.atk, althenia.life) == (10, 10)
    state.players[1].leader_hp = state.players[1].leader_max_hp = 30
    apply(state, Attack(althenia.uid, leader_uid(1)))
    assert Attack(althenia.uid, leader_uid(1)) in legal_actions(state)    # a second attack
    apply(state, Attack(althenia.uid, leader_uid(1)))
    assert enemy_hp(state) == 10
    assert Attack(althenia.uid, leader_uid(1)) not in legal_actions(state)


def test_althenia_evolve_targets_only_when_super_evolution_is_possible():
    state = fresh()
    althenia = put(state, 0, forest.ALTHENIA)
    enemy = put(state, 1, demo.GIANT)
    state.players[0].turns_taken = 5                              # can evolve, can't super-evolve
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == althenia.uid]
    assert evolves == [Evolve(althenia.uid, False, ())]
    unlock_evolution(state, 0)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == althenia.uid]
    assert Evolve(althenia.uid, True, (enemy.uid,)) in evolves


# --- set 10005 -------------------------------------------------------------------------------

def test_prudent_tanuki_evolve_draws():
    state = fresh()
    tanuki = put(state, 0, forest.PRUDENT_TANUKI)
    assert tanuki.has(Keyword.AMBUSH)
    unlock_evolution(state, 0)
    apply(state, Evolve(tanuki.uid))
    assert len(state.players[0].hand) == 1


def test_battledore_woodsmaiden_pings_for_each_pixie():
    state = fresh()
    maiden = give(state, 0, forest.BATTLEDORE_WOODSMAIDEN)
    fairy = give(state, 0, forest.FAIRY)
    set_pp(state, 0, 10)
    play(state, maiden)                                           # its own Fairy counts
    assert enemy_hp(state) == 19
    play(state, fairy)
    assert enemy_hp(state) == 18
    unlock_evolution(state, 0)
    apply(state, Evolve(maiden.uid))
    assert enemy_hp(state) == 17 and count(state.players[0].field, forest.FAIRY) == 3


def test_flight_of_the_swarmpetal_splits_three_and_adds_a_fairy():
    state = fresh()
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    flight = give(state, 0, forest.FLIGHT_OF_THE_SWARMPETAL)
    set_pp(state, 0, 2)
    play(state, flight)
    assert a.fate == DESTROYED and b.life == 4
    assert [c.defn for c in state.players[0].hand] == [forest.FAIRY]


def test_flowering_friendship_combo_five():
    state = fresh()
    p = state.players[0]
    friend = give(state, 0, forest.FLOWERING_FRIENDSHIP)
    set_pp(state, 0, 2)
    p.combo = 4
    play(state, friend)
    assert count(p.field, forest.FLOWERING_FRIENDSHIP) == 2
    assert all(c.evolved for c in p.field) and p.ep == 2
    lone = give(state, 0, forest.FLOWERING_FRIENDSHIP)
    p.combo, p.pp = 2, 2
    play(state, lone)
    assert count(p.field, forest.FLOWERING_FRIENDSHIP) == 3 and not lone.evolved


def test_quiet_encouragement_one_or_two_damage():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    a, b = give(state, 0, forest.QUIET_ENCOURAGEMENT), give(state, 0, forest.QUIET_ENCOURAGEMENT)
    set_pp(state, 0, 6)
    play(state, a)
    assert enemy.life == 4 and enemy_hp(state) == 19
    p.combo = 2
    play(state, b)
    assert enemy.life == 2 and enemy_hp(state) == 17


def test_spirited_skipper_fairies_and_super_evolve_bane():
    state = fresh()
    p = state.players[0]
    skipper = give(state, 0, forest.SPIRITED_SKIPPER)
    set_pp(state, 0, 5)
    play(state, skipper)
    assert count(p.field, forest.FAIRY) == 3
    unlock_evolution(state, 0)
    apply(state, Evolve(skipper.uid, True))                       # Evolve first (1 fits), then Bane
    fairies = [c for c in p.field if c.defn == forest.FAIRY]
    assert len(fairies) == 4 and all(f.has(Keyword.BANE) for f in fairies)
    assert not skipper.has(Keyword.BANE)


def test_grace_of_the_swarmpetal_draws_combo():
    state = fresh()
    p = state.players[0]
    grace = give(state, 0, forest.GRACE_OF_THE_SWARMPETAL)
    set_pp(state, 0, 3)
    p.combo = 2
    play(state, grace)
    assert len(p.hand) == 3


def test_wolfraud_grows_with_combo_and_evolve_swaps_hands():
    state = fresh(deck1=[forest.MARLONE] * 40)
    p = state.players[0]
    wolfraud = give(state, 0, forest.WOLFRAUD)
    junk = give(state, 0, demo.GIANT)
    set_pp(state, 0, 2)
    p.combo = 2
    play(state, wolfraud)
    assert (wolfraud.atk, wolfraud.life) == (4, 4)
    unlock_evolution(state, 0)
    shadows = p.shadows
    apply(state, Evolve(wolfraud.uid))
    assert junk not in p.hand and p.shadows == shadows + 1
    assert [c.defn for c in p.hand] == [forest.MARLONE] * 5 and all(c.owner == 0 for c in p.hand)
    assert len(state.players[1].deck) == 36                    # copies: the deck keeps its cards


def test_miroku_modes_and_evolve_replicates():
    state = fresh()
    p = state.players[0]
    a = put(state, 1, demo.GIANT)
    miroku = give(state, 0, forest.MIROKU)
    set_pp(state, 0, 3)
    assert {x.modes for x in plays(state, miroku.uid)} == {(0,), (1,), (2,)}
    play(state, miroku, modes=(1,))
    assert p.pp == 2
    unlock_evolution(state, 0)
    evolves = {x.modes for x in legal_actions(state) if isinstance(x, Evolve) and x.uid == miroku.uid}
    assert {(0,), (1,), (2,)} <= evolves
    apply(state, Evolve(miroku.uid, False, (), (2,)))
    assert a.life == 2
    second = give(state, 0, forest.MIROKU)
    set_pp(state, 0, 3)
    play(state, second, modes=(0,))
    assert count(p.hand, forest.FAIRY) == 2


# --- set 10004 -------------------------------------------------------------------------------

def test_kou_and_you_attacks_twice_and_heals_all_allies():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    kou = put(state, 0, forest.KOU_AND_YOU)
    ally = put(state, 0, demo.GIANT)
    ally.life = 1
    apply(state, Attack(kou.uid, leader_uid(1)))
    assert p.leader_hp == 13 and ally.life == 4
    apply(state, Attack(kou.uid, leader_uid(1)))
    assert p.leader_hp == 16 and enemy_hp(state) == 4
    assert not any(isinstance(a, Attack) and a.attacker == kou.uid for a in legal_actions(state))


def test_manamel_evolves_at_end_of_turn_and_pings():
    state = fresh()
    manamel = put(state, 0, forest.MANAMEL)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, EndTurn())
    assert manamel.evolved and enemy.life == 1


def test_manamel_pings_when_evolved_with_points():
    state = fresh()
    manamel = put(state, 0, forest.MANAMEL)
    enemy = put(state, 1, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(manamel.uid))
    assert enemy.life == 1
    apply(state, EndTurn())                                       # already evolved: nothing more
    assert enemy.life == 1


def test_comet_drive_draws_with_an_evolved_ally():
    state = fresh()
    p = state.players[0]
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    first, second = give(state, 0, forest.COMET_DRIVE), give(state, 0, forest.COMET_DRIVE)
    set_pp(state, 0, 4)
    play(state, first, [a.uid])
    assert a.life == 1 and len(p.hand) == 1
    E.evolve(state, put(state, 0, demo.FOOTMAN))
    play(state, second, [b.uid])
    assert b.life == 1 and len(p.hand) == 1                       # drew


def test_chloe_enhanced_summons_from_hand_and_returns():
    state = fresh()
    p = state.players[0]
    chloe = give(state, 0, forest.CHLOE)
    giant = give(state, 0, demo.GIANT)
    give(state, 0, forest.DEEPWOOD_BOUNTY)                       # not a follower: not offered
    set_pp(state, 0, 2)
    assert plays(state, chloe.uid) == [PlayCard(chloe.uid, ())]  # not Enhanced: no selection
    set_pp(state, 0, 8)
    assert plays(state, chloe.uid) == [PlayCard(chloe.uid, (giant.uid,))]
    play(state, chloe, [giant.uid])
    assert giant in p.field and giant.fate == IN_PLAY and p.pp == 0
    assert chloe not in p.field and count(p.hand, forest.CHLOE) == 1


def test_chloe_qa_full_field_still_returns_chloe():
    """Official Q&A: field full -> the follower can't be summoned; Chloe returns to hand."""
    state = fresh()
    p = state.players[0]
    for _ in range(4):
        put(state, 0, demo.FOOTMAN)
    chloe = give(state, 0, forest.CHLOE)
    giant = give(state, 0, demo.GIANT)
    set_pp(state, 0, 8)
    play(state, chloe, [giant.uid])
    assert giant in p.hand and count(p.hand, forest.CHLOE) == 1 and len(p.field) == 4


def test_anthuria_gives_barrier():
    state = fresh()
    ally = put(state, 0, demo.FOOTMAN)
    anthuria = give(state, 0, forest.ANTHURIA)
    set_pp(state, 0, 5)
    play(state, anthuria)
    assert ally.has(Keyword.BARRIER) and anthuria.has(Keyword.BARRIER)


def test_cupitan_skybound_evolve_pings_seven_times():
    state = fresh()
    p = state.players[0]
    enemies = [put(state, 1, demo.GIANT) for _ in range(2)]
    cupitan = give(state, 0, forest.CUPITAN)
    p.turns_taken = 10
    set_pp(state, 0, 4)
    play(state, cupitan)
    assert cupitan.evolved and sum(5 - e.life for e in enemies) == 7
    assert enemy_hp(state) == 20


def test_cupitan_super_skybound_also_hits_the_leader():
    state = fresh()
    p = state.players[0]
    cupitan = give(state, 0, forest.CUPITAN)
    p.turns_taken = 12
    cupitan.counters = {"skybound": 3}
    set_pp(state, 0, 4)
    play(state, cupitan)
    assert cupitan.evolved and enemy_hp(state) == 17


def test_cupitan_below_skybound_does_nothing():
    state = fresh()
    cupitan = give(state, 0, forest.CUPITAN)
    set_pp(state, 0, 4)
    play(state, cupitan)
    assert not cupitan.evolved


def test_alfheimr_modes_and_super_skybound_all():
    state = fresh()
    p = state.players[0]
    ally = put(state, 0, demo.FOOTMAN)
    alf = give(state, 0, forest.ALFHEIMR)
    set_pp(state, 0, 4)
    assert {a.modes for a in plays(state, alf.uid)} == {(0,), (1,), (2,)}
    play(state, alf, modes=(1,))
    assert (ally.atk, ally.life) == (2, 2) and ally.has(Keyword.RUSH)
    p.hand.clear()
    p.leader_hp = 10
    second = give(state, 0, forest.ALFHEIMR)
    p.turns_taken = 15
    assert [a.modes for a in plays(state, second.uid)] == [(0, 1, 2)]
    play(state, second, modes=(0, 1, 2))
    assert (ally.atk, ally.life) == (3, 3) and ally.has(Keyword.WARD)
    assert p.leader_hp == 11 and len(p.hand) == 1


def test_ewiyar_skybound_recovers_an_evolution_point():
    state = fresh()
    p = state.players[0]
    p.ep = 0
    early = give(state, 0, forest.EWIYAR)
    set_pp(state, 0, 4)
    play(state, early)
    assert p.ep == 0
    late = give(state, 0, forest.EWIYAR)
    p.turns_taken = 10
    play(state, late)
    assert p.ep == 1 and late.has(Keyword.RUSH)


def test_yuel_and_societte_double_strike_and_crest():
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    yuel = give(state, 0, forest.YUEL_AND_SOCIETTE)
    set_pp(state, 0, 5)
    play(state, yuel)
    assert enemy.fate == DESTROYED                               # 4 + 4 (second hits it again)
    unlock_evolution(state, 0)
    apply(state, Evolve(yuel.uid, True))
    assert E.leader_area_card(state, 0, forest.YUEL_CREST).countdown == 4


# --- set 10000 (Basic) -------------------------------------------------------------------------

def test_fairy_tamer_and_stray_beastman():
    state = fresh()
    p = state.players[0]
    tamer = give(state, 0, forest.FAIRY_TAMER)
    beast = give(state, 0, forest.STRAY_BEASTMAN)
    may = give(state, 0, forest.MAY)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    play(state, tamer)
    assert count(p.hand, forest.FAIRY) == 2
    play(state, beast)
    assert p.combo == 3                                           # 2 cards played, +1
    play(state, may, [enemy.uid])
    assert enemy.life == 2


def test_gentle_treant_combo_evolve_and_strike_heal():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    treant = give(state, 0, forest.GENTLE_TREANT)
    set_pp(state, 0, 4)
    p.combo = 2
    play(state, treant)
    assert treant.evolved
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Attack(treant.uid, enemy.uid))                 # evolved: can attack followers now
    assert p.leader_hp == 12


def test_wild_profusion_pings_on_pixie_entry():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    profusion = give(state, 0, forest.WILD_PROFUSION)
    set_pp(state, 0, 3)
    play(state, profusion)
    fairy = p.hand[-1]
    assert fairy.defn == forest.FAIRY and profusion.countdown == 2
    play(state, fairy)
    assert enemy.life == 4
    footman = give(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, footman)                                          # not a Pixie
    assert enemy.life == 4


def test_may_qa_combo_counts_the_card_itself():
    """Official Q&A: May played as the third card this turn activates Combo (3)."""
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    a, b = give(state, 0, forest.DEEPWOOD_BOUNTY), give(state, 0, forest.DEEPWOOD_BOUNTY)
    may = give(state, 0, forest.MAY)
    set_pp(state, 0, 1)
    assert plays(state, may.uid) == [PlayCard(may.uid, ())]     # Combo (3) not reachable yet
    play(state, a)
    play(state, b)
    assert plays(state, may.uid) == [PlayCard(may.uid, (enemy.uid,))]
    play(state, may, [enemy.uid])
    assert enemy.life == 2


def test_selwyn_super_evolve_returns_an_enemy():
    state = fresh()
    selwyn = put(state, 0, forest.SELWYN)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(selwyn.uid, True, (enemy.uid,)))
    assert enemy not in state.players[1].field
    assert count(state.players[1].hand, demo.GIANT) == 1
    assert selwyn.has(Keyword.STORM)


def test_selwyn_plain_evolve_returns_nothing():
    state = fresh()
    selwyn = put(state, 0, forest.SELWYN)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(selwyn.uid, False, (enemy.uid,)))
    assert enemy in state.players[1].field


def test_bug_alert_returns_an_allied_card_and_pings():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    trap = put(state, 0, forest.TRAP_IN_THE_WOODS)               # after the enemy: doesn't trigger
    alert = give(state, 0, forest.BUG_ALERT)
    set_pp(state, 0, 1)
    play(state, alert, [trap.uid])
    assert p.field == [] and count(p.hand, forest.TRAP_IN_THE_WOODS) == 1
    assert enemy.life == 3


def test_bug_alert_needs_an_allied_card():
    state = fresh()
    alert = give(state, 0, forest.BUG_ALERT)
    set_pp(state, 0, 1)
    assert plays(state, alert.uid) == []


# --- coverage and fuzzing -------------------------------------------------------------------

def _needs_script(card) -> bool:
    flag = getattr(card, "has_ability", None)          # recorded in the pool table
    if flag is not None:
        return flag
    return card not in forest.NO_SCRIPT_NEEDED


def test_every_forest_card_with_abilities_has_a_script():
    for c in forest.CARDS + forest.TOKENS + forest.LEADER_AREA:
        assert has_script(c.card_id) == _needs_script(c), c.name
    assert not any(_needs_script(c) for c in forest.NO_SCRIPT_NEEDED)
    rotation = {c.card_id for c in collectible(Craft.FOREST) if c.craft == Craft.FOREST}
    assert rotation == {c.card_id for c in forest.CARDS}


def random_forest_deck(rng: random.Random) -> list:
    """A random legal Forestcraft deck of scripted cards and cards needing no script."""
    pool = [c for c in collectible(Craft.FOREST) if has_script(c.card_id) or not _needs_script(c)]
    deck: list = []
    while len(deck) < 40:
        c = rng.choice(pool)
        if deck.count(c) < 3:
            deck.append(c)
    return deck


def test_random_forest_decks_play_to_the_end():
    rng = random.Random(1)
    for g in range(100):
        d0, d1 = random_forest_deck(rng), random_forest_deck(rng)
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
        assert state.over
