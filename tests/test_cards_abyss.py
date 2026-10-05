"""Abysscraft cards, their tokens, crests and alternate forms."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import abyss, decks, demo
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, has_script, register
from svsim.core.state import BANISHED, DESTROYED, FIELD_LIMIT, HAND_LIMIT, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution

# A stand-in for Ominous Artifact γ (another craft's card) for the Rotting Zombie Q&A:
# "At the end of your turn, deal 3 damage to all enemy followers."
ARTIFACT = CardDef(7501, "Test Artifact", Craft.NEUTRAL, CardType.AMULET, 1)


@register(ARTIFACT.card_id)
class TestArtifact(CardScript):
    def on_turn_end(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)


def hp(state):
    return state.players[0].leader_hp, state.players[1].leader_hp


def ids(cards):
    return [c.defn.card_id for c in cards]


def play(state, inst, targets=(), modes=()):
    apply(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def kill(state, inst):
    E.destroy(state, inst)
    resolve_queue(state)


def end_turns(state, n=1):
    for _ in range(n):
        apply(state, EndTurn())


# --- tokens -------------------------------------------------------------------------------

def test_ghost_is_banished_at_end_of_turn_and_when_it_leaves():
    state = start()
    p = state.players[0]
    ghost = put(state, 0, abyss.GHOST, ready=False)
    assert Attack(ghost.uid, leader_uid(1)) in legal_actions(state)        # Storm
    end_turns(state)
    assert ghost.fate == BANISHED and p.field == [] and p.shadows == 0
    other = put(state, 0, abyss.GHOST)
    kill(state, other)
    assert other.fate == BANISHED and p.shadows == 0


def test_rotting_zombie_comes_back_once():
    state = start()
    p = state.players[0]
    zombie = put(state, 0, abyss.ROTTING_ZOMBIE)
    kill(state, zombie)
    assert ids(p.field) == [abyss.ROTTING_ZOMBIE.card_id]
    second = p.field[0]
    assert not abyss.has_last_words(second)
    kill(state, second)
    assert p.field == [] and p.shadows == 2


def test_rotting_zombie_qa_both_end_of_turn_abilities_resolve_before_last_words():
    state = start(first=1)
    put(state, 0, abyss.ROTTING_ZOMBIE)
    put(state, 1, ARTIFACT)
    put(state, 1, ARTIFACT)
    end_turns(state)                       # player 1's turn ends
    field = state.players[0].field
    assert ids(field) == [abyss.ROTTING_ZOMBIE.card_id] and field[0].life == 2


def test_depths_of_the_eld_sight_draws_two():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 1)
    depths = give(state, 0, abyss.DEPTHS_OF_THE_ELD_SIGHT)
    before = len(p.hand)
    play(state, depths)
    assert len(p.hand) == before + 1


# --- crests and alternate forms --------------------------------------------------------------

def test_istyndet_crest_destroys_a_last_words_card_and_an_enemy():
    state = start()
    p = state.players[0]
    E.add_to_leader_area(state, 0, abyss.ISTYNDET_CREST)
    lilith = put(state, 0, abyss.LILITH_ENCHANTING_SUCCUBUS)
    plain = put(state, 0, demo.FOOTMAN)
    enemy = put(state, 1, demo.GIANT)
    end_turns(state)
    assert lilith.fate == DESTROYED and enemy.fate == DESTROYED and plain.fate == IN_PLAY
    assert count(p.hand, abyss.BAT) == 1


def test_istyndet_crest_needs_an_allied_last_words_card():
    state = start()
    E.add_to_leader_area(state, 0, abyss.ISTYNDET_CREST)
    put(state, 0, demo.FOOTMAN)
    zombie = put(state, 0, abyss.ROTTING_ZOMBIE)
    abyss.remove_last_words(zombie)                     # a Zombie that lost its Last Words
    enemy = put(state, 1, demo.GIANT)
    end_turns(state)
    assert enemy.fate == IN_PLAY and zombie.fate == IN_PLAY


def test_rigor_crest_draws_then_summons_a_warded_skeleton():
    state = start()
    p = state.players[0]
    E.add_to_leader_area(state, 0, abyss.RIGOR_CREST)
    hand = len(p.hand)                                  # 5 Footmen: 4+ cards of cost 1
    end_turns(state)
    assert len(p.hand) == hand + 1
    skeleton = p.field[-1]
    assert skeleton.defn == abyss.SKELETON and skeleton.has(Keyword.WARD)
    end_turns(state, 2)                                 # countdown 2 -> 1, fires again
    assert count(p.field, abyss.SKELETON) == 2
    end_turns(state, 2)
    assert p.leader_area == [] and count(p.field, abyss.SKELETON) == 2


def test_rigor_crest_without_four_of_a_cost():
    state = start()
    p = state.players[0]
    p.hand.clear()
    give(state, 0, abyss.NIGHT_FIEND)
    E.add_to_leader_area(state, 0, abyss.RIGOR_CREST)
    end_turns(state)
    assert len(p.hand) == 2 and count(p.field, abyss.SKELETON) == 0


def test_milteo_crest_evolves_played_followers():
    state = start()
    E.add_to_leader_area(state, 0, abyss.MILTEO_CREST)
    set_pp(state, 0, 3)
    fiend = give(state, 0, abyss.NIGHT_FIEND)
    play(state, fiend)
    assert fiend.evolved and (fiend.atk, fiend.life) == (6, 5)


def test_milteo_crest_ignores_amulets_played_by_crystallize():
    state = start()
    E.add_to_leader_area(state, 0, abyss.MILTEO_CREST)
    set_pp(state, 0, 2)
    colonel = give(state, 0, abyss.VOID_COLONEL)
    play(state, colonel)
    assert colonel.defn == abyss.VOID_COLONEL_CRYSTALLIZE and not colonel.evolved


def test_valiant_edge_and_its_crest():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    edge = give(state, 0, abyss.VALIANT_EDGE)
    play(state, edge)
    assert hp(state) == (18, 20) and ids(state.players[0].leader_area) == [abyss.VALIANT_EDGE_CREST.card_id]
    end_turns(state)
    assert enemy.life == 3 and hp(state) == (19, 20)


def test_corruption_shrinks_everything_and_gives_both_players_the_crest():
    state = start()
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 5)
    corruption = give(state, 0, abyss.CORRUPTION)
    play(state, corruption)
    assert (mine.atk, mine.life) == (3, 3) and theirs.fate == DESTROYED
    assert all(ids(p.leader_area) == [abyss.CORRUPTION_CREST.card_id] for p in state.players)
    end_turns(state)
    assert hp(state) == (18, 20)
    end_turns(state)
    assert hp(state) == (18, 18)


def test_corruption_super_skybound_art_destroys_your_own_crest():
    state = start()
    state.players[0].turns_taken = 15
    set_pp(state, 0, 5)
    corruption = give(state, 0, abyss.CORRUPTION)
    play(state, corruption)
    assert state.players[0].leader_area == []
    assert ids(state.players[1].leader_area) == [abyss.CORRUPTION_CREST.card_id]


def test_belial_crest_last_words_deals_twenty():
    state = start()
    crest = E.add_to_leader_area(state, 0, abyss.BELIAL_CREST)
    crest.countdown = 1
    end_turns(state, 2)
    assert crest.fate == DESTROYED and state.winner == 0


def test_void_colonel_crystallize_and_its_last_words():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    colonel = give(state, 0, abyss.VOID_COLONEL)
    play(state, colonel)
    assert colonel.defn == abyss.VOID_COLONEL_CRYSTALLIZE and colonel.countdown == 4
    colonel.countdown = 1
    end_turns(state, 2)
    assert ids(p.field) == [abyss.VOID_COLONEL.card_id]


# --- set 10009 ------------------------------------------------------------------------------

def test_ruthless_blitzer_hits_both_leaders():
    state = start()
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.RUTHLESS_BLITZER))
    assert hp(state) == (18, 18)


def test_netherworld_lieutenant_returns_once_with_rush():
    state = start()
    p = state.players[0]
    lieutenant = put(state, 0, abyss.NETHERWORLD_LIEUTENANT)
    kill(state, lieutenant)
    second = p.field[0]
    assert second.defn == abyss.NETHERWORLD_LIEUTENANT and (second.atk, second.life) == (2, 1)
    assert second.has(Keyword.RUSH)
    kill(state, second)
    assert p.field == []


def test_spooky_surprise():
    state = start()
    set_pp(state, 0, 4)
    play(state, give(state, 0, abyss.SPOOKY_SURPRISE))
    assert ids(state.players[0].field) == [abyss.GHOST.card_id, abyss.ROTTING_ZOMBIE.card_id]


def test_void_colonel_last_words():
    state = start()
    state.players[0].leader_hp = 15
    colonel = put(state, 0, abyss.VOID_COLONEL)
    enemy = put(state, 1, demo.GIANT)
    kill(state, colonel)
    assert enemy.fate == DESTROYED and hp(state) == (17, 20)


def test_sparkly_demoness():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.SPARKLY_DEMONESS), [enemy.uid])
    assert enemy.fate == DESTROYED and hp(state) == (20, 18)


def test_chains_of_the_past_once():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.CHAINS_OF_THE_PAST))
    assert enemy.life == 2 and hp(state) == (19, 19)


def test_chains_of_the_past_enhanced_twice():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    play(state, give(state, 0, abyss.CHAINS_OF_THE_PAST))
    assert enemy.fate == DESTROYED and hp(state) == (18, 18)


def test_rampaging_commander_fanfare_and_super_evolve():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 6)
    commander = give(state, 0, abyss.RAMPAGING_COMMANDER)
    play(state, commander)
    assert enemy.life == 2 and hp(state) == (17, 17)
    unlock_evolution(state, 0)
    hand = len(p.hand)
    apply(state, Evolve(commander.uid, True))
    assert len(p.hand) == hand + 2 and hp(state) == (16, 16)


def test_rampaging_commander_plain_evolve_does_nothing():
    state = start()
    commander = put(state, 0, abyss.RAMPAGING_COMMANDER)
    unlock_evolution(state, 0)
    apply(state, Evolve(commander.uid, False))
    assert hp(state) == (20, 20)


def test_reapers_due_gives_summon_a_copy_last_words():
    state = start()
    p = state.players[0]
    giant = put(state, 0, demo.GIANT)
    E.buff(state, giant, 2, 2)
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.REAPERS_DUE), [giant.uid])
    assert abyss.has_last_words(giant)
    kill(state, giant)
    copy = p.field[0]
    assert copy.defn == demo.GIANT and (copy.atk, copy.life) == (5, 5)
    assert not copy.grants                              # a fresh card: no Last Words


def test_reapers_due_restores_last_words_to_a_spent_zombie():
    state = start()
    p = state.players[0]
    zombie = put(state, 0, abyss.ROTTING_ZOMBIE)
    abyss.remove_last_words(zombie)
    assert not abyss.has_last_words(zombie)
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.REAPERS_DUE), [zombie.uid])
    assert abyss.has_last_words(zombie)
    kill(state, zombie)
    fresh = p.field[0]
    assert fresh.defn == abyss.ROTTING_ZOMBIE and abyss.has_last_words(fresh)


def test_reapers_due_needs_an_allied_follower():
    state = start()
    set_pp(state, 0, 2)
    due = give(state, 0, abyss.REAPERS_DUE)
    assert plays(state, due.uid) == []


def test_istyndet_reanimates_three_times_then_burns():
    state = start()
    p = state.players[0]
    p.destroyed += [abyss.LULUMI, abyss.RAZ, demo.FOOTMAN, abyss.NIGHT_FIEND]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    istyndet = give(state, 0, abyss.ISTYNDET_VS_MITILYKKET)
    play(state, istyndet)
    revived = p.field[1:]
    assert len(revived) == 3 and all(c.defn.cost == 2 for c in revived)
    assert all(E.has_trait(c, abyss.DEPARTED) for c in revived)
    assert enemy.life == 3
    unlock_evolution(state, 0)
    apply(state, Evolve(istyndet.uid, True))
    assert ids(p.leader_area) == [abyss.ISTYNDET_CREST.card_id]


def test_garodeth_cost_drops_in_hand_at_low_defense():
    state = start()
    p = state.players[0]
    garodeth = give(state, 0, abyss.GARODETH_VS_ZETH)
    end_turns(state, 2)
    assert garodeth.cost == 8
    p.leader_hp = 12
    end_turns(state)
    assert garodeth.cost == 7
    on_field = put(state, 0, abyss.GARODETH_VS_ZETH)
    end_turns(state, 2)
    assert garodeth.cost == 6 and on_field.cost == 8     # only in hand


def test_garodeth_modes():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 8)
    storm = give(state, 0, abyss.GARODETH_VS_ZETH)
    assert {a.modes for a in plays(state, storm.uid)} == {(0,), (1,)}
    play(state, storm, modes=[0])
    assert storm.has(Keyword.STORM) and hp(state) == (18, 20) and enemy.fate == IN_PLAY
    set_pp(state, 0, 8)
    ward = give(state, 0, abyss.GARODETH_VS_ZETH)
    play(state, ward, modes=[1])
    assert ward.has(Keyword.WARD) and not ward.has(Keyword.STORM) and enemy.fate == DESTROYED


# --- set 10008 ------------------------------------------------------------------------------

def test_anisage_is_blocked_and_unscripted():
    assert not has_script(abyss.ANISAGE.card_id) and abyss.ANISAGE in abyss.BLOCKED


def test_lilith_devilish_cutie_strike_and_last_words():
    state = start()
    lilith = put(state, 0, abyss.LILITH_DEVILISH_CUTIE)
    apply(state, Attack(lilith.uid, leader_uid(1)))
    assert hp(state) == (19, 18)
    enemy = put(state, 1, demo.GIANT)
    end_turns(state, 2)
    apply(state, Attack(lilith.uid, enemy.uid))
    assert hp(state) == (18, 17) and lilith.fate == DESTROYED
    assert count(state.players[0].hand, abyss.BAT) == 1


def test_limil_summons_bats_only_when_ahead():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.LIMIL))
    assert count(p.field, abyss.BAT) == 0                # equal defense
    state.players[1].leader_hp = 19
    set_pp(state, 0, 2)
    limil = give(state, 0, abyss.LIMIL)
    play(state, limil)
    assert count(p.field, abyss.BAT) == 2
    p.field.remove(p.field[-1])
    unlock_evolution(state, 0)
    apply(state, Evolve(limil.uid))
    assert count(p.field, abyss.BAT) == 3


def test_fiole_gives_bats_rush():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 6)
    play(state, give(state, 0, abyss.FIOLE))
    bats = [c for c in p.field if c.defn == abyss.BAT]
    assert len(bats) == 3 and all(b.has(Keyword.RUSH) for b in bats)
    p.field.remove(bats[0])
    later = put(state, 0, abyss.BAT)
    other = put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert later.has(Keyword.RUSH) and not other.has(Keyword.RUSH)


def test_marsha_fanfare_and_evolve():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    marsha = give(state, 0, abyss.MARSHA)
    play(state, marsha)
    assert enemy.life == 4 and hp(state) == (19, 19)
    unlock_evolution(state, 0)
    apply(state, Evolve(marsha.uid))
    assert enemy.life == 3 and hp(state) == (18, 18) and marsha.life == 6


def test_bittersweet_departures_modes():
    state = start()
    p = state.players[0]
    p.leader_hp = 15
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    first = give(state, 0, abyss.BITTERSWEET_DEPARTURES)
    assert len(plays(state, first.uid)) == 6              # 4 choose 2
    play(state, first, modes=[0, 3])
    assert hp(state) == (15, 19) and p.shadows == 5      # 4 + the spell itself
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.BITTERSWEET_DEPARTURES), modes=[1, 2])
    assert hp(state) == (17, 19) and enemy.life == 2


def test_suzy_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    p.hand.clear()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    suzy = give(state, 0, abyss.SUZY)
    fiend = give(state, 0, abyss.NIGHT_FIEND)
    spell = give(state, 0, abyss.SOUL_PREDATION)
    play(state, suzy, [enemy.uid])
    assert (enemy.atk, enemy.life, enemy.max_life) == (5, 2, 2)
    unlock_evolution(state, 0)
    targets = {a.targets for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == suzy.uid}
    assert targets == {(fiend.uid,)} and spell.uid not in {t for ts in targets for t in ts}
    apply(state, Evolve(suzy.uid, False, (fiend.uid,)))
    assert (fiend.atk, fiend.life) == (7, 3)
    set_pp(state, 0, 3)
    play(state, fiend)
    assert fiend.atk == 7                                # the buff stays on the card


def test_ebb_and_flow_before_super_evolution():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    fiend = give(state, 0, abyss.NIGHT_FIEND)
    ebb = give(state, 0, abyss.EBB_AND_FLOW)
    hand = len(p.hand)
    play(state, ebb, [fiend.uid])
    assert fiend in p.deck or fiend in p.hand
    assert len(p.hand) == hand - 2 + 2
    assert all(c.cost == c.defn.cost for c in p.hand[-2:])


def test_ebb_and_flow_reduces_drawn_costs_after_super_evolution_unlocks():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 2)
    ebb = give(state, 0, abyss.EBB_AND_FLOW)
    play(state, ebb, [p.hand[0].uid])
    assert all(c.cost == c.defn.cost - 1 for c in p.hand[-2:])


def test_ebb_and_flow_needs_another_card_in_hand():
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, 2)
    ebb = give(state, 0, abyss.EBB_AND_FLOW)
    assert plays(state, ebb.uid) == []


def test_itsurugi_fanfare_modes():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 8)
    play(state, give(state, 0, abyss.ITSURUGI_AND_TAKETSUMI), modes=[0])
    assert hp(state) == (14, 16) and enemy.life == 5
    p.ep = 1
    set_pp(state, 0, 8)
    play(state, give(state, 0, abyss.ITSURUGI_AND_TAKETSUMI), modes=[1])
    assert enemy.fate == DESTROYED and p.ep == 2


def test_itsurugi_evolve_modes():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    first, second = put(state, 0, abyss.ITSURUGI_AND_TAKETSUMI), put(state, 0, abyss.ITSURUGI_AND_TAKETSUMI)
    hand = len(p.hand)
    apply(state, Evolve(first.uid, False, (), (0,)))
    assert len(p.hand) == hand + 2
    p.evolved_this_turn = False
    set_pp(state, 0, 5)
    p.pp = 1
    apply(state, Evolve(second.uid, False, (), (1,)))
    assert p.pp == 3


def test_ceres_necromancy_clash_and_turn_end():
    state = start()
    p = state.players[0]
    p.shadows = 20
    p.leader_hp = 10
    set_pp(state, 0, 5)
    abyss_card = give(state, 0, abyss.SPARKLY_DEMONESS)
    neutral = give(state, 0, demo.GIANT)
    ceres = give(state, 0, abyss.CERES)
    play(state, ceres)
    assert p.shadows == 0 and abyss_card.cost == 5 and neutral.cost == 5
    end_turns(state)
    assert p.leader_hp == 14
    enemy = put(state, 1, demo.GIANT)
    apply(state, Attack(enemy.uid, ceres.uid))        # Clash fires when attacked too: 4 + 1
    assert enemy.fate == DESTROYED and ceres.fate == DESTROYED


def test_ceres_without_enough_shadows():
    state = start()
    p = state.players[0]
    p.shadows = 19
    set_pp(state, 0, 5)
    other = give(state, 0, abyss.SPARKLY_DEMONESS)
    play(state, give(state, 0, abyss.CERES))
    assert p.shadows == 19 and other.cost == 7


# --- set 10007 ------------------------------------------------------------------------------

def test_lulumi_last_words():
    state = start()
    kill(state, put(state, 0, abyss.LULUMI))
    assert count(state.players[0].hand, abyss.BAT) == 1


def test_raz_last_words_and_evolve():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    raz = put(state, 0, abyss.RAZ)
    unlock_evolution(state, 0)
    apply(state, Evolve(raz.uid, False, (enemy.uid,)))
    assert enemy.life == 2
    kill(state, raz)
    assert ids(state.players[0].field) == [abyss.SKELETON.card_id]


def test_soul_tuning_needs_two_allies():
    state = start()
    a = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 1)
    tuning = give(state, 0, abyss.SOUL_TUNING)
    assert plays(state, tuning.uid) == []
    b = put(state, 0, demo.FOOTMAN)
    hand = len(state.players[0].hand)
    play(state, tuning, [a.uid, b.uid])
    assert a.life == 3 and b.life == 3 and len(state.players[0].hand) == hand


def test_highwire_feline_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    feline = give(state, 0, abyss.HIGHWIRE_FELINE)
    play(state, feline, [enemy.uid])
    assert enemy.life == 2 and count(p.field, abyss.SKELETON) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(feline.uid, False, (enemy.uid,)))
    assert enemy.fate == DESTROYED and count(p.field, abyss.SKELETON) == 2


def test_juggler_corvid():
    state = start()
    p = state.players[0]
    p.destroyed.append(abyss.LULUMI)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 6)
    play(state, give(state, 0, abyss.JUGGLER_CORVID), [enemy.uid])
    assert enemy.fate == DESTROYED and ids(p.field)[-1] == abyss.LULUMI.card_id


def test_harmony_of_youth_summons_evolved_tokens():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.HARMONY_OF_YOUTH))
    assert ids(p.field) == [abyss.GHOST.card_id, abyss.BAT.card_id, abyss.SKELETON.card_id]
    assert all(c.evolved for c in p.field)
    assert [(c.atk, c.life) for c in p.field] == [(3, 3), (3, 3), (3, 3)]


def test_beastmaster_bones_gives_departed_storm():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 7)
    bones = give(state, 0, abyss.BEASTMASTER_BONES)
    play(state, bones)
    zombie, skeleton = p.field[1], p.field[2]
    assert zombie.has(Keyword.STORM) and skeleton.has(Keyword.STORM)
    footman = put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert not footman.has(Keyword.STORM)
    assert not bones.has(Keyword.STORM)


def test_beastmaster_bones_super_evolve_trades_an_ally():
    state = start()
    p = state.players[0]
    bones = put(state, 0, abyss.BEASTMASTER_BONES)
    ally = put(state, 0, demo.FOOTMAN)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(bones.uid, False, (ally.uid,)))      # plain evolve: nothing
    assert ally.fate == IN_PLAY and enemy.fate == IN_PLAY
    second = put(state, 0, abyss.BEASTMASTER_BONES)
    p.evolved_this_turn = False
    apply(state, Evolve(second.uid, True, (ally.uid,)))
    assert ally.fate == DESTROYED and enemy.fate == DESTROYED


def test_beastmaster_bones_super_evolve_without_selection():
    state = start()
    bones = put(state, 0, abyss.BEASTMASTER_BONES)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(bones.uid, True))
    assert enemy.fate == IN_PLAY


def test_hark_to_the_night_song():
    state = start()
    p = state.players[0]
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.HARK_TO_THE_NIGHT_SONG))
    assert a.fate == DESTROYED and b.life == 1 and hp(state) == (20, 20)
    p.shadows = 6
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.HARK_TO_THE_NIGHT_SONG))
    assert b.fate == DESTROYED and hp(state) == (20, 18) and p.shadows == 1


def test_adahime_summons_from_deck_and_rallies():
    state = start()
    p = state.players[0]
    p.deck = [state.new_instance(d, 0) for d in
              (abyss.LULUMI, abyss.LULUMI, abyss.RAZ, abyss.NIGHT_FIEND, demo.FOOTMAN)]
    set_pp(state, 0, 6)
    adahime = give(state, 0, abyss.ADAHIME)
    play(state, adahime)
    summoned = p.field[1:]
    assert sorted(ids(summoned)) == sorted([abyss.LULUMI.card_id, abyss.RAZ.card_id])
    assert all(c.has(Keyword.RUSH) for c in summoned)
    footman = put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert not footman.has(Keyword.RUSH)
    unlock_evolution(state, 0)
    apply(state, Evolve(adahime.uid, True))
    raz = next(c for c in summoned if c.defn == abyss.RAZ)
    assert (raz.atk, raz.life) == (3, 4) and (footman.atk, footman.life) == (1, 2)
    assert (adahime.atk, adahime.life) == (8, 7)


def test_macmillan_necromancy_and_departed_bonus():
    state = start()
    p = state.players[0]
    p.shadows = 10
    set_pp(state, 0, 9)
    play(state, give(state, 0, abyss.MACMILLAN))
    zombies = p.field[1:]
    assert len(zombies) == 3 and p.shadows == 0
    assert all((z.atk, z.life) == (3, 2) and z.has(Keyword.RUSH | Keyword.WARD) for z in zombies)
    assert hp(state) == (20, 17)
    end_turns(state)                                    # opponent's turn: no bonus
    kill(state, zombies[0])
    revived = p.field[-1]
    assert revived.defn == abyss.ROTTING_ZOMBIE and not revived.has(Keyword.WARD)
    assert hp(state)[1] == 17


def test_macmillan_without_necromancy():
    state = start()
    p = state.players[0]
    p.shadows = 9
    set_pp(state, 0, 9)
    play(state, give(state, 0, abyss.MACMILLAN))
    assert len(p.field) == 1 and p.shadows == 9


# --- set 10006 ------------------------------------------------------------------------------

def test_reverent_demon_last_words():
    state = start()
    p = state.players[0]
    hand = len(p.hand)
    kill(state, put(state, 0, abyss.REVERENT_DEMON))
    assert len(p.hand) == hand + 1 and hp(state) == (19, 20)


def test_ghost_dodger_last_words():
    state = start()
    kill(state, put(state, 0, abyss.GHOST_DODGER))
    assert count(state.players[0].hand, abyss.GHOST) == 1


def test_advent_of_the_eld_sight():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    set_pp(state, 0, 3)
    hand = len(p.hand)
    play(state, give(state, 0, abyss.ADVENT_OF_THE_ELD_SIGHT))
    assert len(p.hand) == hand + 2 and p.leader_hp == 10
    p.shadows = 4
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.ADVENT_OF_THE_ELD_SIGHT))
    assert p.leader_hp == 12 and p.shadows == 1


def test_yearnful_necromancer_enhanced_reanimates():
    state = start()
    p = state.players[0]
    p.destroyed += [abyss.SPARKLY_DEMONESS, demo.FOOTMAN]
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.YEARNFUL_NECROMANCER))
    assert len(p.field) == 1 and p.pp == 0
    set_pp(state, 0, 8)
    play(state, give(state, 0, abyss.YEARNFUL_NECROMANCER))
    assert ids(p.field)[-1] == abyss.SPARKLY_DEMONESS.card_id and p.pp == 0


def test_devilish_heartbreaker():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    plain = give(state, 0, abyss.DEVILISH_HEARTBREAKER)
    play(state, plain)
    assert not plain.has(Keyword.STORM)
    set_pp(state, 0, 7)
    storm = give(state, 0, abyss.DEVILISH_HEARTBREAKER)
    play(state, storm)
    assert storm.has(Keyword.STORM) and Attack(storm.uid, leader_uid(1)) in legal_actions(state)
    unlock_evolution(state, 0)
    apply(state, Evolve(plain.uid, False, (enemy.uid,)))
    assert enemy.life == 1


def test_allure_of_the_mightiest_steals_an_exact_copy():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    E.buff(state, enemy, 2, 2)
    E.damage(state, [enemy], 1)
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.ALLURE_OF_THE_MIGHTIEST), [enemy.uid])
    assert enemy.fate == BANISHED and state.players[1].field == [] and state.players[1].shadows == 0
    copy = state.players[0].field[0]
    assert copy.defn == demo.GIANT and (copy.atk, copy.life, copy.max_life) == (7, 6, 7)
    assert copy.owner == 0


def test_deprived_destroyer_destroys_an_ally_and_evolves():
    state = start()
    p = state.players[0]
    ally = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 5)
    destroyer = give(state, 0, abyss.DEPRIVED_DESTROYER)
    play(state, destroyer, [ally.uid])
    assert ally.fate == DESTROYED and destroyer.evolved
    bat = p.field[-1]
    assert bat.defn == abyss.BAT and bat.evolved and (bat.atk, bat.life) == (3, 3)


def test_deprived_destroyer_without_an_ally_and_point_evolution():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 5)
    destroyer = give(state, 0, abyss.DEPRIVED_DESTROYER)
    play(state, destroyer)
    assert not destroyer.evolved and len(p.field) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(destroyer.uid))
    assert count(p.field, abyss.BAT) == 1


def test_depletive_eld_sight_modes():
    state = start()
    p = state.players[0]
    p.ep = 0
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.DEPLETIVE_ELD_SIGHT), modes=[0])
    assert p.ep == 1 and enemy.life == 5
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.DEPLETIVE_ELD_SIGHT), modes=[1])
    assert p.ep == 1 and enemy.life == 3


def test_armes():
    state = start()
    armes = put(state, 0, abyss.ARMES)
    assert not E.destroy(state, armes)
    big = put(state, 1, demo.GIANT)
    E.buff(state, big, 10, 10)
    apply(state, Attack(armes.uid, big.uid))
    assert big.fate == DESTROYED and armes.life == 10        # destroyed before damage
    unlock_evolution(state, 0)
    apply(state, Evolve(armes.uid, True))
    assert armes.max_attacks == 3


def test_bibatii_necromancy_evolves_and_adds_depths():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 4)
    plain = give(state, 0, abyss.BIBATII)
    play(state, plain)
    assert not plain.evolved and count(p.hand, abyss.DEPTHS_OF_THE_ELD_SIGHT) == 0
    p.shadows = 4
    set_pp(state, 0, 4)
    bibatii = give(state, 0, abyss.BIBATII)
    play(state, bibatii)
    assert bibatii.evolved and p.shadows == 0 and count(p.hand, abyss.DEPTHS_OF_THE_ELD_SIGHT) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(plain.uid))
    assert count(p.hand, abyss.DEPTHS_OF_THE_ELD_SIGHT) == 2


# --- set 10005 ------------------------------------------------------------------------------

def test_support_wolf_enhance():
    state = start()
    set_pp(state, 0, 2)
    plain = give(state, 0, abyss.SUPPORT_WOLF)
    play(state, plain)
    assert (plain.atk, plain.life) == (2, 2) and not plain.has(Keyword.BANE)
    set_pp(state, 0, 6)
    wolf = give(state, 0, abyss.SUPPORT_WOLF)
    play(state, wolf)
    assert (wolf.atk, wolf.life) == (2, 8) and wolf.has(Keyword.BANE | Keyword.BARRIER | Keyword.RUSH)


def test_crimson_soulmancer_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    p.destroyed += [abyss.LULUMI, demo.FOOTMAN]
    set_pp(state, 0, 4)
    soulmancer = give(state, 0, abyss.CRIMSON_SOULMANCER)
    play(state, soulmancer)
    assert ids(p.field) == [abyss.CRIMSON_SOULMANCER.card_id, abyss.LULUMI.card_id]
    unlock_evolution(state, 0)
    apply(state, Evolve(soulmancer.uid))
    assert count(p.field, abyss.LULUMI) == 2


def test_valor_of_the_nightblossom_shuffles_a_copy():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    deck = len(p.deck)
    play(state, give(state, 0, abyss.VALOR_OF_THE_NIGHTBLOSSOM), [enemy.uid])
    assert enemy.fate == DESTROYED and len(p.deck) == deck + 1
    assert count(p.deck, abyss.VALOR_OF_THE_NIGHTBLOSSOM) == 1


def test_fickle_necromancer():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 3)
    fickle = give(state, 0, abyss.FICKLE_NECROMANCER)
    play(state, fickle)
    assert ids(p.field) == [abyss.FICKLE_NECROMANCER.card_id, abyss.GHOST.card_id,
                            abyss.SKELETON.card_id]
    unlock_evolution(state, 0)
    apply(state, Evolve(fickle.uid))
    assert ids(p.field)[-1] == abyss.ROTTING_ZOMBIE.card_id


def test_friendly_blue_ogre_pins_an_enemy_until_end_of_their_turn():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    hand = len(p.hand)
    ogre = give(state, 0, abyss.FRIENDLY_BLUE_OGRE)
    play(state, ogre, [enemy.uid])
    assert len(p.hand) == hand + 1
    end_turns(state)
    assert not any(isinstance(a, Attack) and a.attacker == enemy.uid for a in legal_actions(state))
    end_turns(state, 2)
    assert any(isinstance(a, Attack) and a.attacker == enemy.uid for a in legal_actions(state))


def test_friendly_blue_ogre_evolve_replicates():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    ogre = put(state, 0, abyss.FRIENDLY_BLUE_OGRE)
    unlock_evolution(state, 0)
    hand = len(state.players[0].hand)
    apply(state, Evolve(ogre.uid, False, (enemy.uid,)))
    assert len(state.players[0].hand) == hand + 1
    end_turns(state)
    assert not any(isinstance(a, Attack) and a.attacker == enemy.uid for a in legal_actions(state))


def test_tyrannical_fists_qa_lowest_leader():
    state = start()
    state.players[0].leader_hp = 19
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.TYRANNICAL_FISTS))
    assert hp(state) == (16, 20)


def test_tyrannical_fists_qa_tie_hits_both():
    state = start()
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.TYRANNICAL_FISTS))
    assert hp(state) == (17, 17)


def test_lifestealer_transforms_and_heals_on_skeleton_deaths():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 9)
    lifestealer = give(state, 0, abyss.LIFESTEALER)
    play(state, lifestealer)
    assert mine.defn == abyss.SKELETON and theirs.defn == abyss.SKELETON
    assert (lifestealer.atk, lifestealer.life) == (7, 7)
    unlock_evolution(state, 0)
    apply(state, Evolve(lifestealer.uid))                # 1 damage to all other followers
    assert mine.fate == DESTROYED and theirs.fate == DESTROYED and p.leader_hp == 12


def test_rigor_of_the_nightblossom_gains_the_crest():
    state = start()
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.RIGOR_OF_THE_NIGHTBLOSSOM))
    crest = state.players[0].leader_area[0]
    assert crest.defn == abyss.RIGOR_CREST and crest.countdown == 2


def test_milteo_and_luzen_fanfare_reanimates_twice():
    state = start()
    p = state.players[0]
    p.destroyed += [abyss.CERES, abyss.BIBATII, abyss.LULUMI]       # 5, 4, 2
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.MILTEO_AND_LUZEN))
    assert ids(p.field)[1:] == [abyss.BIBATII.card_id, abyss.LULUMI.card_id]


def test_milteo_and_luzen_evolve_destroys_others_and_super_gains_crest():
    state = start()
    p = state.players[0]
    milteo = put(state, 0, abyss.MILTEO_AND_LUZEN)
    others = [put(state, 0, demo.FOOTMAN), put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)]
    unlock_evolution(state, 0)
    apply(state, Evolve(milteo.uid))
    assert all(o.fate == DESTROYED for o in others) and milteo.fate == IN_PLAY
    assert p.leader_area == []
    second = put(state, 0, abyss.MILTEO_AND_LUZEN)
    p.evolved_this_turn = False
    apply(state, Evolve(second.uid, True))
    assert ids(p.leader_area) == [abyss.MILTEO_CREST.card_id]
    assert milteo.fate == DESTROYED                     # evolved, not super-evolved: no protection


def test_milteo_destroys_at_most_six():
    state = start(first=0)
    milteo = put(state, 0, abyss.MILTEO_AND_LUZEN)
    for side in (0, 1):
        for _ in range(4 if side else 3):
            put(state, side, demo.FOOTMAN)
    E.evolve(state, milteo)
    resolve_queue(state)
    survivors = [c for p in state.players for c in p.followers if c is not milteo]
    assert len(survivors) == 1


def test_shakdoh_redraws_twice_and_burns():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 10)
    shakdoh = give(state, 0, abyss.SHAKDOH)
    hand = len(p.hand) - 1                              # five Footmen
    play(state, shakdoh)
    assert len(p.hand) == hand and enemy.fate == DESTROYED and hp(state) == (20, 12)
    unlock_evolution(state, 0)
    apply(state, Evolve(shakdoh.uid, True))
    assert hp(state) == (20, 4)


def test_shakdoh_without_four_of_a_cost():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 10)
    shakdoh = give(state, 0, abyss.SHAKDOH)
    give(state, 0, abyss.NIGHT_FIEND)
    play(state, shakdoh)
    assert len(p.hand) == 1 and hp(state) == (20, 20)


# --- set 10000 ------------------------------------------------------------------------------

def test_night_fiend():
    state = start()
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.NIGHT_FIEND))
    assert hp(state) == (19, 20)


def test_devious_lesser_mummy():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    plain = give(state, 0, abyss.DEVIOUS_LESSER_MUMMY)
    play(state, plain)
    assert not plain.has(Keyword.STORM)
    p.shadows = 4
    set_pp(state, 0, 2)
    mummy = give(state, 0, abyss.DEVIOUS_LESSER_MUMMY)
    play(state, mummy)
    assert mummy.has(Keyword.STORM) and p.shadows == 0
    assert Attack(mummy.uid, leader_uid(1)) in legal_actions(state)


def test_chaos_cyclone_draws_a_follower():
    state = start()
    p = state.players[0]
    p.deck = [state.new_instance(d, 0) for d in (abyss.NIGHT_FIEND, abyss.SOUL_PREDATION,
                                                 abyss.SOUL_PREDATION)]
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.CHAOS_CYCLONE), modes=[0])
    assert p.hand[-1].defn == abyss.NIGHT_FIEND and len(p.deck) == 2


def test_chaos_cyclone_qa_reanimate_mode_with_nothing_destroyed():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    cyclone = give(state, 0, abyss.CHAOS_CYCLONE)
    assert {a.modes for a in plays(state, cyclone.uid)} == {(0,), (1,)}
    play(state, cyclone, modes=[1])
    assert p.field == []
    p.destroyed.append(abyss.LULUMI)
    set_pp(state, 0, 2)
    play(state, give(state, 0, abyss.CHAOS_CYCLONE), modes=[1])
    assert ids(p.field) == [abyss.LULUMI.card_id]


def test_lilith_enchanting_succubus():
    state = start()
    kill(state, put(state, 0, abyss.LILITH_ENCHANTING_SUCCUBUS))
    assert count(state.players[0].hand, abyss.BAT) == 1


def test_amorous_necromancer_evolve_and_super_evolve():
    state = start()
    p = state.players[0]
    first = put(state, 0, abyss.AMOROUS_NECROMANCER)
    unlock_evolution(state, 0)
    apply(state, Evolve(first.uid))
    ghosts = [c for c in p.field if c.defn == abyss.GHOST]
    assert len(ghosts) == 2 and not any(g.has(Keyword.DRAIN) for g in ghosts)
    for g in ghosts:
        p.field.remove(g)
    second = put(state, 0, abyss.AMOROUS_NECROMANCER)
    p.evolved_this_turn = False
    apply(state, Evolve(second.uid, True))
    ghosts = [c for c in p.field if c.defn == abyss.GHOST]
    assert len(ghosts) == 2 and all(g.has(Keyword.DRAIN) for g in ghosts)


def test_soul_predation():
    state = start()
    p = state.players[0]
    ally = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 2)
    hand = len(p.hand)
    play(state, give(state, 0, abyss.SOUL_PREDATION), [ally.uid])
    assert ally.fate == DESTROYED and len(p.hand) == hand + 2


def test_soul_predation_qa_super_evolved_ally_survives_but_you_draw():
    state = start()
    p = state.players[0]
    ally = put(state, 0, demo.GIANT)
    E.evolve(state, ally, super_=True)
    resolve_queue(state)
    set_pp(state, 0, 2)
    hand = len(p.hand)
    play(state, give(state, 0, abyss.SOUL_PREDATION), [ally.uid])
    assert ally.fate == IN_PLAY and len(p.hand) == hand + 2


# --- set 10004 ------------------------------------------------------------------------------

def test_almeida_enhance():
    state = start()
    set_pp(state, 0, 2)
    plain = give(state, 0, abyss.ALMEIDA)
    play(state, plain)
    assert not plain.evolved and (plain.atk, plain.life) == (3, 1)
    set_pp(state, 0, 4)
    almeida = give(state, 0, abyss.ALMEIDA)
    play(state, almeida)
    assert almeida.evolved and (almeida.atk, almeida.life) == (6, 4)


def test_vaseraga_last_words():
    state = start()
    p = state.players[0]
    kill(state, put(state, 0, abyss.VASERAGA))
    assert ids(p.field) == [abyss.VASERAGA.card_id] and hp(state) == (18, 20)
    assert p.field[0].has(Keyword.INTIMIDATE)


def test_nezha_end_of_turn():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    E.buff(state, enemy, 0, 5)                          # 5/10
    put(state, 0, abyss.NEZHA)
    end_turns(state)
    assert enemy.life == 4


def test_satyr_evolves_next_to_an_evolved_ally():
    state = start()
    set_pp(state, 0, 3)
    plain = give(state, 0, abyss.SATYR)
    play(state, plain)
    assert not plain.evolved
    ally = put(state, 0, demo.FOOTMAN)
    E.evolve(state, ally)
    resolve_queue(state)
    set_pp(state, 0, 3)
    satyr = give(state, 0, abyss.SATYR)
    play(state, satyr)
    assert satyr.evolved and satyr.has(Keyword.AURA)


def test_baal_modes():
    state = start()
    ally = put(state, 0, demo.FOOTMAN)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    baal = give(state, 0, abyss.BAAL)
    play(state, baal, modes=[0])
    assert (baal.atk, baal.life) == (3, 3) and (ally.atk, ally.life) == (2, 3)
    set_pp(state, 0, 3)
    play(state, give(state, 0, abyss.BAAL), modes=[1])
    assert enemy.life == 2


def test_baal_alone_buffs_itself():
    state = start()
    set_pp(state, 0, 3)
    baal = give(state, 0, abyss.BAAL)
    play(state, baal, modes=[0])
    assert (baal.atk, baal.life) == (3, 3)


def test_nehan_evolves_everyone():
    state = start()
    ally = put(state, 0, demo.FOOTMAN)
    done = put(state, 0, demo.FOOTMAN)
    E.evolve(state, done)
    resolve_queue(state)
    set_pp(state, 0, 6)
    nehan = give(state, 0, abyss.NEHAN)
    play(state, nehan)
    assert ally.evolved and nehan.evolved and (done.atk, done.life) == (3, 4)
    assert hp(state) == (18, 20)


def test_fediel_reanimates_evolved_and_shrinks_enemies():
    state = start()
    p = state.players[0]
    p.shadows = 6
    p.destroyed += [abyss.LULUMI, abyss.LILITH_ENCHANTING_SUCCUBUS]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.FEDIEL))
    revived = p.field[1:]
    assert ids(revived) == [abyss.LULUMI.card_id, abyss.LILITH_ENCHANTING_SUCCUBUS.card_id]
    assert all(c.evolved for c in revived) and p.shadows == 0
    end_turns(state)
    assert (enemy.atk, enemy.life) == (3, 3)


def test_fediel_without_necromancy():
    state = start()
    p = state.players[0]
    p.shadows = 5
    p.destroyed.append(abyss.LULUMI)
    set_pp(state, 0, 7)
    play(state, give(state, 0, abyss.FEDIEL))
    assert len(p.field) == 1


def test_belial_clears_the_board():
    state = start()
    p = state.players[0]
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    belial = give(state, 0, abyss.BELIAL)
    play(state, belial)
    assert mine.fate == DESTROYED and theirs.fate == DESTROYED and belial.life == 6
    assert p.leader_area == []


def test_belial_super_skybound_art_and_super_evolve():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 7)
    belial = give(state, 0, abyss.BELIAL)
    E.counters(belial)["skybound"] = 14                 # + 1 own turn = 15
    play(state, belial)
    crest = p.leader_area[0]
    assert crest.defn == abyss.BELIAL_CREST and crest.countdown == 4
    unlock_evolution(state, 0)
    apply(state, Evolve(belial.uid, True))
    assert crest.countdown == 3


# --- fuzz -------------------------------------------------------------------------------------

def _needs_no_script(card) -> bool:
    flag = getattr(card, "has_ability", None)       # present once the pool records it
    if flag is not None:
        return not flag
    return card in abyss.KEYWORD_ONLY


def random_abyss_deck(rng: random.Random) -> list:
    pool = [c for c in collectible(Craft.ABYSS) if has_script(c.card_id) or _needs_no_script(c)]
    deck: list = []
    while len(deck) < decks.DECK_SIZE:
        c = rng.choice(pool)
        if deck.count(c) < decks.MAX_COPIES:
            deck.append(c)
    return deck


def _check(state, action):
    assert not state.queue
    for p in state.players:
        assert len(p.field) <= FIELD_LIMIT and len(p.hand) <= HAND_LIMIT
        assert all(c.life > 0 for c in p.followers), action


def test_random_abyss_games():
    for g in range(100):
        rng = random.Random(g)
        d0, d1 = random_abyss_deck(rng), random_abyss_deck(rng)
        assert decks.validate(d0, Craft.ABYSS) == [] and decks.validate(d1, Craft.ABYSS) == []
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=_check) in (0, 1, -1)
        assert state.over
