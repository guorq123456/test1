"""Dragoncraft cards beyond the Ramp Dragon starter deck (sets 10004-10009, Basic)."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, demo, dragon
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import DRAW, Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import BANISHED, DESTROYED, FIELD_LIMIT, HAND_LIMIT, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution


def attacks_by(state, uid):
    return [a for a in legal_actions(state) if isinstance(a, Attack) and a.attacker == uid]


def evolves_of(state, uid):
    return [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == uid]


def play(state, defn, targets=(), modes=(), pp=10, player=0):
    """Give `defn` to a player, set their play points, and play it."""
    card = give(state, player, defn)
    set_pp(state, player, pp)
    apply(state, PlayCard(card.uid, tuple(targets), tuple(modes)))
    return card


def in_hand(state, player, card):
    return any(c is card for c in state.players[player].hand)


# --- crests and tokens ---------------------------------------------------------------

def test_every_dragon_card_has_a_script_or_needs_none():
    for defn in dragon.CARDS + dragon.TOKENS + dragon.LEADER_AREA + dragon.ALTERNATE_FORMS:
        assert has_script(defn.card_id) or defn in dragon.KEYWORD_ONLY, defn.name
    for defn in dragon.KEYWORD_ONLY:
        assert not has_script(defn.card_id)


# --- set 10009 -----------------------------------------------------------------------

def test_ripper_clawed_thief_storm_and_last_words():
    state = start(first=0)
    p = state.players[0]
    thief = play(state, dragon.RIPPER_CLAWED_THIEF, pp=1)
    assert not thief.has(Keyword.STORM)
    p.attacked_leader_last_turn = True
    storm = play(state, dragon.RIPPER_CLAWED_THIEF, pp=1)
    assert storm.has(Keyword.STORM) and Attack(storm.uid, leader_uid(1)) in legal_actions(state)
    p.hand.clear()
    E.destroy(state, thief)
    resolve_queue(state)
    copy = p.hand[-1]
    assert copy.defn == dragon.RIPPER_CLAWED_THIEF and copy.counters[dragon.NO_LAST_WORDS]
    set_pp(state, 0, 1)
    apply(state, PlayCard(copy.uid))
    E.destroy(state, copy)                     # the copy has no Last Words
    resolve_queue(state)
    assert p.hand == []


def test_cave_dragon_evolves_in_overflow():
    state = start()
    small = play(state, dragon.CAVE_DRAGON, pp=6)
    big = play(state, dragon.CAVE_DRAGON, pp=7)
    assert not small.evolved and (small.atk, small.life) == (5, 3)
    assert big.evolved and (big.atk, big.life) == (7, 5) and big.has(Keyword.AMBUSH)


def test_drake_whelps_tantrum_enhance():
    state = start()
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.DRAKE_WHELPS_TANTRUM, pp=1)
    assert count(state.players[0].field, dragon.FIRE_DRAKE_WHELP) == 1 and giant.life == 5
    play(state, dragon.DRAKE_WHELPS_TANTRUM, pp=3)
    assert count(state.players[0].field, dragon.FIRE_DRAKE_WHELP) == 2 and giant.life == 2
    assert state.players[0].pp == 0


def test_high_spirited_marauder_strike():
    for attacked, damage in ((False, 1), (True, 2)):
        state = start(first=0)
        state.players[0].attacked_leader_last_turn = attacked
        marauder = put(state, 0, dragon.HIGH_SPIRITED_MARAUDER)
        apply(state, Attack(marauder.uid, leader_uid(1)))
        assert state.players[1].leader_hp == 20 - damage
        apply(state, EndTurn())
        assert marauder.atk == 1                  # until the end of the turn


def test_dragonfolk_butler():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    butler = play(state, dragon.DRAGONFOLK_BUTLER, pp=10)
    assert p.leader_hp == 13 and p.pp == 5        # paid 8, recovered 3
    ally = put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    assert {a.targets for a in evolves_of(state, butler.uid)} == {(ally.uid,)}   # another follower
    apply(state, Evolve(butler.uid, targets=(ally.uid,)))
    assert (ally.atk, ally.life) == (4, 5)


def test_parting_jaws_needs_two_cards():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 3)
    jaws = give(state, 0, dragon.PARTING_JAWS)
    vorlalai = give(state, 0, dragon.VORLALAI)
    assert plays(state, jaws.uid) == []
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    giant = put(state, 1, demo.GIANT)
    apply(state, PlayCard(jaws.uid, (vorlalai.uid, depths.uid)))
    # 3 to the Giant and the leader, then the discarded Depths deals 1 more
    assert giant.life == 2 and state.players[1].leader_hp == 16
    assert count(p.field, dragon.VORLALAI) == 1


def test_barren_earth_tyrant_after_attacking_the_leader():
    state = start(first=0)
    raider = put(state, 0, demo.RAIDER)
    apply(state, Attack(raider.uid, leader_uid(1)))
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert state.players[0].attacked_leader_last_turn
    victims = [put(state, 1, demo.FOOTMAN) for _ in range(3)]
    tyrant = play(state, dragon.BARREN_EARTH_TYRANT, pp=5)
    assert sum(v.fate == DESTROYED for v in victims) == 2      # twice
    unlock_evolution(state, 0)
    apply(state, Evolve(tyrant.uid))
    assert count(state.players[0].field, dragon.HIGH_SPIRITED_MARAUDER) == 1


def test_barren_earth_tyrant_once_without_a_leader_attack():
    state = start(first=0)
    victims = [put(state, 1, demo.FOOTMAN) for _ in range(3)]
    play(state, dragon.BARREN_EARTH_TYRANT, pp=5)
    assert sum(v.fate == DESTROYED for v in victims) == 1


def test_artiglio_splits_damage():
    for attacked, giant_life in ((False, 4), (True, 1)):
        state = start()
        state.players[0].attacked_leader_last_turn = attacked
        footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
        play(state, dragon.ARTIGLIO, pp=2)
        assert footman.fate == DESTROYED and giant.life == giant_life


def test_antemaria_storm_when_a_leader_was_attacked():
    state = start()
    rush = play(state, dragon.ANTEMARIA, pp=7)
    assert not rush.has(Keyword.STORM) and Attack(rush.uid, leader_uid(1)) not in legal_actions(state)
    state.players[0].attacked_leader_last_turn = True
    storm = play(state, dragon.ANTEMARIA, pp=7)
    assert Attack(storm.uid, leader_uid(1)) in legal_actions(state)


# --- set 10008 -----------------------------------------------------------------------

def test_gido_evolves_at_low_defense():
    state = start()
    p = state.players[0]
    p.leader_hp = 11
    healthy = play(state, dragon.GIDO, pp=4)
    p.leader_hp = 10
    hurt = play(state, dragon.GIDO, pp=4)
    assert not healthy.evolved and hurt.evolved and (hurt.atk, hurt.life) == (3, 9)


def test_sandstorm_watchdragon_last_words():
    state = start()
    p = state.players[0]
    dragon_ = put(state, 0, dragon.SANDSTORM_WATCHDRAGON)
    hand = len(p.hand)
    E.destroy(state, dragon_)
    resolve_queue(state)
    assert len(p.hand) == hand + 3


def test_spirit_of_wadatsumi_and_its_crest():
    state = start()
    p = state.players[0]
    p.hand.clear()
    spirit = play(state, dragon.SPIRIT_OF_WADATSUMI, pp=2)
    assert count(p.hand, dragon.MAJESTIC_MEGALORCA) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(spirit.uid))
    assert E.leader_area_card(state, 0, dragon.SPIRIT_OF_WADATSUMI_CREST) is not None
    megalorca = p.hand[0]
    set_pp(state, 0, 2)
    apply(state, PlayCard(megalorca.uid))
    assert (megalorca.atk, megalorca.life) == (3, 3)            # Marine: +1/+1
    footman = play(state, demo.FOOTMAN, pp=1)
    assert (footman.atk, footman.life) == (1, 2)


def test_reef_and_lolo():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    play(state, dragon.REEF_AND_LOLO, pp=5)
    assert count(p.field, dragon.REEF_AND_LOLO) == 2
    apply(state, EndTurn())                       # both copies add a Megalorca
    assert count(p.hand, dragon.MAJESTIC_MEGALORCA) == 2


def test_art_of_decay():
    state = start()
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.ART_OF_DECAY, pp=6)
    assert giant.life == 1 and state.players[1].leader_hp == 16


def test_giada_barrier_and_second_attack():
    state = start(first=0)
    giada = put(state, 0, dragon.GIADA)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    apply(state, Attack(giada.uid, a.uid))
    assert a.fate == DESTROYED and giada.life == 2          # Barrier took the hit
    assert Attack(giada.uid, b.uid) in legal_actions(state)
    apply(state, Attack(giada.uid, b.uid))
    assert b.fate == DESTROYED and giada.life == 2 and attacks_by(state, giada.uid) == []
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert giada.max_attacks == 1
    apply(state, Attack(giada.uid, leader_uid(1)))          # attacking a leader: no extra attack
    assert giada.has(Keyword.BARRIER) and attacks_by(state, giada.uid) == []


def test_ephemeral_foxfire():
    state = start()
    p = state.players[0]
    deck, hand = len(p.deck), len(p.hand)
    play(state, dragon.EPHEMERAL_FOXFIRE, targets=(leader_uid(1),), pp=1)
    assert state.players[1].leader_hp == 19
    assert len(p.deck) == deck + 1 and count(p.deck, dragon.EPHEMERAL_FOXFIRE) == 1
    assert len(p.hand) == hand
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.EPHEMERAL_FOXFIRE, targets=(giant.uid,), pp=7)
    assert giant.life == 4 and len(p.hand) == hand + 1     # Overflow: drew a card


def test_drache_and_aluzard_counts_other_copies():
    state = start()
    p = state.players[0]
    first = play(state, dragon.DRACHE_AND_ALUZARD, pp=4)
    second = play(state, dragon.DRACHE_AND_ALUZARD, pp=4)
    assert (first.atk, first.life) == (4, 4) and (second.atk, second.life, second.evolved) == (5, 5, False)
    E.destroy(state, first)
    resolve_queue(state)
    assert E.leader_area_card(state, 0, dragon.DRACHE_AND_ALUZARD_CREST) is not None
    third = play(state, dragon.DRACHE_AND_ALUZARD, pp=4)
    # X = 2 (one destroyed, one on the field): +2/+2, then evolved
    assert third.evolved and (third.atk, third.life) == (8, 8)
    assert count(p.leader_area, dragon.DRACHE_AND_ALUZARD_CREST) == 1


def test_drache_and_aluzard_crest_returns_a_cheap_copy():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    E.add_to_leader_area(state, 0, dragon.DRACHE_AND_ALUZARD_CREST)
    for _ in range(2):
        apply(state, EndTurn())
        apply(state, EndTurn())
    assert E.leader_area_card(state, 0, dragon.DRACHE_AND_ALUZARD_CREST) is None
    returned = [c for c in p.hand if c.defn == dragon.DRACHE_AND_ALUZARD]
    assert len(returned) == 1 and returned[0].cost == 2


# --- set 10007 -----------------------------------------------------------------------

def test_carrier_wyvern():
    state = start()
    p = state.players[0]
    p.hand.clear()
    ally = put(state, 0, demo.FOOTMAN)
    wyvern = play(state, dragon.CARRIER_WYVERN, targets=(ally.uid,), pp=4)
    assert (ally.atk, ally.life) == (3, 4)
    give(state, 0, dragon.DRAGONSIGN)
    follower, twin = give(state, 0, demo.FOOTMAN), give(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    assert {a.targets for a in evolves_of(state, wyvern.uid)} == {(follower.uid,)}   # followers only
    apply(state, Evolve(wyvern.uid, targets=(follower.uid,)))
    assert (follower.atk, follower.life) == (3, 4) and (twin.atk, twin.life) == (1, 2)
    set_pp(state, 0, 1)
    assert len(plays(state, follower.uid)) == 1 and len(plays(state, twin.uid)) == 1   # told apart
    apply(state, PlayCard(follower.uid))
    assert follower in p.field and (follower.atk, follower.life) == (3, 4)


def test_apathetic_gaze_turns_its_copies_into_lazing_flame():
    state = start()
    p = state.players[0]
    p.hand.clear()
    other = give(state, 0, dragon.APATHETIC_GAZE)
    p.deck.append(state.new_instance(dragon.APATHETIC_GAZE, 0))
    play(state, dragon.APATHETIC_GAZE, pp=4)
    assert p.max_pp == 5
    assert other.defn == dragon.LAZING_FLAME and other.cost == 3
    assert count(p.hand + p.deck, dragon.APATHETIC_GAZE) == 0 and count(p.deck, dragon.LAZING_FLAME) == 1


def test_gallant_gatekeeper():
    state = start()
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.GALLANT_GATEKEEPER, targets=(giant.uid,), pp=7)
    assert giant.fate == DESTROYED


def test_draconic_part_timer():
    state = start(first=0)
    p = state.players[0]
    p.leader_hp = 10
    plain = play(state, dragon.DRACONIC_PART_TIMER, pp=9)
    evolved = play(state, dragon.DRACONIC_PART_TIMER, pp=10)
    assert not plain.evolved and evolved.evolved and (evolved.atk, evolved.life) == (3, 5)
    apply(state, EndTurn())
    assert p.leader_hp == 13                      # 1 + 2


def test_dragonewt_pathfinder_modes():
    for mode in (0, 1):
        state = start()
        small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
        card = give(state, 0, dragon.DRAGONEWT_PATHFINDER)
        set_pp(state, 0, 5)
        assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}
        apply(state, PlayCard(card.uid, modes=(mode,)))
        assert big.fate == DESTROYED and small.fate == IN_PLAY
        assert card.evolved == (mode == 0) and card.has(Keyword.AMBUSH) == (mode == 1)


def test_blackflame_deluge():
    state = start()
    giant, bearer = put(state, 1, demo.GIANT), put(state, 1, demo.SHIELDBEARER)
    play(state, dragon.BLACKFLAME_DELUGE, pp=7)
    assert giant.fate == DESTROYED and bearer.fate == DESTROYED
    assert state.players[1].leader_hp == 17


def test_dragons_vale_elder_and_its_crest():
    state = start(first=0)
    p = state.players[0]
    elder = play(state, dragon.DRAGONS_VALE_ELDER, pp=10)
    crest = E.leader_area_card(state, 0, dragon.DRAGONS_VALE_ELDER_CREST)
    assert count(p.field, dragon.VASTWING_DRAGON) == 1 and crest.countdown == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(elder.uid, super_=True))
    assert crest.countdown == 4
    apply(state, EndTurn())
    assert count(p.field, dragon.VASTWING_DRAGON) == 2


def test_dragons_vale_elder_crest_runs_out():
    state = start(first=0)
    p = state.players[0]
    E.add_to_leader_area(state, 0, dragon.DRAGONS_VALE_ELDER_CREST)
    for _ in range(3):
        apply(state, EndTurn())
        apply(state, EndTurn())
    assert count(p.field, dragon.VASTWING_DRAGON) == 2
    assert E.leader_area_card(state, 0, dragon.DRAGONS_VALE_ELDER_CREST) is None


# --- set 10006 -----------------------------------------------------------------------

def test_resolute_dragonewt():
    state = start()
    p = state.players[0]
    p.hand.clear()
    vorlalai = give(state, 0, dragon.VORLALAI)
    dewt = play(state, dragon.RESOLUTE_DRAGONEWT, targets=(vorlalai.uid,), pp=3)
    assert count(p.field, dragon.VORLALAI) == 1 and p.hand == []
    E.destroy(state, dewt)
    resolve_queue(state)
    assert len(p.hand) == 2


def test_fruitfish():
    state = start()
    p = state.players[0]
    play(state, dragon.FRUITFISH, pp=2)
    assert count(p.field, dragon.FRUITFISH) == 1
    play(state, dragon.FRUITFISH, pp=6)
    assert count(p.field, dragon.FRUITFISH) == 4
    p.leader_hp = 10
    E.destroy(state, p.field[0])
    resolve_queue(state)
    assert p.leader_hp == 11


def test_advent_of_the_eld_blades():
    state = start()
    p = state.players[0]
    p.hand.clear()
    advent = give(state, 0, dragon.ADVENT_OF_THE_ELD_BLADES)
    set_pp(state, 0, 4)
    assert plays(state, advent.uid) == []         # a spell needs its target
    ally = put(state, 0, demo.FOOTMAN)
    apply(state, PlayCard(advent.uid, (ally.uid,)))
    assert (ally.atk, ally.life) == (3, 4)
    discarded = give(state, 0, dragon.ADVENT_OF_THE_ELD_BLADES)
    E.discard(state, discarded)
    resolve_queue(state)
    cheap = p.hand[-1]
    assert cheap.defn == dragon.ADVENT_OF_THE_ELD_BLADES and cheap.cost == 2
    E.discard(state, cheap)                       # costs 2 now: nothing comes back
    resolve_queue(state)
    assert p.hand == []


def test_decisive_swordmaster():
    state = start()
    p = state.players[0]
    p.hand.clear()
    vorlalai = give(state, 0, dragon.VORLALAI)
    sword = play(state, dragon.DECISIVE_SWORDMASTER, targets=(vorlalai.uid,), pp=4)
    assert count(p.field, dragon.VORLALAI) == 1 and sword.has(Keyword.BARRIER)


def test_spiked_dragon_evolves_at_end_of_turn():
    state = start(first=0)
    spiked = put(state, 0, dragon.SPIKED_DRAGON)
    giant = put(state, 1, demo.GIANT)
    apply(state, EndTurn())
    assert spiked.evolved and giant.life == 2 and state.players[1].leader_hp == 17


def test_spiked_dragon_point_evolution_triggers_too():
    state = start(first=0)
    spiked = put(state, 0, dragon.SPIKED_DRAGON)
    giant = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    apply(state, Evolve(spiked.uid))
    assert giant.life == 2 and state.players[1].leader_hp == 17
    apply(state, EndTurn())                       # already evolved: nothing more
    assert giant.life == 2 and state.players[1].leader_hp == 17


def test_impeding_pugilist_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    p.hand.clear()
    giants = [put(state, 1, demo.GIANT) for _ in range(2)]
    vorlalai = give(state, 0, dragon.VORLALAI)
    pugilist = play(state, dragon.IMPEDING_PUGILIST, targets=(vorlalai.uid,), pp=6)
    assert count(p.field, dragon.VORLALAI) == 1
    assert sum(g.fate == DESTROYED for g in giants) == 1
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    unlock_evolution(state, 0)
    apply(state, Evolve(pugilist.uid, targets=(depths.uid,)))
    assert all(g.fate == DESTROYED for g in giants) and state.players[1].leader_hp == 19


def test_impeding_pugilist_without_a_card_to_discard():
    state = start()
    state.players[0].hand.clear()
    giant = put(state, 1, demo.GIANT)
    card = give(state, 0, dragon.IMPEDING_PUGILIST)
    set_pp(state, 0, 6)
    assert plays(state, card.uid) == [PlayCard(card.uid)]
    apply(state, PlayCard(card.uid))
    assert giant.fate == DESTROYED


def test_beheading_eld_blades_damage_is_its_cost():
    state = start()
    giant = put(state, 1, demo.GIANT)
    tough = put(state, 1, demo.GIANT)
    E.buff(state, tough, 0, 3)                    # 5/8
    play(state, dragon.BEHEADING_ELD_BLADES, pp=7)
    assert giant.fate == DESTROYED and tough.life == 1


def test_beheading_eld_blades_discard_chain():
    state = start()
    p = state.players[0]
    p.hand.clear()
    blades = give(state, 0, dragon.BEHEADING_ELD_BLADES)
    costs = []
    while blades is not None:
        E.discard(state, blades)
        resolve_queue(state)
        blades = p.hand[-1] if p.hand else None
        if blades is not None:
            costs.append(blades.cost)
    assert costs == [5, 3]
    state = start()
    giant = put(state, 1, demo.GIANT)
    cheap = give(state, 0, dragon.BEHEADING_ELD_BLADES)
    E.set_cost(cheap, 3)
    set_pp(state, 0, 3)
    apply(state, PlayCard(cheap.uid))
    assert giant.life == 2


# --- set 10005 -----------------------------------------------------------------------

def test_springwell_steward_evolve_and_super_evolve():
    for super_, destroyed in ((False, 1), (True, 2)):
        state = start()
        unlock_evolution(state, 0)
        a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
        steward = put(state, 0, dragon.SPRINGWELL_STEWARD)
        apply(state, Evolve(steward.uid, super_, (a.uid, b.uid)))
        assert a.fate == DESTROYED and sum(g.fate == DESTROYED for g in (a, b)) == destroyed


def test_springwell_steward_with_one_enemy():
    state = start()
    unlock_evolution(state, 0)
    giant = put(state, 1, demo.GIANT)
    steward = put(state, 0, dragon.SPRINGWELL_STEWARD)
    assert {a.targets for a in evolves_of(state, steward.uid)} == {(giant.uid, giant.uid)}
    apply(state, Evolve(steward.uid, True, (giant.uid, giant.uid)))
    assert giant.fate == DESTROYED


def test_stormy_shamisen_shredder():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    play(state, dragon.STORMY_SHAMISEN_SHREDDER, pp=6)
    assert count(p.field, dragon.MAJESTIC_MEGALORCA) == 1 and p.leader_hp == 12
    play(state, dragon.MAJESTIC_MEGALORCA, pp=2)
    assert p.leader_hp == 14
    play(state, demo.FOOTMAN, pp=1)
    assert p.leader_hp == 14


def test_blade_of_the_crestpetal():
    state = start()
    p = state.players[0]
    p.deck = [state.new_instance(dragon.DRAGONSIGN, 0) for _ in range(5)]
    p.deck.insert(2, state.new_instance(demo.GIANT, 0))
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    E.buff(state, b, 0, 3)                        # 1/5
    play(state, dragon.BLADE_OF_THE_CRESTPETAL, pp=3)
    assert p.hand[-1].defn == demo.GIANT and len(p.deck) == 5
    assert sum(f.fate == DESTROYED for f in (a, b)) == 1     # X = 5
    play(state, dragon.BLADE_OF_THE_CRESTPETAL, pp=3)         # no follower left: nothing
    assert sum(f.fate == DESTROYED for f in (a, b)) == 1


def test_ironmace_dragoon():
    state = start()
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.IRONMACE_DRAGOON, targets=(giant.uid,), pp=8)
    assert giant.fate == DESTROYED and count(state.players[0].field, dragon.VASTWING_DRAGON) == 1


def test_jellyfish_dancer():
    state = start()
    p = state.players[0]
    p.hand.clear()
    dancer = play(state, dragon.JELLYFISH_DANCER, pp=2)
    assert count(p.hand, dragon.MAJESTIC_MEGALORCA) == 1
    play(state, demo.FOOTMAN, pp=1)
    assert not dancer.has(Keyword.RUSH)
    set_pp(state, 0, 2)
    apply(state, PlayCard(p.hand[0].uid))
    assert dancer.has(Keyword.RUSH) and dancer.has(Keyword.BANE)


def test_ruinbringer_super_evolve():
    state = start()
    p = state.players[0]
    p.deck = [state.new_instance(d, 0)
              for d in (demo.FOOTMAN, demo.RAIDER, demo.LANCER, demo.CAPTAIN, demo.GIANT)]
    odd = [c for c in p.deck if c.cost % 2]
    footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    ruin = put(state, 0, dragon.RUINBRINGER)
    apply(state, Evolve(ruin.uid, super_=True))
    assert [c.cost for c in p.deck] == [2, 4] and all(c.fate == BANISHED for c in odd)
    assert footman.fate == DESTROYED and giant.life == 4    # 3 split, oldest first


def test_ruinbringer_plain_evolve_does_nothing():
    state = start()
    deck = len(state.players[0].deck)
    unlock_evolution(state, 0)
    ruin = put(state, 0, dragon.RUINBRINGER)
    apply(state, Evolve(ruin.uid))
    assert len(state.players[0].deck) == deck


def test_yube_and_its_crest():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    yube = play(state, dragon.YUBE, pp=3)
    megalorca = next(c for c in p.field if c.defn == dragon.MAJESTIC_MEGALORCA)
    vorlalai = give(state, 0, dragon.VORLALAI)
    unlock_evolution(state, 0)
    apply(state, Evolve(yube.uid, targets=(vorlalai.uid,)))
    assert count(p.field, dragon.VORLALAI) == 1
    assert E.leader_area_card(state, 0, dragon.YUBE_CREST) is not None
    bearer, other = put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.SHIELDBEARER)   # 1/3
    apply(state, Attack(megalorca.uid, bearer.uid))           # Rush; 3 attack with the crest
    assert bearer.fate == DESTROYED and count(p.hand, dragon.MAJESTIC_MEGALORCA) == 1
    second = put(state, 0, dragon.MAJESTIC_MEGALORCA)
    apply(state, Attack(second.uid, other.uid))
    assert other.fate == DESTROYED and count(p.hand, dragon.MAJESTIC_MEGALORCA) == 1   # once per turn
    apply(state, EndTurn())
    assert megalorca.atk == 2


# --- set 10000 -----------------------------------------------------------------------

def test_searing_firenewt():
    state = start()
    footman = put(state, 1, demo.FOOTMAN)
    play(state, dragon.SEARING_FIRENEWT, targets=(footman.uid,), pp=2)
    assert footman.life == 1


def test_warrior_of_the_deep():
    state = start()
    play(state, dragon.WARRIOR_OF_THE_DEEP, pp=8)
    assert state.players[1].leader_hp == 14


def test_strike_of_the_dragonewt():
    for max_pp, life in ((6, 3), (7, 1)):
        state = start()
        giant = put(state, 1, demo.GIANT)
        play(state, dragon.STRIKE_OF_THE_DRAGONEWT, targets=(giant.uid,), pp=max_pp)
        assert giant.life == life


def test_draconic_berserker():
    for super_, lives in ((False, (1, 5)), (True, (1, 1))):
        state = start()
        unlock_evolution(state, 0)
        a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
        berserker = put(state, 0, dragon.DRACONIC_BERSERKER)
        apply(state, Evolve(berserker.uid, super_, (a.uid,)))
        assert (a.life, b.life) == lives


def test_battleforged_dragon_keeper():
    state = start()
    p = state.players[0]
    play(state, dragon.BATTLEFORGED_DRAGON_KEEPER, pp=6)
    assert count(p.field, dragon.VASTWING_DRAGON) == 0
    play(state, dragon.BATTLEFORGED_DRAGON_KEEPER, pp=7)
    assert count(p.field, dragon.VASTWING_DRAGON) == 1 and p.pp == 0


# --- set 10004 -----------------------------------------------------------------------

def test_mari_in_hand_gets_cheap_when_a_3_cost_super_evolves():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    mari = give(state, 0, dragon.MARI)
    unlock_evolution(state, 0)
    raider = put(state, 0, demo.RAIDER)           # 2-cost: doesn't count
    lancer = put(state, 0, demo.LANCER)           # 3-cost
    E.evolve(state, raider, super_=True)
    E.evolve(state, put(state, 0, demo.LANCER))   # evolving (not super) doesn't count
    resolve_queue(state)
    assert mari.cost == 2
    apply(state, Evolve(lancer.uid, super_=True))
    assert mari.cost == 0
    atk = (raider.atk, lancer.atk)
    apply(state, EndTurn())                       # in hand: no end-of-turn buff; cost expires
    assert mari.cost == 2 and (raider.atk, lancer.atk) == atk


def test_mari_on_the_field_buffs_a_super_evolved_ally():
    state = start(first=0)
    put(state, 0, dragon.MARI)
    lancer = put(state, 0, demo.LANCER)
    plain = put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(lancer.uid, super_=True))
    apply(state, EndTurn())
    assert (lancer.atk, lancer.life) == (7, 6) and (plain.atk, plain.life) == (1, 2)


def test_crescent_tube_ride():
    state = start(first=0)
    footman = put(state, 0, demo.FOOTMAN)
    play(state, dragon.CRESCENT_TUBE_RIDE, pp=2)
    crest = E.leader_area_card(state, 0, dragon.CRESCENT_TUBE_RIDE_CREST)
    assert crest is not None and crest.countdown == 4
    apply(state, EndTurn())
    assert (footman.atk, footman.life) == (2, 3)


def test_izmir():
    state = start()
    giant = put(state, 1, demo.GIANT)
    plain = play(state, dragon.IZMIR, pp=9)
    assert not plain.evolved and giant.life == 5
    evolved = play(state, dragon.IZMIR, pp=10)
    assert evolved.evolved and giant.life == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(plain.uid))               # any evolution triggers it
    assert giant.fate == DESTROYED


def test_mugen_super_skybound_art_and_super_evolve():
    state = start()
    p = state.players[0]
    early = play(state, dragon.MUGEN, pp=8)
    assert not early.has(Keyword.STORM)
    p.turns_taken = 15
    late = play(state, dragon.MUGEN, pp=8)
    assert late.has(Keyword.STORM) and Attack(late.uid, leader_uid(1)) in legal_actions(state)
    a, b, c = (put(state, 1, demo.GIANT) for _ in range(3))
    apply(state, Evolve(early.uid, super_=True, targets=(a.uid, b.uid)))
    assert (a.fate, b.fate, c.fate) == (DESTROYED, DESTROYED, IN_PLAY)


def test_mugen_plain_evolve_destroys_nothing():
    state = start()
    unlock_evolution(state, 0)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    mugen = put(state, 0, dragon.MUGEN)
    apply(state, Evolve(mugen.uid, targets=(a.uid, b.uid)))
    assert a.fate == IN_PLAY and b.fate == IN_PLAY


def test_maximum_love_bomb():
    state = start(first=0)
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.MAXIMUM_LOVE_BOMB, targets=(giant.uid,), pp=2)
    assert giant.life == 2
    apply(state, EndTurn())
    assert attacks_by(state, giant.uid) == []     # until the end of the opponent's turn
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert Attack(giant.uid, leader_uid(0)) in legal_actions(state)


def test_meg_skybound_art_and_ward():
    state = start()
    p = state.players[0]
    early = play(state, dragon.MEG, pp=3)
    assert not early.evolved and not early.has(Keyword.WARD)
    p.turns_taken = 10
    late = play(state, dragon.MEG, pp=3)
    assert late.super_evolved and (late.atk, late.life) == (5, 4)
    play(state, demo.LANCER, pp=3)
    assert not early.has(Keyword.WARD)
    play(state, demo.RAIDER, pp=2)                # 2-base-cost
    assert early.has(Keyword.WARD) and late.has(Keyword.WARD)


def test_meg_super_evolving_makes_mari_free():
    state = start()
    p = state.players[0]
    p.turns_taken = 10
    mari = give(state, 0, dragon.MARI)
    play(state, dragon.MEG, pp=3)
    assert mari.cost == 0


def test_primal_beast_absorption():
    state = start()
    p = state.players[0]
    p.hand.clear()
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 2, 2)
    play(state, dragon.PRIMAL_BEAST_ABSORPTION, targets=(giant.uid,), pp=5)
    assert giant.fate == BANISHED
    copy = p.hand[-1]
    assert copy.defn == demo.GIANT and copy.owner == 0 and (copy.atk, copy.life) == (5, 5)
    totem = put(state, 1, demo.TOTEM)             # amulets can be selected; banished: no Last Words
    play(state, dragon.PRIMAL_BEAST_ABSORPTION, targets=(totem.uid,), pp=5)
    resolve_queue(state)
    assert totem.fate == BANISHED and state.players[1].field == [] and p.hand[-1].defn == demo.TOTEM


def test_wilnas_fanfare_and_evolve():
    state = start()
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    wilnas = play(state, dragon.WILNAS, targets=(a.uid,), pp=7)
    assert a.fate == DESTROYED and wilnas.has(Keyword.INTIMIDATE)
    unlock_evolution(state, 0)
    apply(state, Evolve(wilnas.uid, targets=(b.uid,)))
    assert b.fate == DESTROYED


# --- fuzz ----------------------------------------------------------------------------

def _random_deck(rng, pool):
    deck = []
    while len(deck) < decks.DECK_SIZE:
        card = rng.choice(pool)
        if deck.count(card) < decks.MAX_COPIES:
            deck.append(card)
    return deck


def _check(state, action):
    assert not state.queue
    for p in state.players:
        assert len(p.field) <= FIELD_LIMIT and len(p.hand) <= HAND_LIMIT
        assert all(c.life > 0 for c in p.followers), action
        assert p.leader_hp <= p.leader_max_hp


def test_random_dragon_decks_play_out():
    pool = [c for c in collectible(Craft.DRAGON)
            if has_script(c.card_id) or c in dragon.KEYWORD_ONLY]
    assert sum(c.craft == Craft.DRAGON for c in pool) >= 60
    for g in range(100):
        rng = random.Random(g)
        deck0, deck1 = _random_deck(rng, pool), _random_deck(rng, pool)
        assert decks.validate(deck0, Craft.DRAGON) == [] and decks.validate(deck1, Craft.DRAGON) == []
        state = new_game(deck0, deck1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        winner = play_game(state, agents, on_action=_check)
        assert state.over and winner in (0, 1, DRAW)
