"""Havencraft cards, tokens, crests, faith and Crystallize forms."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import demo, haven as H
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, has_script
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution
from test_fuzz import check_invariants

ENEMY_LEADER = leader_uid(1)


def play(state, inst, targets=(), modes=()):
    apply(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def end_turns(state, n=1):
    for _ in range(n):
        apply(state, EndTurn())


def hurt(state, player=0, hp=10):
    state.players[player].leader_hp = hp


def ids(cards):
    return [c.defn.card_id for c in cards]


def amulets_on_field(state, player=0, n=3):
    return [put(state, player, demo.TOTEM) for _ in range(n)]


class ThreeAttacks(CardScript):
    attacks_per_turn = 3


# --- Basic ---------------------------------------------------------------------------------

def test_soulcure_sister_heals_five():
    state = start()
    hurt(state)
    set_pp(state, 0, 6)
    play(state, give(state, 0, H.SOULCURE_SISTER))
    assert state.players[0].leader_hp == 15


def test_winged_warrior_buffs_another_ally_on_fanfare_and_evolve():
    state = start()
    ally = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 4)
    warrior = give(state, 0, H.WINGED_WARRIOR)
    assert plays(state, warrior.uid) == [PlayCard(warrior.uid, (ally.uid,))]   # not itself
    play(state, warrior, [ally.uid])
    assert (ally.atk, ally.life) == (2, 3)
    unlock_evolution(state, 0)
    apply(state, Evolve(warrior.uid, False, (ally.uid,)))
    assert (ally.atk, ally.life) == (3, 4)


def test_avian_statue_engage_advances_by_two_and_summons_regal_falcon():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 6)
    statue = give(state, 0, H.AVIAN_STATUE)
    play(state, statue)
    assert statue.countdown == 2
    apply(state, Engage(statue.uid))
    assert statue.fate == DESTROYED and p.pp == 0
    assert ids(p.field) == [H.REGAL_FALCON.card_id]


def test_ironfist_priest_evolve_banishes_one_small_enemy():
    state = start()
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    priest = put(state, 0, H.IRONFIST_PRIEST)
    unlock_evolution(state, 0)
    targets = {a.targets for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == priest.uid}
    assert targets == {(small.uid,)}                      # 3 defense or less only
    apply(state, Evolve(priest.uid, False, (small.uid,)))
    assert small.fate == BANISHED and big.fate == IN_PLAY


def test_ironfist_priest_super_evolve_banishes_all_small_enemies():
    state = start()
    a, b, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.GIANT)
    priest = put(state, 0, H.IRONFIST_PRIEST)
    unlock_evolution(state, 0)
    apply(state, Evolve(priest.uid, True, (a.uid,)))
    assert a.fate == b.fate == BANISHED and big.fate == IN_PLAY


def test_sacred_griffon_gains_storm_when_you_engage():
    state = start()
    griffon = put(state, 0, H.SACRED_GRIFFON, ready=False)
    statue = put(state, 0, H.WINGED_STATUE)
    set_pp(state, 0, 1)
    assert Attack(griffon.uid, ENEMY_LEADER) not in legal_actions(state)
    apply(state, Engage(statue.uid))
    assert griffon.has(Keyword.STORM)
    assert Attack(griffon.uid, ENEMY_LEADER) in legal_actions(state)


def test_winged_statue_ticks_and_summons_holy_falcon():
    state = start()
    p = state.players[0]
    statue = put(state, 0, H.WINGED_STATUE)
    end_turns(state, 2)
    assert statue.countdown == 3
    set_pp(state, 0, 1)
    statue.countdown = 1
    apply(state, Engage(statue.uid))
    assert statue.fate == DESTROYED and ids(p.field) == [H.HOLY_FALCON.card_id]


# --- set 10004 -------------------------------------------------------------------------------

def test_troue_gains_drain_when_you_engage():
    state = start()
    troue = put(state, 0, H.TROUE)
    statue = put(state, 0, H.WINGED_STATUE)
    set_pp(state, 0, 1)
    apply(state, Engage(statue.uid))
    assert troue.has(Keyword.DRAIN)
    hurt(state, 0, 10)
    apply(state, Attack(troue.uid, ENEMY_LEADER))
    assert state.players[0].leader_hp == 12


def test_lamretta_evolve_cant_attack_and_end_of_turn_damage():
    state = start(first=0)
    lam = put(state, 0, H.LAMRETTA)
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(lam.uid))
    assert not any(isinstance(a, Attack) and a.attacker == lam.uid for a in legal_actions(state))
    end_turns(state)
    assert lam.life == 4 and mine.life == 3 and theirs.life == 3   # 3/6 -> 4; giants 5 -> 3
    end_turns(state)
    assert any(isinstance(a, Attack) and a.attacker == lam.uid for a in legal_actions(state))


def test_lamretta_unevolved_does_nothing_at_end_of_turn():
    state = start(first=0)
    put(state, 0, H.LAMRETTA)
    giant = put(state, 1, demo.GIANT)
    end_turns(state)
    assert giant.life == 5


def test_lamretta_evolved_by_galleon_at_end_of_turn_deals_no_damage():
    """Official Q&A: Galleon evolving Lamretta at the end of the turn doesn't make
    Lamretta's end-of-turn ability activate."""
    state = start(first=0)
    galleon = put(state, 0, H.GALLEON)
    galleon.evolved = True                                 # so Galleon picks Lamretta
    lam = put(state, 0, H.LAMRETTA)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    end_turns(state)
    assert lam.evolved and enemy.life == 5 and galleon.life == 5
    end_turns(state)                                       # next own turn: now it fires
    end_turns(state)
    assert enemy.life == 3


def test_awed_and_inspired_transforms_an_ally_and_draws():
    state = start()
    p = state.players[0]
    awed = put(state, 0, H.AWED_AND_INSPIRED)
    ally = put(state, 0, demo.GIANT)
    set_pp(state, 0, 2)
    hand = len(p.hand)
    apply(state, Engage(awed.uid, (ally.uid,)))
    assert awed.fate == DESTROYED and ally.defn == H.AWED_AND_INSPIRED
    assert len(p.hand) == hand + 1 and p.pp == 0


def test_sara_enhance_and_evolve_destroys_a_damaged_enemy():
    state = start()
    set_pp(state, 0, 6)
    sara = give(state, 0, H.SARA)
    play(state, sara)
    assert (sara.atk, sara.life) == (4, 15)
    healthy, damaged = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    damaged.life -= 1
    unlock_evolution(state, 0)
    targets = {a.targets for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == sara.uid}
    assert targets == {(damaged.uid,)}
    apply(state, Evolve(sara.uid, False, (damaged.uid,)))
    assert damaged.fate == DESTROYED and healthy.fate == IN_PLAY


def test_sara_unenhanced():
    state = start()
    set_pp(state, 0, 5)
    sara = give(state, 0, H.SARA)
    play(state, sara)
    assert (sara.atk, sara.life) == (4, 5)


def test_sophia_summons_a_cheap_haven_follower_and_super_evolve_gives_barrier():
    state = start(deck=[demo.FOOTMAN] * 39 + [H.FOX_OF_PURITY])
    p = state.players[0]
    p.deck = [c for c in p.deck if c.defn != H.FOX_OF_PURITY] + \
        [state.new_instance(H.FOX_OF_PURITY, 0)]
    set_pp(state, 0, 4)
    sophia = give(state, 0, H.SOPHIA)
    play(state, sophia)
    assert ids(p.field) == [H.SOPHIA.card_id, H.FOX_OF_PURITY.card_id]   # not the Neutral Footman
    fox = p.field[1]
    unlock_evolution(state, 0)
    apply(state, Evolve(sophia.uid, True))
    assert fox.has(Keyword.BARRIER) and not sophia.has(Keyword.BARRIER)


def test_skyfaring_vessel_gets_cheaper_in_hand_and_evolves_an_ally():
    state = start()
    vessel_in_hand = give(state, 0, H.SKYFARING_VESSEL)
    statue = put(state, 0, H.WINGED_STATUE)
    set_pp(state, 0, 1)
    apply(state, Engage(statue.uid))
    assert vessel_in_hand.cost == 3
    vessel = put(state, 0, H.SKYFARING_VESSEL)
    giant = put(state, 1, demo.GIANT)
    ally = put(state, 0, demo.GIANT)
    apply(state, Engage(vessel.uid, (ally.uid,)))
    assert vessel.fate == DESTROYED and ally.evolved and (ally.atk, ally.life) == (7, 7)
    assert giant.life == 5                                 # Evolve abilities don't fire
    assert vessel_in_hand.cost == 2


def test_tikoh_heals_on_engage_and_evolve_deals_three():
    state = start()
    hurt(state)
    tikoh = put(state, 0, H.TIKOH)
    statue = put(state, 0, H.WINGED_STATUE)
    set_pp(state, 0, 1)
    apply(state, Engage(statue.uid))
    assert state.players[0].leader_hp == 11
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(tikoh.uid, False, (enemy.uid,)))
    assert enemy.life == 2


def test_gleaming_gems_modes():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    gems = put(state, 0, H.GLEAMING_GEMS)
    modes = {a.modes for a in legal_actions(state) if isinstance(a, Engage) and a.uid == gems.uid}
    assert modes == {(0,), (1,)}
    apply(state, Engage(gems.uid, (), (0,)))
    assert gems.fate == DESTROYED and enemy.fate == DESTROYED
    gems = put(state, 0, H.GLEAMING_GEMS)
    hand = len(p.hand)
    apply(state, Engage(gems.uid, (), (1,)))
    assert len(p.hand) == hand + 2


def test_galleon_cant_attack_and_evolves_a_follower_that_didnt_attack():
    state = start(first=0)
    galleon = put(state, 0, H.GALLEON)
    galleon.evolved = True
    attacker, idle = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    assert not any(isinstance(a, Attack) and a.attacker == galleon.uid for a in legal_actions(state))
    unlock_evolution(state, 0)
    apply(state, Attack(attacker.uid, ENEMY_LEADER))
    end_turns(state)
    assert idle.evolved and not attacker.evolved


def test_galleon_needs_super_evolution_unlocked():
    state = start(first=0)
    put(state, 0, H.GALLEON)
    footman = put(state, 0, demo.FOOTMAN)
    end_turns(state)
    assert not footman.evolved


def test_vira_banishes_two_and_super_skybound_art():
    state = start()
    a, b, c = (put(state, 1, demo.GIANT) for _ in range(3))
    set_pp(state, 0, 8)
    vira = give(state, 0, H.VIRA)
    play(state, vira, [a.uid, b.uid])
    assert a.fate == b.fate == BANISHED and c.fate == IN_PLAY and not vira.evolved
    E.damage(state, [vira], 7)
    assert vira.life == 5                                  # can't take more than 3 at a time
    state.players[0].turns_taken = 15
    set_pp(state, 0, 8)
    vira2 = give(state, 0, H.VIRA)
    play(state, vira2, [c.uid])
    assert vira2.super_evolved


# --- set 10005 ---------------------------------------------------------------------------------

def test_prescient_priestess_fanfare_and_evolve():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    priestess = give(state, 0, H.PRESCIENT_PRIESTESS)
    play(state, priestess, [enemy.uid])
    assert enemy.life == 3
    unlock_evolution(state, 0)
    apply(state, Evolve(priestess.uid, False, (enemy.uid,)))
    assert enemy.life == 1


def test_bouquet_believer_enhanced_draws_gains_bane_and_rush():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    believer = give(state, 0, H.BOUQUET_BELIEVER)
    hand = len(state.players[0].hand)
    play(state, believer)
    assert len(state.players[0].hand) == hand          # -1 played, +1 drawn
    assert believer.has(Keyword.BANE) and believer.has(Keyword.RUSH)
    assert Attack(believer.uid, enemy.uid) in legal_actions(state)


def test_bouquet_believer_unenhanced_and_opponents_turn_draws():
    state = start(first=0)
    set_pp(state, 0, 1)
    believer = give(state, 0, H.BOUQUET_BELIEVER)
    play(state, believer)
    assert not believer.has(Keyword.BANE) and not believer.has(Keyword.RUSH)
    end_turns(state)                                       # opponent draws, then we draw
    assert not believer.has(Keyword.RUSH)
    E.draw(state, 0)                                       # a draw on the opponent's turn
    resolve_queue(state)
    assert not believer.has(Keyword.RUSH)
    end_turns(state)                                       # our turn-start draw
    assert believer.has(Keyword.RUSH)


def test_malice_of_the_mistbloom():
    state = start()
    p = state.players[0]
    p.hand.clear()
    keep = give(state, 0, demo.GIANT)
    set_pp(state, 0, 3)
    deck = len(p.deck)
    play(state, give(state, 0, H.MALICE_OF_THE_MISTBLOOM))
    assert keep in p.deck and len(p.hand) == 3 and len(p.deck) == deck + 1 - 3


def test_immovable_paladin_summons_three_copies():
    state = start()
    put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 8)
    play(state, give(state, 0, H.IMMOVABLE_PALADIN))
    assert count(state.players[0].field, H.IMMOVABLE_PALADIN) == 4   # field is full at 5


def test_desperate_shrinemouse_pings_on_draws_during_your_turn():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    mouse = give(state, 0, H.DESPERATE_SHRINEMOUSE)
    play(state, mouse)
    assert enemy.life == 4
    unlock_evolution(state, 0)
    apply(state, Evolve(mouse.uid))
    assert enemy.life == 3
    end_turns(state)                                       # opponent's draw: no ping
    assert enemy.life == 3


def test_desperate_shrinemouse_full_hand_evolve_doesnt_ping():
    """Official Q&A: evolving it with 9 cards in hand doesn't activate the draw ability."""
    state = start()
    enemy = put(state, 1, demo.GIANT)
    mouse = put(state, 0, H.DESPERATE_SHRINEMOUSE)
    while len(state.players[0].hand) < 9:
        give(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(mouse.uid))
    assert enemy.life == 5


def test_protective_shell_draws_per_ward_follower():
    state = start()
    p = state.players[0]
    put(state, 0, demo.SHIELDBEARER)
    put(state, 0, demo.SHIELDBEARER)
    put(state, 0, demo.FOOTMAN)
    shell = put(state, 0, H.PROTECTIVE_SHELL)
    hand = len(p.hand)
    apply(state, Engage(shell.uid))
    assert shell.fate == DESTROYED and len(p.hand) == hand + 2


def test_saint_of_rehabilitation_summons_foxes_on_your_turns():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    set_pp(state, 0, 5)
    saint = give(state, 0, H.SAINT_OF_REHABILITATION)
    play(state, saint)
    assert p.leader_hp == 11 and count(p.field, H.FOX_OF_PURITY) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(saint.uid, True))                 # Evolve and Super-Evolve both heal
    assert p.leader_hp == 13 and count(p.field, H.FOX_OF_PURITY) == 3
    end_turns(state)
    E.heal_leader(state, 0, 1)                            # opponent's turn: no fox
    resolve_queue(state)
    assert count(p.field, H.FOX_OF_PURITY) == 3


def test_resolve_of_the_mistbloom_fanfare_and_engage():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    resolve = give(state, 0, H.RESOLVE_OF_THE_MISTBLOOM)
    play(state, resolve, [enemy.uid])
    assert enemy.fate == DESTROYED
    p.hand.clear()
    a, b, c = give(state, 0, demo.GIANT), give(state, 0, demo.GIANT), give(state, 0, demo.GIANT)
    apply(state, Engage(resolve.uid))
    assert resolve.fate == DESTROYED and len(p.hand) == 3
    assert sum(x in p.deck for x in (a, b, c)) == 2


def test_sofina_mode_one_evolves_itself_and_shrinks_others_at_end_of_turn():
    state = start(first=0)
    ally, enemy = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    sofina = give(state, 0, H.SOFINA)
    play(state, sofina, modes=(0,))
    assert sofina.evolved and (sofina.atk, sofina.life) == (4, 4)
    end_turns(state)
    assert (ally.atk, ally.life) == (4, 4) and (enemy.atk, enemy.life) == (4, 4)
    assert (sofina.atk, sofina.life) == (4, 4)


def test_sofina_mode_two_evolves_a_ward_ally():
    state = start(first=0)
    plain = put(state, 0, demo.FOOTMAN)
    warder = put(state, 0, demo.SHIELDBEARER)
    set_pp(state, 0, 4)
    sofina = give(state, 0, H.SOFINA)
    play(state, sofina, modes=(1,))
    assert warder.evolved and (warder.atk, warder.life) == (4, 6)
    assert not plain.evolved and not sofina.evolved
    end_turns(state)
    assert (plain.atk, plain.life) == (1, 2)               # Sofina isn't evolved


def test_kukishiro_gains_crest_and_cycles_hand():
    state = start()
    p = state.players[0]
    p.hand.clear()
    a, b = give(state, 0, demo.GIANT), give(state, 0, demo.GIANT)
    set_pp(state, 0, 7)
    kuki = give(state, 0, H.KUKISHIRO)
    play(state, kuki)
    assert ids(p.leader_area) == [H.KUKISHIRO_CREST.card_id]
    assert a in p.deck and b in p.deck and len(p.hand) == 2
    # Both draws were 1-cost Footmen during our turn: two allied Fox / Falcon tokens.
    tokens = [c for c in p.field if c.defn in (H.FOX_OF_PURITY, H.HOLY_FALCON)]
    assert len(tokens) == 2


def test_kukishiro_crest_even_costs_summon_for_the_opponent():
    state = start(deck=[demo.SHIELDBEARER] * 40)
    E.add_to_leader_area(state, 0, H.KUKISHIRO_CREST)
    E.draw(state, 0)                                       # a 2-cost card
    resolve_queue(state)
    assert len(state.players[1].field) == 1 and state.players[0].field == []
    assert state.players[1].field[0].defn in (H.FOX_OF_PURITY, H.HOLY_FALCON)


def test_kukishiro_crest_full_hand_evolve_doesnt_trigger():
    """Official Q&A: with 9 cards in hand, Shrinemouse's evolve draw doesn't trigger the crest."""
    state = start()
    E.add_to_leader_area(state, 0, H.KUKISHIRO_CREST)
    mouse = put(state, 0, H.DESPERATE_SHRINEMOUSE)
    while len(state.players[0].hand) < 9:
        give(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(mouse.uid))
    assert state.players[0].field == [mouse] and state.players[1].field == []


# --- set 10006 ---------------------------------------------------------------------------------

def test_prostrating_coward_heals_when_played():
    state = start()
    hurt(state)
    set_pp(state, 0, 5)
    play(state, give(state, 0, H.PROSTRATING_COWARD))
    assert state.players[0].leader_hp == 12


def test_prostrating_coward_crystallize_summons_a_coward_that_heals():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    set_pp(state, 0, 2)
    coward = give(state, 0, H.PROSTRATING_COWARD)
    play(state, coward)
    assert coward.defn == H.COWARD_CRYSTALLIZE and coward.countdown == 3 and p.leader_hp == 10
    coward.countdown = 1
    end_turns(state, 2)
    assert ids(p.field) == [H.PROSTRATING_COWARD.card_id] and p.leader_hp == 12
    assert p.field[0].has(Keyword.WARD | Keyword.BANE)


def test_prostrating_coward_heals_however_it_enters():
    state = start()
    hurt(state)
    E.summon(state, 0, H.PROSTRATING_COWARD)
    resolve_queue(state)
    assert state.players[0].leader_hp == 12


def test_unholy_water_last_words_and_engage():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    water = put(state, 0, H.UNHOLY_WATER)
    set_pp(state, 0, 3)
    apply(state, Engage(water.uid))
    assert water.countdown == 2
    water.countdown = 1
    hand = len(p.hand)
    end_turns(state, 2)
    assert water.fate == DESTROYED and enemy.fate == DESTROYED
    assert len(p.hand) == hand + 2                          # turn draw + Last Words


def deck_of(state, player, cards):
    """Replace a player's deck (the last card is on top)."""
    state.players[player].deck = [state.new_instance(d, player) for d in cards]


def test_advent_of_the_eld_tome_draws_amulets():
    state = start()
    p = state.players[0]
    p.hand.clear()
    deck_of(state, 0, [H.WINGED_STATUE, H.JURATIO, demo.FOOTMAN, H.UNHOLY_WATER] + [demo.FOOTMAN] * 5)
    set_pp(state, 0, 3)
    play(state, give(state, 0, H.ADVENT_OF_THE_ELD_TOME))
    assert len(p.hand) == 2 and all(c.defn.is_amulet for c in p.hand)
    assert len(p.deck) == 7


def test_venerating_dyer_and_almiraj_crystallize():
    state = start(first=0)
    p = state.players[0]
    set_pp(state, 0, 1)
    dyer = give(state, 0, H.VENERATING_DYER)
    play(state, dyer)
    assert dyer.defn == H.DYER_CRYSTALLIZE and dyer.countdown == 3
    set_pp(state, 0, 2)
    rabbit = give(state, 0, H.MIRACULOUS_ALMIRAJ)
    play(state, rabbit)
    assert rabbit.defn == H.ALMIRAJ_CRYSTALLIZE
    apply(state, Engage(rabbit.uid))
    assert rabbit.countdown == 2
    dyer.countdown = rabbit.countdown = 1
    end_turns(state, 2)
    assert sorted(ids(p.field)) == sorted([H.VENERATING_DYER.card_id, H.MIRACULOUS_ALMIRAJ.card_id])


def test_pegasus_rider_summons_falcons():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 6)
    rider = give(state, 0, H.PEGASUS_RIDER)
    play(state, rider)
    unlock_evolution(state, 0)
    apply(state, Evolve(rider.uid))
    assert count(p.field, H.HOLY_FALCON) == 2


def test_scripture_of_salvation_last_words():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    enemy = put(state, 1, demo.GIANT)
    scripture = put(state, 0, H.SCRIPTURE_OF_SALVATION)
    scripture.countdown = 1
    hand = len(p.hand)
    end_turns(state, 2)
    assert enemy.life == 3 and p.leader_hp == 12 and len(p.hand) == hand + 3


def test_worshipful_crusader_fanfare_evolve_and_crystallize():
    state = start(first=0)
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 6)
    crusader = give(state, 0, H.WORSHIPFUL_CRUSADER)
    play(state, crusader)
    assert count(p.field, H.WORSHIPFUL_CRUSADER) == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(crusader.uid, False, (enemy.uid,)))
    assert enemy.fate == DESTROYED
    set_pp(state, 0, 1)
    crystal = give(state, 0, H.WORSHIPFUL_CRUSADER)
    play(state, crystal)
    assert crystal.defn == H.CRUSADER_CRYSTALLIZE
    crystal.countdown = 1
    end_turns(state, 2)
    assert count(p.field, H.WORSHIPFUL_CRUSADER) == 3


def test_sublime_eld_tome_recovers_pp_for_an_allied_amulet():
    state = start()
    p = state.players[0]
    statue = put(state, 0, H.WINGED_STATUE)
    set_pp(state, 0, 4)
    tome = give(state, 0, H.SUBLIME_ELD_TOME)
    play(state, tome, [statue.uid])
    assert statue.fate == DESTROYED and p.pp == 2
    assert ids(p.field) == [H.SUBLIME_ELD_TOME.card_id, H.HOLY_FALCON.card_id]


def test_sublime_eld_tome_enemy_target_and_last_words_copy():
    state = start(first=0)
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    p.destroyed_amulets += [H.WINGED_STATUE, H.JURATIO, H.SCRIPTURE_OF_SALVATION]
    set_pp(state, 0, 4)
    tome = give(state, 0, H.SUBLIME_ELD_TOME)
    play(state, tome, [enemy.uid])
    assert enemy.fate == DESTROYED and p.pp == 0
    tome.countdown = 1
    end_turns(state, 2)
    # Eligible: Winged Statue (1) and Scripture of Salvation (2), not Juratio (6, no Last Words).
    assert len(p.field) == 1
    assert p.field[0].defn in (H.WINGED_STATUE, H.SCRIPTURE_OF_SALVATION)


def test_kandima_summons_two_differently_named_amulets_and_super_evolve():
    state = start()
    p = state.players[0]
    p.destroyed_amulets += [H.WINGED_STATUE] * 3 + [H.UNHOLY_WATER, H.AWED_AND_INSPIRED]
    set_pp(state, 0, 4)
    kandima = give(state, 0, H.KANDIMA)
    play(state, kandima)
    summoned = [c.defn for c in p.field if c is not kandima]
    assert sorted(d.card_id for d in summoned) == sorted([H.WINGED_STATUE.card_id,
                                                          H.UNHOLY_WATER.card_id])
    enemies = [put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)]
    unlock_evolution(state, 0)
    statue = next(c for c in p.field if c.defn == H.WINGED_STATUE)
    apply(state, Evolve(kandima.uid, True, (statue.uid,)))
    assert statue.fate == DESTROYED and enemies[0].life == 2 and enemies[1].fate == DESTROYED


def test_kandima_super_evolve_on_an_enemy_card_deals_no_damage():
    state = start()
    kandima = put(state, 0, H.KANDIMA)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(kandima.uid, True, (a.uid,)))
    assert a.fate == DESTROYED and b.life == 5


def test_lyanthoth_destroys_three_and_faith_counts_amulets():
    state = start(first=0, deck=[H.LYANTHOTH] + [demo.FOOTMAN] * 39)
    p = state.players[0]
    faith = E.leader_area_card(state, 0, H.LYANTHOTH_FAITH)
    assert faith is not None
    statue, water = put(state, 0, H.WINGED_STATUE), put(state, 0, H.UNHOLY_WATER)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 9)
    lyanthoth = give(state, 0, H.LYANTHOTH)
    play(state, lyanthoth, [statue.uid, water.uid, enemy.uid])
    assert statue.fate == water.fate == enemy.fate == DESTROYED
    assert faith.counters["value"] == 2
    faith.counters["value"] = 11
    end_turns(state)
    assert faith.counters["value"] == 1 and count(p.hand, H.DEPTHS_OF_THE_ELD_TOME) == 1
    end_turns(state, 2)
    assert count(p.hand, H.DEPTHS_OF_THE_ELD_TOME) == 1   # not enough faith


def test_depths_of_the_eld_tome():
    state = start()
    p = state.players[0]
    statue = put(state, 0, H.WINGED_STATUE)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    play(state, give(state, 0, H.DEPTHS_OF_THE_ELD_TOME), [statue.uid])
    assert statue.fate == DESTROYED and state.players[1].leader_hp == 18
    again = next(c for c in p.hand if c.defn == H.DEPTHS_OF_THE_ELD_TOME)
    play(state, again, [enemy.uid])
    assert enemy.fate == DESTROYED and state.players[1].leader_hp == 18
    assert count(p.hand, H.DEPTHS_OF_THE_ELD_TOME) == 0


# --- set 10007 ---------------------------------------------------------------------------------

def test_reverend_of_finance_needs_three_amulets_and_draws_on_last_words():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 8)
    first = give(state, 0, H.REVEREND_OF_FINANCE)
    play(state, first)
    assert count(p.field, H.REVEREND_OF_FINANCE) == 1
    E.banish(state, first)
    amulets_on_field(state)
    play(state, give(state, 0, H.REVEREND_OF_FINANCE))
    assert count(p.field, H.REVEREND_OF_FINANCE) == 2
    hand = len(p.hand)
    E.destroy(state, next(c for c in p.field if c.defn == H.REVEREND_OF_FINANCE))
    resolve_queue(state)
    assert len(p.hand) == hand + 1


def test_missionary_of_recruitment_draws_amulets_and_evolve_scales():
    state = start()
    p = state.players[0]
    p.hand.clear()
    deck_of(state, 0, [demo.FOOTMAN, H.WINGED_STATUE, H.WINGED_STATUE, demo.FOOTMAN])
    set_pp(state, 0, 6)
    missionary = give(state, 0, H.MISSIONARY_OF_RECRUITMENT)
    play(state, missionary)
    assert ids(p.hand) == [H.WINGED_STATUE.card_id] * 2
    give(state, 0, H.JURATIO)
    give(state, 0, demo.FOOTMAN)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(missionary.uid))
    assert enemy.life == 2                                 # 3 amulets in hand


def test_earrings_of_sunlight_fanfare_and_engage():
    state = start()
    p = state.players[0]
    p.hand.clear()
    giant = give(state, 0, demo.GIANT)
    set_pp(state, 0, 1)
    earrings = give(state, 0, H.EARRINGS_OF_SUNLIGHT)
    play(state, earrings, [giant.uid])
    assert giant in p.deck and len(p.hand) == 1
    other = p.hand[0]
    apply(state, Engage(earrings.uid, (other.uid,)))
    assert earrings.fate == DESTROYED and other in p.deck and len(p.hand) == 1


def test_sister_of_strategic_development():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    play(state, give(state, 0, H.SISTER_OF_STRATEGIC_DEVELOPMENT), [enemy.uid])
    assert enemy.life == 5
    amulets_on_field(state)
    play(state, give(state, 0, H.SISTER_OF_STRATEGIC_DEVELOPMENT), [enemy.uid])
    assert enemy.fate == DESTROYED


def test_holy_hawk_banishes_and_heals_with_three_amulets():
    state = start()
    hurt(state)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 8)
    hawk = give(state, 0, H.HOLY_HAWK_OF_COMMUNICATIONS)
    play(state, hawk, [a.uid])
    assert a.fate == BANISHED and state.players[0].leader_hp == 10
    assert Attack(hawk.uid, ENEMY_LEADER) in legal_actions(state)   # Storm
    amulets_on_field(state)
    set_pp(state, 0, 8)
    play(state, give(state, 0, H.HOLY_HAWK_OF_COMMUNICATIONS), [b.uid])
    assert b.fate == BANISHED and state.players[0].leader_hp == 13


def test_timepiece_of_perfection():
    state = start()
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    plain = give(state, 0, H.TIMEPIECE_OF_PERFECTION)
    play(state, plain)
    assert a.life == 2
    set_pp(state, 0, 4)
    enhanced = give(state, 0, H.TIMEPIECE_OF_PERFECTION)
    play(state, enhanced)
    assert a.life == 1 and b.life == 4 and state.players[0].pp == 0
    apply(state, Engage(plain.uid))
    assert plain.fate == DESTROYED and a.fate == DESTROYED and b.life == 3


def test_deacon_of_security():
    state = start()
    p = state.players[0]
    hurt(state)
    set_pp(state, 0, 6)
    plain = give(state, 0, H.DEACON_OF_SECURITY)
    play(state, plain)
    assert not plain.evolved and not plain.has(Keyword.BARRIER)
    amulets_on_field(state)
    set_pp(state, 0, 6)
    deacon = give(state, 0, H.DEACON_OF_SECURITY)
    play(state, deacon)
    assert deacon.evolved and deacon.has(Keyword.BARRIER) and deacon.has(Keyword.WARD)
    E.destroy(state, plain)
    resolve_queue(state)
    assert p.leader_hp == 13


def test_trident_of_eroding_tides():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    trident = give(state, 0, H.TRIDENT_OF_ERODING_TIDES)
    play(state, trident, [enemy.uid])
    assert enemy.life == 1
    other = put(state, 1, demo.GIANT)
    apply(state, Engage(trident.uid, (other.uid,)))
    assert trident.fate == DESTROYED and other.life == 3


def test_rodeo_summons_rings_and_evolve_delays_them():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 8)
    rodeo = give(state, 0, H.RODEO)
    play(state, rodeo)
    rings = next(c for c in p.field if c.defn == H.RINGS_OF_MOONLIGHT)
    assert rings.countdown == 1 and rings.has(Keyword.AURA)
    unlock_evolution(state, 0)
    apply(state, Evolve(rodeo.uid))
    assert rings.countdown == 2


def test_rings_of_moonlight_needs_three_amulets():
    state = start(first=0)
    rings = put(state, 0, H.RINGS_OF_MOONLIGHT)
    enemy = put(state, 1, demo.GIANT)
    end_turns(state)
    assert enemy.life == 5 and state.players[1].leader_hp == 20
    end_turns(state)
    assert rings.fate == DESTROYED                          # Countdown (1)
    rings = put(state, 0, H.RINGS_OF_MOONLIGHT)
    amulets_on_field(state, n=2)
    end_turns(state)
    assert enemy.life == 2 and state.players[1].leader_hp == 17


def test_initia_banishes_and_super_evolve_replicates():
    state = start()
    hurt(state)
    amulets_on_field(state)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    initia = give(state, 0, H.INITIA)
    play(state, initia, [a.uid])
    assert a.fate == BANISHED and state.players[0].leader_hp == 13
    unlock_evolution(state, 0)
    apply(state, Evolve(initia.uid, True, (b.uid,)))
    assert b.fate == BANISHED and state.players[0].leader_hp == 16


def test_initia_normal_evolve_does_nothing():
    state = start()
    initia = put(state, 0, H.INITIA)
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(initia.uid, False, (enemy.uid,)))
    assert enemy.fate == IN_PLAY


# --- set 10008 ---------------------------------------------------------------------------------

def test_lilium_last_words_draws():
    state = start()
    lilium = put(state, 0, H.LILIUM)
    hand = len(state.players[0].hand)
    E.destroy(state, lilium)
    resolve_queue(state)
    assert len(state.players[0].hand) == hand + 1


def test_lilium_evolve_removes_all_abilities_and_deals_two():
    state = start()
    bomber = put(state, 1, demo.BOMBER)
    E.buff(state, bomber, 0, 3)
    E.give_keywords(bomber, Keyword.WARD | Keyword.BARRIER)
    lilium = put(state, 0, H.LILIUM)
    unlock_evolution(state, 0)
    apply(state, Evolve(lilium.uid, False, (bomber.uid,)))
    assert bomber.keywords == Keyword.NONE and bomber.life == 3     # barrier gone first
    assert bomber.defn.name == demo.BOMBER.name
    E.destroy(state, bomber)
    resolve_queue(state)
    assert state.players[0].leader_hp == 20               # no Last Words


def test_lilium_silence_removes_damage_cap_and_granted_abilities():
    state = start()
    vira = put(state, 1, H.VIRA)
    E.grant(vira, ThreeAttacks())
    lilium = put(state, 0, H.LILIUM)
    unlock_evolution(state, 0)
    apply(state, Evolve(lilium.uid, False, (vira.uid,)))
    assert vira.max_attacks == 1 and not vira.grants
    E.damage(state, [vira], 5)
    assert vira.life == 1                                  # 8 - 2 - 5


def test_theresa_summons_a_stormy_soulcure_sister_without_healing():
    state = start()
    hurt(state)
    set_pp(state, 0, 7)
    play(state, give(state, 0, H.THERESA))
    sister = state.players[0].field[1]
    assert sister.defn == H.SOULCURE_SISTER and (sister.atk, sister.life) == (5, 3)
    assert sister.has(Keyword.STORM) and state.players[0].leader_hp == 10
    assert Attack(sister.uid, ENEMY_LEADER) in legal_actions(state)


def test_grant_destroys_on_fanfare_and_evolve():
    state = start()
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    grant = give(state, 0, H.GRANT)
    play(state, grant, [a.uid])
    unlock_evolution(state, 0)
    apply(state, Evolve(grant.uid, False, (b.uid,)))
    assert a.fate == b.fate == DESTROYED


def test_edeth_last_words_summons_one_without_last_words():
    state = start()
    p = state.players[0]
    edeth = put(state, 0, H.EDETH)
    E.destroy(state, edeth)
    resolve_queue(state)
    twin = p.field[0]
    assert twin.defn == H.EDETH and twin.has(Keyword.WARD | Keyword.AURA)
    E.destroy(state, twin)
    resolve_queue(state)
    assert p.field == []


def test_edeth_super_evolve_destroys_and_evolve_does_not():
    state = start()
    a = put(state, 1, demo.GIANT)
    e1, e2 = put(state, 0, H.EDETH), put(state, 0, H.EDETH)
    unlock_evolution(state, 0)
    apply(state, Evolve(e1.uid, False, (a.uid,)))
    assert a.fate == IN_PLAY
    state.players[0].evolved_this_turn = False
    apply(state, Evolve(e2.uid, True, (a.uid,)))
    assert a.fate == DESTROYED


def test_viche_gets_cheaper_when_an_ally_super_evolves():
    state = start()
    viche = give(state, 0, H.VICHE)
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(a.uid))
    assert viche.cost == 6
    state.players[0].evolved_this_turn = False
    apply(state, Evolve(b.uid, True))
    assert viche.cost == 3
    E.evolve(state, put(state, 0, demo.FOOTMAN), super_=True)   # effect super-evolution too
    resolve_queue(state)
    assert viche.cost == 0


def test_lingering_threat_single_and_enhanced():
    state = start()
    small, ward, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    threat = give(state, 0, H.LINGERING_THREAT)
    assert {a.targets for a in plays(state, threat.uid)} == {(small.uid,), (ward.uid,)}
    play(state, threat, [small.uid])
    assert small.fate == BANISHED and ward.fate == IN_PLAY
    small2 = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 5)
    play(state, give(state, 0, H.LINGERING_THREAT), [ward.uid])
    assert ward.fate == small2.fate == BANISHED and big.fate == IN_PLAY


def test_colette_evolves_itself_next_to_an_evolved_ally():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    ally = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 6)
    plain = give(state, 0, H.COLETTE)
    play(state, plain)
    assert not plain.evolved and enemy.life == 5
    E.evolve(state, ally)
    resolve_queue(state)
    colette = give(state, 0, H.COLETTE)
    play(state, colette)
    assert colette.evolved and enemy.life == 3


def test_colette_point_evolution_pings_twice():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    colette = put(state, 0, H.COLETTE)
    unlock_evolution(state, 0)
    apply(state, Evolve(colette.uid))
    assert enemy.life == 3


def test_academy_hijinks_draws_and_heals_by_evolution():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    hijinks = put(state, 0, H.ACADEMY_HIJINKS)
    hand = len(p.hand)
    end_turns(state)
    assert len(p.hand) == hand + 1 and p.leader_hp == 10
    end_turns(state)
    f = put(state, 0, demo.FOOTMAN)
    E.evolve(state, f)
    resolve_queue(state)
    end_turns(state)
    assert p.leader_hp == 11
    end_turns(state)
    assert hijinks.fate == DESTROYED                          # Countdown (2)
    hijinks = put(state, 0, H.ACADEMY_HIJINKS)
    E.evolve(state, put(state, 0, demo.FOOTMAN), super_=True)
    resolve_queue(state)
    end_turns(state)
    assert p.leader_hp == 13


def test_verdilia_summons_and_super_evolves_a_cheap_follower():
    state = start(deck=[demo.GIANT] * 39 + [demo.FOOTMAN])
    p = state.players[0]
    p.deck = [c for c in p.deck if c.defn != demo.FOOTMAN] + [state.new_instance(demo.FOOTMAN, 0)]
    set_pp(state, 0, 7)
    verdilia = give(state, 0, H.VERDILIA_AND_CASTELLE)
    play(state, verdilia)
    footman = p.field[1]
    assert footman.defn == demo.FOOTMAN and footman.super_evolved and (footman.atk, footman.life) == (4, 5)
    unlock_evolution(state, 0)
    apply(state, Evolve(verdilia.uid, True))
    assert ids(p.leader_area) == [H.VERDILIA_CREST.card_id]


def test_verdilia_crest_lets_super_evolved_followers_attack_twice():
    state = start(first=0)
    E.add_to_leader_area(state, 0, H.VERDILIA_CREST)
    hero, normal = put(state, 0, demo.GIANT), put(state, 0, demo.GIANT)
    E.evolve(state, hero, super_=True)
    E.evolve(state, normal)
    resolve_queue(state)
    a, b, c = put(state, 1, demo.FOOTMAN), put(state, 1, demo.FOOTMAN), put(state, 1, demo.FOOTMAN)
    apply(state, Attack(hero.uid, a.uid))
    apply(state, Attack(hero.uid, b.uid))                  # second attack this turn
    assert not any(isinstance(x, Attack) and x.attacker == hero.uid for x in legal_actions(state))
    apply(state, Attack(normal.uid, c.uid))
    assert not any(isinstance(x, Attack) and x.attacker == normal.uid for x in legal_actions(state))
    end_turns(state, 2)
    assert hero.max_attacks == 1
    apply(state, Attack(hero.uid, ENEMY_LEADER))           # attacking a leader: no bonus
    assert not any(isinstance(x, Attack) and x.attacker == hero.uid for x in legal_actions(state))


def test_verdilia_crest_doesnt_lower_three_attacks():
    """Official Q&A: a super-evolved follower that can attack 3 times still can."""
    state = start(first=0)
    E.add_to_leader_area(state, 0, H.VERDILIA_CREST)
    armes = put(state, 0, demo.GIANT)
    E.evolve(state, armes, super_=True)
    E.grant(armes, ThreeAttacks())
    resolve_queue(state)
    enemies = [put(state, 1, demo.FOOTMAN) for _ in range(3)]
    for enemy in enemies:
        apply(state, Attack(armes.uid, enemy.uid))
    assert all(e.fate == DESTROYED for e in enemies) and armes.attacks_made == 3


def test_zoe_modes_self_damage_and_crest():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    zoe = give(state, 0, H.ZOE)
    assert {a.modes for a in plays(state, zoe.uid)} == {(0,), (1,), (2,)}
    play(state, zoe, modes=(0,))
    assert enemy.life == 2 and zoe.life == 1
    set_pp(state, 0, 5)
    play(state, give(state, 0, H.ZOE), modes=(1,))
    assert state.players[1].leader_hp == 17
    set_pp(state, 0, 5)
    play(state, give(state, 0, H.ZOE), modes=(2,))
    assert p.leader_hp == 13
    unlock_evolution(state, 0)
    apply(state, Evolve(zoe.uid))
    crest = E.leader_area_card(state, 0, H.ZOE_CREST)
    assert crest.countdown == 1
    for c in list(p.field):
        E.banish(state, c)
    end_turns(state, 2)
    assert crest.fate == DESTROYED
    assert ids(p.field) == [H.ZOE.card_id] and p.field[0].evolved and p.field[0].life == 6


# --- set 10009 ---------------------------------------------------------------------------------

def test_follower_of_the_tenets_evolves_when_healed_on_your_turn():
    state = start(first=0)
    hurt(state)
    tenets = put(state, 0, H.FOLLOWER_OF_THE_TENETS)
    end_turns(state)
    E.heal_leader(state, 0, 2)                            # opponent's turn
    resolve_queue(state)
    assert not tenets.evolved
    end_turns(state)
    E.heal_leader(state, 0, 2)
    resolve_queue(state)
    assert tenets.evolved and (tenets.atk, tenets.life) == (4, 4)


def test_peryton_summons_two_copies():
    state = start()
    set_pp(state, 0, 6)
    peryton = give(state, 0, H.PERYTON)
    play(state, peryton)
    assert count(state.players[0].field, H.PERYTON) == 3


def test_roaring_basilica_engage_bursts_it():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    basilica = give(state, 0, H.ROARING_BASILICA)
    play(state, basilica)
    apply(state, Engage(basilica.uid))
    assert basilica.fate == DESTROYED and p.pp == 0
    assert ids(p.field) == [H.HOLYFLAME_TIGER.card_id] and enemy.life == 1


def test_agent_of_the_testaments_ambush_and_heal():
    state = start(first=0)
    hurt(state)
    set_pp(state, 0, 3)
    agent = give(state, 0, H.AGENT_OF_THE_TESTAMENTS)
    play(state, agent)
    assert agent.has(Keyword.AMBUSH)
    end_turns(state)
    assert state.players[0].leader_hp == 11 and agent.has(Keyword.AMBUSH)
    end_turns(state)
    assert not agent.has(Keyword.AMBUSH)


def test_vow_of_devotion_one_mode_or_both():
    state = start()
    hurt(state)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 1)
    vow = give(state, 0, H.VOW_OF_DEVOTION)
    assert {a.modes for a in plays(state, vow.uid)} == {(0,), (1,)}
    play(state, vow, modes=(1,))
    assert state.players[0].leader_hp == 12 and enemy.life == 5
    put(state, 0, H.SOULCURE_SISTER)                      # base cost 6
    set_pp(state, 0, 1)
    vow = give(state, 0, H.VOW_OF_DEVOTION)
    assert [a.modes for a in plays(state, vow.uid)] == [(0, 1)]
    play(state, vow, modes=(0, 1))
    assert state.players[0].leader_hp == 14 and enemy.life == 2


def test_executor_of_the_vow_destroys_on_heals_during_your_turn():
    state = start(first=0)
    hurt(state)
    a, b, c = (put(state, 1, demo.GIANT) for _ in range(3))
    set_pp(state, 0, 7)
    executor = give(state, 0, H.EXECUTOR_OF_THE_VOW)
    play(state, executor)                                 # its own Fanfare heal triggers it
    assert sum(x.fate == DESTROYED for x in (a, b, c)) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(executor.uid, True))
    assert sum(x.fate == DESTROYED for x in (a, b, c)) == 2
    end_turns(state)
    E.heal_leader(state, 0, 1)
    resolve_queue(state)
    assert sum(x.fate == DESTROYED for x in (a, b, c)) == 2


def test_juratio_destroys_all_followers_and_engage():
    state = start()
    p = state.players[0]
    hurt(state)
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    juratio = give(state, 0, H.JURATIO)
    play(state, juratio)
    assert mine.fate == theirs.fate == DESTROYED and juratio.fate == IN_PLAY
    hand = len(p.hand)
    apply(state, Engage(juratio.uid))
    assert juratio.fate == DESTROYED and len(p.hand) == hand + 1 and p.leader_hp == 11 and p.pp == 0


def test_erralde_fanfare_evolve_and_crest():
    state = start(first=0)
    p = state.players[0]
    hurt(state)
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 6)
    erralde = give(state, 0, H.ERRALDE)
    play(state, erralde, [enemy.uid])
    assert enemy.fate == DESTROYED
    unlock_evolution(state, 0)
    apply(state, Evolve(erralde.uid))
    assert ids(p.leader_area) == [H.ERRALDE_CREST.card_id]
    end_turns(state)
    assert state.players[1].leader_hp == 19 and p.leader_hp == 11
    end_turns(state)
    E.banish(state, erralde)
    end_turns(state)                                       # no 6-cost card: nothing
    assert state.players[1].leader_hp == 19 and p.leader_hp == 11


def test_omerio_cycles_its_abilities():
    """Official Q&A: after the third ability, the next amulet destroyed activates the first."""
    state = start()
    p = state.players[0]
    hurt(state)
    omerio = put(state, 0, H.OMERIO)
    enemies = [put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)]
    statues = [put(state, 0, H.AWED_AND_INSPIRED) for _ in range(4)]   # no Last Words
    for s in statues[:3]:
        E.destroy(state, s)
        resolve_queue(state)
    assert all(e.life == 2 for e in enemies) and p.leader_hp == 12
    assert count(p.field, H.HOLY_FALCON) == 1
    E.destroy(state, statues[3])
    resolve_queue(state)
    assert all(e.fate == DESTROYED for e in enemies)
    E.destroy(state, put(state, 1, demo.TOTEM))             # enemy amulets don't count
    resolve_queue(state)
    assert omerio.counters["step"] == 1


def test_omerio_evolve_destroys_all_allied_amulets():
    state = start()
    p = state.players[0]
    hurt(state)
    omerio = put(state, 0, H.OMERIO)
    a, b = put(state, 0, demo.TOTEM), put(state, 0, demo.TOTEM)
    enemy_totem = put(state, 1, demo.TOTEM)
    unlock_evolution(state, 0)
    apply(state, Evolve(omerio.uid))
    assert a.fate == b.fate == DESTROYED and enemy_totem.fate == IN_PLAY
    assert p.leader_hp == 12 and omerio.counters["step"] == 2


# --- coverage and fuzzing ------------------------------------------------------------------

def test_every_haven_card_is_scripted_or_keyword_only():
    from svsim.cards.pool import POOL, ROTATION_IDS
    haven = [POOL[i] for i in ROTATION_IDS if POOL[i].craft == Craft.HAVEN]
    unscripted = [c for c in haven if not has_script(c.card_id)]
    assert sorted(c.card_id for c in unscripted) == sorted(c.card_id for c in H.NO_SCRIPT)
    assert len(haven) == len(H.CARDS) + len(H.TOKENS) + len(H.LEADER_AREA) + len(H.ALTERNATE_FORMS)


def _random_deck(rng):
    no_script = {c.card_id for c in H.NO_SCRIPT}
    pool = [c for c in collectible(Craft.HAVEN) if has_script(c.card_id) or c.card_id in no_script]
    deck = []
    while len(deck) < 40:
        c = rng.choice(pool)
        if deck.count(c) < 3:
            deck.append(c)
    return deck


def test_random_haven_games():
    for g in range(100):
        rng = random.Random(g)
        deck0, deck1 = _random_deck(rng), _random_deck(rng)
        state = new_game(deck0, deck1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
        assert state.over
