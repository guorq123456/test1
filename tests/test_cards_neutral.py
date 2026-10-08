"""Neutral cards, their tokens, crests and Accelerate forms."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, demo, neutral, sword
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.script import has_script, prop
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution
from test_fuzz import check_invariants


class FixedRng(random.Random):
    """Answers the first calls to sample() with the given picks, then plays fair."""

    def __init__(self, picks):
        super().__init__(0)
        self.picks = list(picks)

    def sample(self, population, k, **kwargs):
        if self.picks:
            return list(self.picks.pop(0))
        return super().sample(population, k, **kwargs)


def deck_of(state, player, *defns):
    """Replace a player's deck (the last card listed is drawn first)."""
    state.players[player].deck = [state.new_instance(d, player) for d in defns]


def fresh(pp=10):
    """Turn 1 for player 0 with an empty hand and `pp` play points."""
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, pp)
    return state


def end_round(state, n=1):
    """Pass n full rounds (own turn end, opponent's turn), back to the same player."""
    for _ in range(2 * n):
        apply(state, EndTurn())


# --- set 10009 ------------------------------------------------------------------------------

def test_jailor_of_antiquity_hits_the_selected_and_an_unselected_follower():
    state = fresh()
    big, small = put(state, 1, demo.GIANT), put(state, 1, demo.SHIELDBEARER)   # 5/5, 1/3
    jailor = give(state, 0, neutral.JAILOR_OF_ANTIQUITY)
    apply(state, PlayCard(jailor.uid, (big.uid,)))
    assert big.fate == DESTROYED and small.life == 1
    assert jailor.has(Keyword.WARD) and state.players[0].pp == 4


def test_jailor_random_part_hits_aura_when_nothing_can_be_selected():
    # Official Q&A: with only an Aura follower, the second part still deals 2 damage.
    state = fresh()
    aura = put(state, 1, neutral.YUNI)                                          # 3/3 Aura
    jailor = give(state, 0, neutral.JAILOR_OF_ANTIQUITY)
    assert [a.targets for a in plays(state, jailor.uid)] == [()]
    apply(state, PlayCard(jailor.uid))
    assert aura.life == 1


def test_jailor_accelerate_and_its_base_cost():
    state = fresh(pp=3)
    p = state.players[0]
    enemy = put(state, 1, demo.SHIELDBEARER)
    jailor = give(state, 0, neutral.JAILOR_OF_ANTIQUITY)
    apply(state, PlayCard(jailor.uid))
    assert enemy.life == 1 and p.pp == 2 and jailor not in p.field
    # Zerael Q&A: an accelerated Jailor's base cost is 1.
    assert p.played_base_costs == {1} and p.shadows == 1


def test_initiation_of_rebirth_shuffles_in_the_costliest_destroyed_follower():
    state = fresh()
    p = state.players[0]
    deck_of(state, 0, *[demo.FOOTMAN] * 5)
    p.destroyed = [demo.FOOTMAN, demo.GIANT, demo.LANCER]
    spell = give(state, 0, neutral.INITIATION_OF_REBIRTH)
    apply(state, PlayCard(spell.uid))
    assert count(p.deck + p.hand, demo.GIANT) == 1 and len(p.hand) == 1 and len(p.deck) == 5


def test_initiation_of_rebirth_with_nothing_destroyed_just_draws():
    state = fresh()
    p = state.players[0]
    spell = give(state, 0, neutral.INITIATION_OF_REBIRTH)
    deck = len(p.deck)
    apply(state, PlayCard(spell.uid))
    assert len(p.hand) == 1 and len(p.deck) == deck - 1


def test_blade_angel_buffs_two_other_allies():
    state = fresh()
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    angel = give(state, 0, neutral.BLADE_ANGEL)
    assert {a_.targets for a_ in plays(state, angel.uid)} == {(a.uid, b.uid)}
    apply(state, PlayCard(angel.uid, (a.uid, b.uid)))
    assert (a.atk, a.life) == (b.atk, b.life) == (4, 5) and (angel.atk, angel.life) == (6, 6)


def test_blade_angel_with_one_ally_buffs_it_alone():
    state = fresh()
    a = put(state, 0, demo.FOOTMAN)
    angel = give(state, 0, neutral.BLADE_ANGEL)
    assert [x.targets for x in plays(state, angel.uid)] == [(a.uid,)]
    apply(state, PlayCard(angel.uid, (a.uid,)))
    assert (a.atk, a.life) == (4, 5)


def test_warden_of_selflessness_counts_neutral_cards_in_hand():
    state = fresh()
    p = state.players[0]
    e1, e2 = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    give(state, 0, neutral.LEAH)                          # Neutral
    give(state, 0, sword.GILDED_BLADE)                    # Swordcraft
    warden = give(state, 0, neutral.WARDEN_OF_SELFLESSNESS)
    apply(state, PlayCard(warden.uid))
    assert p.hand[-1].defn == neutral.JAILOR_OF_ANTIQUITY
    assert e1.life == e2.life == 3                        # X = 2: Leah and the new Jailor


def test_warden_evolve_recovers_a_play_point():
    state = fresh(pp=3)
    state.players[0].pp = 1
    unlock_evolution(state, 0)
    warden = put(state, 0, neutral.WARDEN_OF_SELFLESSNESS)
    apply(state, Evolve(warden.uid))
    assert state.players[0].pp == 2


def test_azvaldt_destroys_itself_once_costs_one_to_eight_were_played():
    state = fresh()
    p = state.players[0]
    azvaldt = put(state, 0, neutral.AZVALDT)
    mine = put(state, 0, demo.FOOTMAN)
    p.played_base_costs = {1, 2, 3, 4, 5, 6, 7}
    apply(state, EndTurn())
    assert azvaldt.fate == IN_PLAY
    apply(state, EndTurn())
    p.destroyed = [demo.FOOTMAN, demo.FOOTMAN, demo.SHIELDBEARER, demo.RAIDER, demo.LANCER,
                   demo.GIANT]
    p.played_base_costs.add(8)
    apply(state, EndTurn())
    assert azvaldt.fate == DESTROYED
    summoned = [f for f in p.followers if f is not mine]
    assert len(summoned) == 4 and len({f.defn.name for f in summoned}) == 4
    assert all(f.atk == f.defn.atk + 3 and f.life == f.defn.life + 3 for f in summoned)
    assert (mine.atk, mine.life) == (4, 5)


def test_zerael_is_invoked_at_the_end_of_turn():
    state = fresh()
    p = state.players[0]
    zerael = state.new_instance(neutral.ZERAEL, 0)
    p.deck.insert(0, zerael)
    p.played_base_costs = {1, 2, 3, 4, 5, 6, 7}
    apply(state, EndTurn())
    assert zerael in p.deck
    apply(state, EndTurn())
    p.played_base_costs.add(8)
    apply(state, EndTurn())
    assert zerael in p.field and zerael.has(Keyword.INTIMIDATE)


def test_zerael_fanfare():
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    zerael = give(state, 0, neutral.ZERAEL)
    apply(state, PlayCard(zerael.uid, (enemy.uid,)))
    assert enemy.fate == DESTROYED


def test_azvaldt_last_words_buffs_the_invoked_zerael():
    # Official Q&A: Azvaldt is destroyed, Zerael is invoked, then Azvaldt's Last Words.
    state = fresh()
    p = state.players[0]
    put(state, 0, neutral.AZVALDT)
    zerael = state.new_instance(neutral.ZERAEL, 0)
    p.deck.insert(0, zerael)
    p.played_base_costs = set(range(1, 9))
    p.destroyed = [demo.FOOTMAN]
    apply(state, EndTurn())
    assert zerael in p.field and (zerael.atk, zerael.life) == (12, 12)
    assert count(p.field, demo.FOOTMAN) == 1


def test_zerael_is_invoked_into_the_space_azvaldt_leaves():
    state = fresh()
    p = state.players[0]
    put(state, 0, neutral.AZVALDT)
    for _ in range(4):
        put(state, 0, demo.FOOTMAN)
    zerael = state.new_instance(neutral.ZERAEL, 0)
    p.deck.insert(0, zerael)
    p.played_base_costs = set(range(1, 9))
    apply(state, EndTurn())
    assert zerael in p.field


# --- set 10008 ------------------------------------------------------------------------------

def test_hamsa_evolve():
    state = fresh()
    unlock_evolution(state, 0)
    hamsa = put(state, 0, neutral.HAMSA)
    apply(state, Evolve(hamsa.uid))
    assert (hamsa.atk, hamsa.life) == (8, 8)


def test_reina_recovers_an_evolution_point():
    state = fresh()
    state.players[0].ep = 0
    reina = give(state, 0, neutral.REINA)
    apply(state, PlayCard(reina.uid))
    assert state.players[0].ep == 1


def test_olivia_recovers_two_super_evolution_points():
    state = fresh()
    state.players[0].sep = 0
    olivia = give(state, 0, neutral.OLIVIA)
    apply(state, PlayCard(olivia.uid))
    assert state.players[0].sep == 2 and olivia.has(Keyword.WARD)


def test_alfied_fanfare_and_evolve_storm():
    state = fresh()
    unlock_evolution(state, 0)
    enemy = put(state, 1, demo.SHIELDBEARER)
    alfied = give(state, 0, neutral.ALFIED)
    apply(state, PlayCard(alfied.uid, (enemy.uid,)))
    assert enemy.fate == DESTROYED
    assert Attack(alfied.uid, leader_uid(1)) not in legal_actions(state)
    apply(state, Evolve(alfied.uid))
    assert Attack(alfied.uid, leader_uid(1)) in legal_actions(state)


def test_legacy_of_the_brave_copies_an_opponent_card():
    state = fresh()
    p, opp = state.players
    opp.hand.clear()
    original = give(state, 1, demo.GIANT)
    E.add_cost(original, -2)                               # an exact copy keeps this
    spell = give(state, 0, neutral.LEGACY_OF_THE_BRAVE)
    apply(state, PlayCard(spell.uid))
    copy = p.hand[0]
    assert copy.defn == demo.GIANT and copy.owner == 0 and copy.cost == 2 and copy is not original
    assert len(p.hand) == 2 and len(opp.hand) == 1


def test_aika_fanfare_and_evolve_recall_destroyed_followers():
    state = fresh()
    unlock_evolution(state, 0)
    p = state.players[0]
    aika = give(state, 0, neutral.AIKA)
    apply(state, PlayCard(aika.uid))
    assert p.hand == []                                    # nothing destroyed yet
    p.destroyed = [demo.GIANT]
    apply(state, Evolve(aika.uid))
    assert [c.defn for c in p.hand] == [demo.GIANT]


def test_wills_united_modes():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.SHIELDBEARER)
    ally = put(state, 0, demo.FOOTMAN)
    spell = give(state, 0, neutral.WILLS_UNITED)
    assert {a.modes for a in plays(state, spell.uid)} == {(0,), (1,), (2,)}
    apply(state, PlayCard(spell.uid, modes=(0,)))
    assert enemy.fate == DESTROYED
    spell = give(state, 0, neutral.WILLS_UNITED)
    apply(state, PlayCard(spell.uid, modes=(2,)))
    assert ally.atk == 2 and ally.life == 2
    p.destroyed = [demo.RAIDER, demo.LANCER]               # Reanimate (2): the Raider
    spell = give(state, 0, neutral.WILLS_UNITED)
    apply(state, PlayCard(spell.uid, modes=(1,)))
    assert count(p.field, demo.RAIDER) == 1 and count(p.field, demo.LANCER) == 0


def test_alabaster_bahamut_banishes_followers():
    state = fresh()
    mine, theirs = put(state, 0, demo.BOMBER), put(state, 1, demo.BOMBER)
    totem = put(state, 1, demo.TOTEM)
    bahamut = give(state, 0, neutral.ALABASTER_BAHAMUT)
    apply(state, PlayCard(bahamut.uid, modes=(0,)))
    assert mine.fate == theirs.fate == BANISHED and totem.fate == IN_PLAY
    assert bahamut in state.players[0].field and state.players[0].leader_hp == 20


def test_alabaster_bahamut_banishes_amulets():
    state = fresh()
    mine, theirs = put(state, 0, demo.TOTEM), put(state, 1, demo.TOTEM)
    follower = put(state, 1, demo.FOOTMAN)
    bahamut = give(state, 0, neutral.ALABASTER_BAHAMUT)
    apply(state, PlayCard(bahamut.uid, modes=(1,)))
    assert mine.fate == theirs.fate == BANISHED and follower.fate == IN_PLAY
    assert count(state.players[1].field, demo.WISP) == 0   # no Last Words


def test_alabaster_bahamut_banishes_crests_but_not_faiths():
    # Official Q&A: option 3 doesn't banish faiths.
    state = fresh()
    crest = E.add_to_leader_area(state, 1, sword.UNKEI_CREST)
    own_crest = E.add_to_leader_area(state, 0, neutral.SANDALPHON_CREST)
    faith = E.add_to_leader_area(state, 1, sword.ELD_SWORD_FAITH)
    bahamut = give(state, 0, neutral.ALABASTER_BAHAMUT)
    apply(state, PlayCard(bahamut.uid, modes=(2,)))
    assert crest.fate == own_crest.fate == BANISHED
    assert state.players[1].leader_area == [faith]


# --- set 10007 ------------------------------------------------------------------------------

def test_altaro_superfan_evolve_draws_a_neutral_card():
    state = fresh()
    unlock_evolution(state, 0)
    p = state.players[0]
    deck_of(state, 0, sword.GILDED_BLADE, neutral.LEAH, sword.GILDED_GOBLET)
    fan = put(state, 0, neutral.ALTARO_SUPERFAN)
    apply(state, Evolve(fan.uid))
    assert [c.defn for c in p.hand] == [neutral.LEAH]


def test_tears_of_degradation_banishes_an_enemy_card():
    state = fresh()
    spell = give(state, 0, neutral.TEARS_OF_DEGRADATION)
    assert plays(state, spell.uid) == []                   # needs a target
    totem = put(state, 1, demo.TOTEM)
    bomber = put(state, 1, demo.BOMBER)
    assert {a.targets for a in plays(state, spell.uid)} == {(totem.uid,), (bomber.uid,)}
    apply(state, PlayCard(spell.uid, (bomber.uid,)))
    assert bomber.fate == BANISHED and state.players[0].leader_hp == 20


def test_intrepid_newshound_last_words_and_super_evolve():
    state = fresh()
    unlock_evolution(state, 0)
    p = state.players[0]
    hound = put(state, 0, neutral.INTREPID_NEWSHOUND)
    apply(state, Evolve(hound.uid, super_=True))
    assert count(p.field, neutral.INTREPID_NEWSHOUND) == 3
    E.destroy(state, hound, by_ability=False)    # super-evolved: immune to abilities on our turn
    resolve_queue(state)
    assert len(p.hand) == 1


def test_intrepid_newshound_evolve_summons_nothing():
    state = fresh()
    unlock_evolution(state, 0)
    hound = put(state, 0, neutral.INTREPID_NEWSHOUND)
    apply(state, Evolve(hound.uid))
    assert count(state.players[0].field, neutral.INTREPID_NEWSHOUND) == 1


def test_hedonistic_socialite_discards_and_sweeps():
    state = fresh()
    p = state.players[0]
    enemies = [put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER)]
    junk = give(state, 0, demo.FOOTMAN)
    socialite = give(state, 0, neutral.HEDONISTIC_SOCIALITE)
    apply(state, PlayCard(socialite.uid, (junk.uid,)))
    assert p.hand == [] and p.shadows == 1
    assert enemies[0].fate == DESTROYED and enemies[1].life == 1


def test_city_of_babelon_runs_out_without_a_delay():
    state = fresh(pp=1)
    enemy = put(state, 1, demo.SHIELDBEARER)               # 1/3
    city = give(state, 0, neutral.CITY_OF_BABELON)
    apply(state, PlayCard(city.uid))
    assert city.countdown == 1
    apply(state, EndTurn())                                # step 1: 2 damage to an enemy follower
    assert enemy.life == 1
    end_round(state)                                       # Countdown (1) runs out on our next turn
    assert city.fate == DESTROYED and state.players[0].leader_hp == 20


def test_city_of_babelon_engage_delays_and_finishes_the_sequence():
    state = fresh(pp=3)
    p, opp = state.players
    enemy = put(state, 1, demo.SHIELDBEARER)
    city = give(state, 0, neutral.CITY_OF_BABELON)
    apply(state, PlayCard(city.uid))
    junk = give(state, 0, demo.FOOTMAN)
    assert Engage(city.uid, (junk.uid,)) in legal_actions(state)
    apply(state, Engage(city.uid, (junk.uid,)))
    assert junk not in p.hand and p.shadows == 1 and p.pp == 1 and city.countdown == 2
    give(state, 0, demo.FOOTMAN)
    assert not any(isinstance(a, Engage) for a in legal_actions(state))   # once per turn
    p.leader_hp = 10
    apply(state, EndTurn())                                # step 1
    assert enemy.life == 1
    apply(state, EndTurn())
    assert city.countdown == 1
    apply(state, Engage(city.uid, (p.hand[0].uid,)))
    apply(state, EndTurn())                                # step 2: restore 2
    assert p.leader_hp == 12 and city.fate == IN_PLAY
    apply(state, EndTurn())
    apply(state, Engage(city.uid, (p.hand[0].uid,)))
    apply(state, EndTurn())                                # step 3: 2 to the enemy leader, destroyed
    assert opp.leader_hp == 18 and city.fate == DESTROYED


def test_illamrita_strike_designates_the_defender():
    state = fresh()
    illamrita = put(state, 0, neutral.ILLAMRITA)           # 1/4
    giant = put(state, 1, demo.GIANT)                      # 5/5
    apply(state, Attack(illamrita.uid, giant.uid))
    assert illamrita.life == 4 and not illamrita.has(Keyword.BARRIER)   # Barrier took the hit
    assert giant.life == 4 and prop(giant, "cant_attack")
    apply(state, EndTurn())
    assert giant.fate == IN_PLAY
    assert not any(isinstance(a, Attack) and a.attacker == giant.uid for a in legal_actions(state))
    apply(state, EndTurn())                                # end of the giant's controller's turn
    assert giant.fate == BANISHED


def test_illamrita_leader_attack_does_nothing_special():
    state = fresh()
    illamrita = put(state, 0, neutral.ILLAMRITA)
    apply(state, Attack(illamrita.uid, leader_uid(1)))
    assert not illamrita.has(Keyword.BARRIER) and state.players[1].leader_hp == 19


def test_illamrita_crest_brings_her_back_evolved():
    state = fresh()
    p = state.players[0]
    illamrita = put(state, 0, neutral.ILLAMRITA)
    E.destroy(state, illamrita)
    resolve_queue(state)
    crest = E.leader_area_card(state, 0, neutral.ILLAMRITA_CREST)
    assert crest is not None and crest.countdown == 2
    end_round(state)
    assert crest.countdown == 1 and p.followers == []
    end_round(state)
    assert crest.fate == DESTROYED
    back = p.followers[0]
    assert back.defn == neutral.ILLAMRITA and back.evolved and (back.atk, back.life) == (3, 6)


def test_altaro_mayor_draws_at_the_end_of_turn():
    state = fresh()
    mayor = put(state, 0, neutral.ALTARO_MAYOR)
    apply(state, EndTurn())
    assert len(state.players[0].hand) == 1 and mayor.has(Keyword.AMBUSH)


# --- set 10006 ------------------------------------------------------------------------------

def test_muddled_onlooker_last_words():
    state = fresh()
    onlooker = put(state, 0, neutral.MUDDLED_ONLOOKER)
    E.destroy(state, onlooker)
    resolve_queue(state)
    assert state.players[1].leader_hp == 19


def test_disrupted_commoner_destroys_a_follower():
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    commoner = give(state, 0, neutral.DISRUPTED_COMMONER)
    apply(state, PlayCard(commoner.uid, (enemy.uid,)))
    assert enemy.fate == DESTROYED and commoner.has(Keyword.BANE)


def test_encroached_world_transforms_a_hand_card():
    state = fresh(pp=0)
    p = state.players[0]
    world = put(state, 0, neutral.ENCROACHED_WORLD)
    original = state.new_instance(demo.GIANT, 1)
    E.add_cost(original, -1)
    state.players[1].deck = [original]
    target = give(state, 0, demo.FOOTMAN)
    apply(state, Engage(world.uid, (target.uid,)))
    assert p.hand == [target] and target.defn == demo.GIANT and target.cost == 4
    assert target.owner == 0 and state.players[1].deck == [original]
    assert not any(isinstance(a, Engage) for a in legal_actions(state))


def test_encroached_world_can_engage_with_an_empty_hand():
    # Official Q&A: yes, and nothing happens.
    state = fresh(pp=0)
    world = put(state, 0, neutral.ENCROACHED_WORLD)
    assert Engage(world.uid, ()) in legal_actions(state)
    apply(state, Engage(world.uid, ()))
    assert world.fate == IN_PLAY


def test_beast_lost_to_the_dark_gets_three_random_abilities():
    abilities = Keyword.STORM | Keyword.BANE | Keyword.INTIMIDATE | Keyword.DRAIN | Keyword.AURA \
        | Keyword.BARRIER
    seen = set()
    for seed in range(8):
        state = start(seed=seed)
        set_pp(state, 0, 6)
        beast = give(state, 0, neutral.BEAST_LOST_TO_THE_DARK)
        apply(state, PlayCard(beast.uid))
        gained = beast.keywords & abilities
        assert bin(int(gained)).count("1") == 3
        seen.add(int(gained))
    assert len(seen) > 1


def test_dark_dimensions_spares_encroachers():
    state = fresh()
    dims = put(state, 0, neutral.DARK_DIMENSIONS)
    mine, theirs = put(state, 0, demo.SHIELDBEARER), put(state, 1, demo.GIANT)
    omegotep = put(state, 0, neutral.OMEGOTEP)
    apply(state, EndTurn())
    assert mine.life == 1 and theirs.life == 3 and omegotep.life == 4
    assert dims.countdown == 2


def test_omegotep_two_random_abilities():
    state = fresh(pp=9)
    p, opp = state.players
    enemy = put(state, 1, demo.GIANT)
    omegotep = give(state, 0, neutral.OMEGOTEP)
    state.rng = FixedRng([(0, 1)])                         # destroy + 2 to the enemy leader
    apply(state, PlayCard(omegotep.uid))
    assert enemy.fate == DESTROYED and opp.leader_hp == 18 and p.pp == 0
    assert (omegotep.atk, omegotep.life) == (4, 4)


def test_omegotep_fourth_ability_activates_the_fanfare_again():
    state = fresh(pp=9)
    p, opp = state.players
    omegotep = give(state, 0, neutral.OMEGOTEP)
    state.rng = FixedRng([(3, 2), (1, 2)])                 # +4/+4, recover 2, then again
    apply(state, PlayCard(omegotep.uid))
    assert (omegotep.atk, omegotep.life) == (8, 8)
    assert p.pp == 4 and opp.leader_hp == 18


def test_omegotep_super_evolve_replicates_the_fanfare():
    state = fresh(pp=5)
    state.players[0].pp = 0
    unlock_evolution(state, 0)
    opp = state.players[1]
    omegotep = put(state, 0, neutral.OMEGOTEP)
    state.rng = FixedRng([(1, 2)])
    apply(state, Evolve(omegotep.uid, super_=True))
    assert opp.leader_hp == 18 and state.players[0].pp == 2
    state = fresh(pp=0)
    unlock_evolution(state, 0)
    omegotep = put(state, 0, neutral.OMEGOTEP)
    state.rng = FixedRng([(1, 2)])
    apply(state, Evolve(omegotep.uid))                     # plain evolve: nothing
    assert state.players[1].leader_hp == 20


# --- set 10005 ------------------------------------------------------------------------------

def test_monster_litterateur_needs_another_one_cost_card():
    state = fresh()
    monster = give(state, 0, neutral.MONSTER_LITTERATEUR)
    put(state, 0, demo.SHIELDBEARER)
    apply(state, PlayCard(monster.uid))
    assert (monster.atk, monster.life) == (1, 1)
    put(state, 1, demo.FOOTMAN)                            # either side counts
    monster = give(state, 0, neutral.MONSTER_LITTERATEUR)
    apply(state, PlayCard(monster.uid))
    assert (monster.atk, monster.life) == (2, 2)


def test_goddess_of_starlight_discards_three_and_copies_the_leftmost():
    state = fresh()
    unlock_evolution(state, 0)
    p = state.players[0]
    goddess = put(state, 0, neutral.GODDESS_OF_STARLIGHT)
    junk = [give(state, 0, demo.FOOTMAN) for _ in range(3)]
    keep = [give(state, 0, d) for d in (demo.GIANT, demo.LANCER, demo.RAIDER, demo.BOMBER)]
    E.add_cost(keep[0], -2)
    apply(state, Evolve(goddess.uid, targets=tuple(c.uid for c in junk)))
    assert p.shadows == 3
    assert [c.defn for c in p.hand] == [demo.GIANT, demo.LANCER, demo.RAIDER, demo.BOMBER,
                                        demo.GIANT, demo.LANCER, demo.RAIDER]
    assert p.hand[4].cost == 3                             # exact copy


def test_behemoth_general_compares_the_three_highest_base_costs():
    for theirs, destroyed in (((demo.GIANT, demo.FOOTMAN), True),
                              ((demo.GIANT, demo.GIANT, demo.FOOTMAN), False)):
        state = fresh()
        unlock_evolution(state, 0)
        state.players[1].hand.clear()
        for d in theirs:
            give(state, 1, d)
        for d in (demo.GIANT, demo.LANCER, demo.FOOTMAN, demo.FOOTMAN):   # 5 + 3 + 1 = 9
            give(state, 0, d)
        enemy = put(state, 1, demo.GIANT)
        general = put(state, 0, neutral.BEHEMOTH_GENERAL)
        apply(state, Evolve(general.uid))
        assert (enemy.fate == DESTROYED) == destroyed      # 9 > 6, but not 9 > 11


def test_world_of_games_advances_on_matching_base_costs():
    state = fresh()
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    put(state, 1, demo.LANCER)                             # base cost 3
    apply(state, PlayCard(give(state, 0, neutral.HAMSA).uid))   # cost 2: no match
    assert games.countdown == 5
    apply(state, PlayCard(give(state, 0, neutral.ALTARO_MAYOR).uid))   # cost 3: match
    assert games.countdown == 4


def test_world_of_games_checks_the_field_as_the_card_is_played():
    # Official Q&A: a spell that destroys the only matching card still advances the count.
    state = fresh(pp=5)
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    giant = put(state, 1, demo.GIANT)                      # base cost 5
    fate = give(state, 0, neutral.FATE_OF_THE_WORLD)       # cost 5: destroys the giant
    apply(state, PlayCard(fate.uid))
    assert giant.fate == DESTROYED and games.countdown == 4


def test_world_of_games_counts_a_follower_destroyed_by_the_played_fanfare():
    state = fresh()
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    giant = put(state, 1, demo.GIANT)                      # base cost 5
    commoner = give(state, 0, neutral.DISRUPTED_COMMONER)  # cost 5
    apply(state, PlayCard(commoner.uid, (giant.uid,)))
    assert giant.fate == DESTROYED and games.countdown == 4


def test_world_of_games_ignores_cards_summoned_by_the_played_follower():
    state = fresh(pp=4)
    p = state.players[0]
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    zeta = give(state, 0, sword.ZETA_AND_BEA)             # cost 4; its Fanfare summons another
    apply(state, PlayCard(zeta.uid))
    assert count(p.field, sword.ZETA_AND_BEA) == 2 and games.countdown == 5
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, sword.ZETA_AND_BEA).uid))   # now they match
    assert games.countdown == 4


def test_world_of_games_last_words_draws_two():
    state = fresh()
    p = state.players[0]
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    games.countdown = 1
    put(state, 1, demo.FOOTMAN)
    apply(state, PlayCard(give(state, 0, neutral.MONSTER_LITTERATEUR).uid))
    assert games.fate == DESTROYED and len(p.hand) == 2


def test_world_of_games_uses_the_accelerate_base_cost():
    state = fresh(pp=1)
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    put(state, 1, demo.FOOTMAN)                            # base cost 1, like Jailor's Accelerate
    apply(state, PlayCard(give(state, 0, neutral.JAILOR_OF_ANTIQUITY).uid))
    assert games.countdown == 4


def test_getenou_modes():
    state = fresh()
    p = state.players[0]
    for _ in range(3):
        give(state, 0, demo.FOOTMAN)
    getenou = give(state, 0, neutral.GETENOU)
    assert {a.modes for a in plays(state, getenou.uid)} == {(0,), (1,)}
    apply(state, PlayCard(getenou.uid, modes=(0,)))
    assert p.shadows == 3 and len(p.hand) == 8
    state = fresh()
    p = state.players[0]
    deck_of(state, 0, *[demo.GIANT] * 5)
    give(state, 0, demo.FOOTMAN)
    getenou = give(state, 0, neutral.GETENOU)
    apply(state, PlayCard(getenou.uid, modes=(1,)))
    assert [(c.defn, c.cost) for c in p.hand] == [(demo.GIANT, 0)] * 2


# --- set 10000 ------------------------------------------------------------------------------

def test_indomitable_fighter_enhance():
    for pp, stats in ((2, (2, 2)), (4, (5, 5))):
        state = fresh(pp=pp)
        fighter = give(state, 0, neutral.INDOMITABLE_FIGHTER)
        apply(state, PlayCard(fighter.uid))
        assert (fighter.atk, fighter.life) == stats and state.players[0].pp == 0


def test_leah_draws_on_evolve_and_last_words():
    state = fresh()
    unlock_evolution(state, 0)
    p = state.players[0]
    leah = put(state, 0, neutral.LEAH)
    apply(state, Evolve(leah.uid))
    assert len(p.hand) == 1
    E.destroy(state, leah)
    resolve_queue(state)
    assert len(p.hand) == 2


def test_detectives_lens_removes_ward():
    state = fresh(pp=0)
    lens = put(state, 0, neutral.DETECTIVES_LENS)
    warded, plain = put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.FOOTMAN)
    assert [a.targets for a in legal_actions(state) if isinstance(a, Engage)] == [(warded.uid,)]
    apply(state, Engage(lens.uid, (warded.uid,)))
    assert lens.fate == DESTROYED and not warded.has(Keyword.WARD)
    assert plain.fate == IN_PLAY


def test_detectives_lens_with_no_ward_follower_just_breaks():
    # Official Q&A: it can be engaged; it's simply destroyed.
    state = fresh(pp=0)
    lens = put(state, 0, neutral.DETECTIVES_LENS)
    apply(state, Engage(lens.uid, ()))
    assert lens.fate == DESTROYED


def test_arriet_evolve_and_super_evolve():
    for super_, hp in ((False, 12), (True, 14)):
        state = fresh()
        unlock_evolution(state, 0)
        state.players[0].leader_hp = 10
        arriet = put(state, 0, neutral.ARRIET)
        apply(state, Evolve(arriet.uid, super_=super_))
        assert state.players[0].leader_hp == hp


def test_adventurers_guild_draws_a_follower_and_gives_rush():
    state = fresh(pp=3)
    p = state.players[0]
    deck_of(state, 0, demo.GIANT, sword.GILDED_BLADE)
    guild = give(state, 0, neutral.ADVENTURERS_GUILD)
    apply(state, PlayCard(guild.uid))
    assert [c.defn for c in p.hand] == [demo.GIANT]
    fresh_ally = put(state, 0, demo.FOOTMAN, ready=False)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Engage(guild.uid, (fresh_ally.uid,)))
    assert guild.fate == DESTROYED and fresh_ally.has(Keyword.RUSH)
    assert Attack(fresh_ally.uid, enemy.uid) in legal_actions(state)


def test_adventurers_guild_engages_without_followers():
    # Official Q&A: it can be engaged with no allied follower; it's simply destroyed.
    state = fresh(pp=0)
    guild = put(state, 0, neutral.ADVENTURERS_GUILD)
    apply(state, Engage(guild.uid, ()))
    assert guild.fate == DESTROYED


# --- set 10004 ------------------------------------------------------------------------------

def test_katalina_skybound_art_and_damage_cap():
    state = fresh()
    e1, e2 = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    katalina = give(state, 0, neutral.KATALINA)
    apply(state, PlayCard(katalina.uid))
    assert e1.life == e2.life == 5                         # gauge 1: no Skybound Art
    E.damage(state, [katalina], 5)
    assert katalina.life == 2                              # took 3
    state = fresh()
    e1, e2 = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    katalina = give(state, 0, neutral.KATALINA)
    E.counters(katalina)["skybound"] = 9                   # turn 1 + 9 = 10
    apply(state, PlayCard(katalina.uid))
    assert e1.fate == e2.fate == DESTROYED


def test_skybound_gauge_counts_evolutions_while_in_hand():
    state = fresh()
    unlock_evolution(state, 0)                             # 8 turns taken
    katalina = give(state, 0, neutral.KATALINA)
    for _ in range(2):
        ally = put(state, 0, demo.FOOTMAN)
        state.players[0].evolved_this_turn = False
        apply(state, Evolve(ally.uid))
    assert E.skybound_gauge(state, katalina) == 10


def test_vyrn_evolves_once_super_evolution_is_unlocked():
    state = fresh()
    vyrn = give(state, 0, neutral.VYRN)
    apply(state, PlayCard(vyrn.uid))
    assert not vyrn.evolved
    state = fresh()
    unlock_evolution(state, 0)
    vyrn = give(state, 0, neutral.VYRN)
    apply(state, PlayCard(vyrn.uid))
    assert vyrn.evolved and not vyrn.super_evolved and (vyrn.atk, vyrn.life) == (4, 4)
    assert state.players[0].ep == 2


def test_yuni_heals_all_allies():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 15
    yuni = put(state, 0, neutral.YUNI)
    ally = put(state, 0, demo.SHIELDBEARER)
    ally.life = 1
    yuni.life = 2
    enemy = put(state, 1, demo.SHIELDBEARER)
    enemy.life = 1
    apply(state, EndTurn())
    assert p.leader_hp == 16 and ally.life == 2 and yuni.life == 3 and enemy.life == 1


def test_gran_and_djeeta_modes_and_skybound_art():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    gd = give(state, 0, neutral.GRAN_AND_DJEETA)
    assert {a.modes for a in plays(state, gd.uid)} == {(0,), (1,)}
    apply(state, PlayCard(gd.uid, modes=(0,)))
    assert enemy.fate == DESTROYED and not gd.evolved
    state = fresh()
    p = state.players[0]
    deck_of(state, 0, demo.GIANT, sword.GILDED_BLADE, demo.LANCER, sword.GILDED_GOBLET)
    gd = give(state, 0, neutral.GRAN_AND_DJEETA)
    E.counters(gd)["skybound"] = 9
    apply(state, PlayCard(gd.uid, modes=(1,)))
    assert sorted(c.defn.name for c in p.hand) == ["Giant", "Lancer"]
    assert gd.evolved and (gd.atk, gd.life) == (5, 4)


def test_sandalphon_invoked_returns_to_hand_with_its_cost_reset():
    # Official Q&A: a returned card loses its cost changes.
    state = fresh()
    p = state.players[0]
    sandalphon = state.new_instance(neutral.SANDALPHON, 0)
    E.set_cost(sandalphon, 3)
    p.deck.insert(0, sandalphon)
    p.evolutions = 5
    end_round(state)
    assert sandalphon in p.deck
    p.deck.remove(sandalphon)
    p.deck.append(sandalphon)                              # on top: still invoked before the draw
    p.evolutions = 6
    p.hand.clear()
    end_round(state)
    assert E.leader_area_card(state, 0, neutral.SANDALPHON_CREST) is not None
    returned = [c for c in p.hand if c.defn == neutral.SANDALPHON]
    assert len(returned) == 1 and returned[0].cost == 6
    assert len(p.hand) == 2 and p.followers == []          # plus the turn's draw


def test_sandalphon_destroyed_by_trap_in_the_woods_still_gives_its_crest():
    # Confirmed by the player: the trap destroys the invoked Sandalphon, and the crest comes anyway.
    from svsim.cards import forest
    state = fresh()
    trap = put(state, 0, forest.TRAP_IN_THE_WOODS)
    p = state.players[1]
    sandalphon = state.new_instance(neutral.SANDALPHON, 1)
    p.deck.append(sandalphon)
    p.evolutions = 6
    apply(state, EndTurn())
    assert sandalphon.fate == DESTROYED and trap.fate == DESTROYED
    assert E.leader_area_card(state, 1, neutral.SANDALPHON_CREST) is not None
    assert not any(c.defn == neutral.SANDALPHON for c in p.hand)


def test_azvaldt_favours_names_destroyed_more_often():
    # Confirmed by the player: the more often a follower was destroyed, the likelier its name.
    others = [demo.SHIELDBEARER, demo.RAIDER, demo.LANCER, demo.ASSASSIN, demo.LEECH]
    footman_summoned = 0
    for seed in range(200):
        state = start(seed=seed)
        p = state.players[0]
        azvaldt = put(state, 0, neutral.AZVALDT)
        p.destroyed = [demo.FOOTMAN] * 20 + others
        E.destroy(state, azvaldt)
        resolve_queue(state)
        assert len({c.defn.name for c in p.followers}) == 4
        footman_summoned += count(p.followers, demo.FOOTMAN)
    assert footman_summoned >= 190                         # uniform by name would give ~133


def test_sandalphon_super_skybound_art():
    state = fresh(pp=6)
    sandalphon = give(state, 0, neutral.SANDALPHON)
    apply(state, PlayCard(sandalphon.uid))
    assert state.players[1].leader_hp == 20                # gauge 1
    state = fresh(pp=6)
    sandalphon = give(state, 0, neutral.SANDALPHON)
    E.counters(sandalphon)["skybound"] = 14
    apply(state, PlayCard(sandalphon.uid))
    assert state.players[1].leader_hp == 10                # 5 x 2 at the only enemy


def test_sandalphon_damage_re_rolls_between_followers_and_the_leader():
    totals = set()
    for seed in range(10):
        state = start(seed=seed)
        set_pp(state, 0, 6)
        enemies = [put(state, 1, demo.GIANT) for _ in range(2)]
        sandalphon = give(state, 0, neutral.SANDALPHON)
        E.counters(sandalphon)["skybound"] = 14
        apply(state, PlayCard(sandalphon.uid))
        dealt = (20 - state.players[1].leader_hp) + sum(5 - e.life for e in enemies)
        assert dealt == 10
        totals.add(state.players[1].leader_hp)
    assert len(totals) > 1


def test_sandalphon_crest_heals_all_allies_then_expires():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    crest = E.add_to_leader_area(state, 0, neutral.SANDALPHON_CREST)
    ally = put(state, 0, demo.SHIELDBEARER)
    ally.life = 1
    apply(state, EndTurn())
    assert p.leader_hp == 11 and ally.life == 2
    end_round(state)
    assert crest.countdown == 1
    end_round(state)
    assert crest.fate == DESTROYED and p.leader_hp == 12


# --- coverage and fuzzing ---------------------------------------------------------------------

def test_every_neutral_card_is_scripted_or_needs_no_script():
    neutral_pool = [c for c in collectible(Craft.NEUTRAL) if c.craft == Craft.NEUTRAL]
    assert sorted(c.card_id for c in neutral_pool) == sorted(c.card_id for c in neutral.CARDS)
    extra = neutral.LEADER_AREA + neutral.ALTERNATE_FORMS
    assert decks.unimplemented(neutral_pool + extra) == []
    assert all(has_script(c.card_id) for c in extra)
    assert {c.name for c in neutral_pool if not c.has_ability} == {"Quake Goliath", "Caravan Mammoth"}


def _random_neutral_deck(rng):
    """40 Neutral cards, up to 3 copies each, skipping any that would need a missing script."""
    pool = [c for c in collectible(Craft.NEUTRAL)
            if c.craft == Craft.NEUTRAL and (has_script(c.card_id) or not c.has_ability)]
    return rng.sample([c for c in pool for _ in range(3)], 40)


def test_random_neutral_games():
    for g in range(100):
        rng = random.Random(g)
        d0, d1 = _random_neutral_deck(rng), _random_neutral_deck(rng)
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
        assert state.over


def test_the_start_of_turn_resolves_in_the_order_of_sandalphon_s_official_q_and_a():
    # Official Q&A on Sandalphon, Primarch Successor (its card page), with a Serene Sanctuary at count 1: "First,
    # Serene Sanctuary's count falls to 0 and it is destroyed. Then, Sandalphon's Invoke ability summons him to
    # your field. Next, Serene Sanctuary's Last Words ability activates and you draw 2 cards. Sandalphon's 'When
    # this card is invoked' ability then returns him to your hand. Finally, you'll draw your card for the turn."
    # (Every answer there ends with the turn's draw: Invocation comes before it.) Serene Sanctuary has no script
    # here; Scripture of Salvation (Countdown, Last Words: draw 2 cards, ...) stands in for it.
    from svsim.cards import library  # noqa: F401  (every card's script registered)
    from svsim.cards.pool import POOL
    state = fresh()
    p = state.players[0]
    sanctuary = put(state, 0, POOL[10662210])                               # Scripture of Salvation
    sanctuary.countdown = 1                                                 # falls to 0 at my next turn's start
    sandalphon = state.new_instance(neutral.SANDALPHON, 0)
    p.deck.append(sandalphon)                                               # on top: the draw would take it
    below = list(p.deck[-4:-1])                                             # the next cards under it
    p.evolutions = 6
    p.hand.clear()
    end_round(state)
    assert p.hand[:2] == [below[-1], below[-2]]                             # the Last Words' 2 cards
    assert p.hand[2].defn == neutral.SANDALPHON                             # back to hand when invoked
    assert p.hand[3] is below[-3] and len(p.hand) == 4                      # the turn's draw, last
    assert E.leader_area_card(state, 0, neutral.SANDALPHON_CREST) is not None and sanctuary not in p.field
