"""Dragoncraft cards of set 10 (Deicide in Nacreheim, 2026-10-28)."""
from itertools import combinations
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, demo, dragon
from svsim.cards.neutral import DIVINE_EVIDENCE
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, Evolve, PlayCard
from svsim.core.engine import apply, new_game, resolve_queue
from svsim.core.enums import DRAW, Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution

SET10 = [dragon.OBLIVIATIONIST_MARAUDER, dragon.FREEZING_ICENEWT, dragon.DANCE_OF_THE_WATERWYRM,
         dragon.OBLIVIATIONIST_SMUGGLER, dragon.DRAGONEWT_SCOUT, dragon.COLLECTION_MANIFEST,
         dragon.OBLIVIATIONIST_MUGGER, dragon.BIRDS_EYE_VIEW, dragon.LEIZAUT, dragon.JERVA]


def play(state, defn, targets=(), modes=(), pp=10, player=0):
    card = give(state, player, defn)
    set_pp(state, player, pp)
    apply(state, PlayCard(card.uid, tuple(targets), tuple(modes)))
    return card


def test_all_ten_are_scripted_and_listed():
    assert len({c.card_id for c in SET10}) == 10
    for defn in SET10:
        assert has_script(defn.card_id) and defn in dragon.CARDS and defn.craft == Craft.DRAGON


def test_obliviationist_marauder_rush_and_last_words():
    state = start(first=0)
    p = state.players[0]
    marauder = play(state, dragon.OBLIVIATIONIST_MARAUDER, pp=1)
    assert marauder.has(Keyword.RUSH)
    p.hand.clear()
    E.destroy(state, marauder)
    resolve_queue(state)
    assert [c.defn for c in p.hand] == [DIVINE_EVIDENCE]


def test_freezing_icenewt_once_unenhanced():
    state = start(first=0)
    giants = [put(state, 1, demo.GIANT) for _ in range(3)]
    newt = play(state, dragon.FREEZING_ICENEWT, pp=6)
    assert sorted(g.life for g in giants) == [2, 5, 5]
    assert (newt.atk, newt.life) == (2, 2)


def test_freezing_icenewt_enhanced_three_times_and_buff():
    state = start(first=0)
    giants = [put(state, 1, demo.GIANT) for _ in range(3)]
    for g in giants:
        E.buff(state, g, 0, 10)
    newt = play(state, dragon.FREEZING_ICENEWT, pp=7)
    assert sum(15 - g.life for g in giants) == 9
    assert (newt.atk, newt.life) == (7, 7)


def test_freezing_icenewt_rerolls_each_time():
    """Three hits on a board of 1-defense followers kill three of them (each hit picks a live one)."""
    state = start(first=0)
    wisps = [put(state, 1, demo.WISP) for _ in range(4)]
    play(state, dragon.FREEZING_ICENEWT, pp=7)
    assert sum(w.fate == DESTROYED for w in wisps) == 3


def test_dance_of_the_waterwyrm_draws_heals_and_ramps_in_overflow():
    state = start(first=0)
    p = state.players[0]
    p.leader_hp = 15
    hand = len(p.hand)
    play(state, dragon.DANCE_OF_THE_WATERWYRM, pp=3)
    assert len(p.hand) == hand + 1 and p.leader_hp == 16 and p.max_pp == 3
    play(state, dragon.DANCE_OF_THE_WATERWYRM, pp=7)
    assert E.overflow(state, 0) and p.max_pp == 8


def test_obliviationist_smuggler_destroys_two_and_adds_two_evidence():
    state = start(first=0)
    p = state.players[0]
    a, b, c = (put(state, 1, demo.GIANT) for _ in range(3))
    p.hand.clear()
    play(state, dragon.OBLIVIATIONIST_SMUGGLER, targets=(a.uid, c.uid), pp=7)
    assert a.fate == DESTROYED and c.fate == DESTROYED and b.fate == IN_PLAY
    assert count(p.hand, DIVINE_EVIDENCE) == 2


def test_dragonewt_scout_ambush_and_strike_evolves_another_ally():
    state = start(first=0)
    unlock_evolution(state, 0)
    p = state.players[0]
    scout = put(state, 0, dragon.DRAGONEWT_SCOUT)
    assert scout.has(Keyword.AMBUSH)
    evolved = put(state, 0, demo.FOOTMAN)
    E.evolve(state, evolved)
    plain = put(state, 0, demo.FOOTMAN)
    ep = p.ep
    apply(state, Attack(scout.uid, leader_uid(1)))
    assert plain.evolved and (plain.atk, plain.life) == (3, 4)
    assert not scout.evolved and p.ep == ep


def test_dragonewt_scout_with_no_other_unevolved_ally():
    state = start(first=0)
    scout = put(state, 0, dragon.DRAGONEWT_SCOUT)
    apply(state, Attack(scout.uid, leader_uid(1)))
    assert not scout.evolved and state.players[1].leader_hp == 19


def _evidence_in_hand(state, player=0, n=1):
    return [give(state, player, DIVINE_EVIDENCE) for _ in range(n)]


def test_collection_manifest_without_a_clue_only_damages():
    state = start(first=0, deck=[demo.GIANT] * 40)
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    p.hand.clear()
    play(state, dragon.COLLECTION_MANIFEST, pp=2)
    assert giant.life == 1 and p.hand == []


def test_collection_manifest_discards_a_clue_and_draws_five_plus():
    deck = [demo.FOOTMAN] * 20 + [demo.GIANT] * 20
    state = start(first=0, deck=deck)
    p = state.players[0]
    p.hand.clear()
    _evidence_in_hand(state, n=2)
    shadows = p.shadows
    play(state, dragon.COLLECTION_MANIFEST, pp=2)
    assert count(p.hand, DIVINE_EVIDENCE) == 1 and p.shadows == shadows + 2   # the discard and the spell
    assert [c.defn for c in p.hand if c.defn != DIVINE_EVIDENCE] == [demo.GIANT]


def test_obliviationist_mugger_ramps_only_with_a_clue():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    play(state, dragon.OBLIVIATIONIST_MUGGER, pp=4)
    assert p.max_pp == 4
    _evidence_in_hand(state)
    play(state, dragon.OBLIVIATIONIST_MUGGER, pp=4)
    assert p.max_pp == 5 and count(p.hand, DIVINE_EVIDENCE) == 0


def test_obliviationist_mugger_evolve_deals_three():
    state = start(first=0)
    unlock_evolution(state, 0)
    giant = put(state, 1, demo.GIANT)
    mugger = put(state, 0, dragon.OBLIVIATIONIST_MUGGER)
    apply(state, Evolve(mugger.uid, False, (giant.uid,)))
    assert giant.life == 2


def test_birds_eye_view_summon_and_buff_leftmost_two():
    state = start(first=0)
    p = state.players[0]
    left, middle, right = (put(state, 0, demo.FOOTMAN) for _ in range(3))
    play(state, dragon.BIRDS_EYE_VIEW, modes=(0, 1), pp=3)
    assert [f.atk for f in (left, middle, right)] == [2, 2, 1]
    assert p.field[-1].defn == dragon.INQUIRING_MISCHIEF


def test_birds_eye_view_evidence_and_damage():
    state = start(first=0)
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    p.hand.clear()
    play(state, dragon.BIRDS_EYE_VIEW, modes=(2, 3), pp=3)
    assert count(p.hand, DIVINE_EVIDENCE) == 3 and giant.life == 1
    assert not any(f.defn == dragon.INQUIRING_MISCHIEF for f in p.field)


def test_leizaut_banishes_cheap_deck_cards_discards_clues_and_shoots():
    deck = [demo.FOOTMAN] * 15 + [demo.CAPTAIN] * 5 + [demo.GIANT] * 20
    state = start(first=0, deck=deck)
    p = state.players[0]
    giants = [put(state, 1, demo.GIANT) for _ in range(3)]
    p.hand.clear()
    _evidence_in_hand(state, n=2)
    give(state, 0, demo.FOOTMAN)
    leizaut = play(state, dragon.LEIZAUT, pp=10)
    assert all(c.defn.cost >= 5 for c in p.deck_view()) and len(p.deck_view()) > 0
    assert [c.defn for c in p.hand] == [demo.FOOTMAN]
    assert sum(g.fate == DESTROYED for g in giants) == 2
    assert leizaut.has(Keyword.STORM)


def test_leizaut_with_no_clue_deals_nothing():
    state = start(first=0)
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    p.hand.clear()
    play(state, dragon.LEIZAUT, pp=10)
    assert giant.life == 5 and p.deck_view() == []          # a deck of Footmen: all banished


def test_jerva_splits_missing_enemy_defense():
    state = start(first=0)
    enemy = state.players[1]
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    enemy.leader_hp = enemy.leader_max_hp - 4
    play(state, dragon.JERVA, pp=6)
    assert a.fate == DESTROYED and b.life == 3


def test_jerva_at_full_enemy_defense_deals_nothing():
    state = start(first=0)
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.JERVA, pp=6)
    assert giant.life == 5


def test_jerva_super_evolve_storm_and_ward():
    state = start(first=0)
    unlock_evolution(state, 0)
    jerva = put(state, 0, dragon.JERVA, ready=False)
    apply(state, Evolve(jerva.uid, True))
    assert jerva.has(Keyword.STORM) and jerva.has(Keyword.WARD)
    jerva2 = put(state, 0, dragon.JERVA, ready=False)
    apply(state, Evolve(jerva2.uid, False))
    assert not jerva2.has(Keyword.STORM) and not jerva2.has(Keyword.WARD)


def test_random_decks_with_set_10_play_out():
    pool = [c for c in collectible(Craft.DRAGON) if has_script(c.card_id) or c in dragon.KEYWORD_ONLY]
    assert all(c in pool for c in SET10)
    for g in range(30):
        rng = random.Random(1000 + g)
        deck0 = [c for c in SET10 for _ in range(3)] + [rng.choice(pool) for _ in range(10)]
        deck1 = [rng.choice(pool) for _ in range(decks.DECK_SIZE)]
        state = new_game(deck0, deck1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        winner = play_game(state, agents)
        assert state.over and winner in (0, 1, DRAW)


# --- gaps found by the analysis line's review (2026-10-28) ---------------------------------

def test_obliviationist_mugger_discards_only_one_of_two_clues():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    _evidence_in_hand(state, n=2)
    play(state, dragon.OBLIVIATIONIST_MUGGER, pp=4)
    assert count(p.hand, DIVINE_EVIDENCE) == 1 and p.max_pp == 5


def test_dragonewt_scout_evolves_only_one_of_two_candidates():
    state = start(first=0)
    scout = put(state, 0, dragon.DRAGONEWT_SCOUT)
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    apply(state, Attack(scout.uid, leader_uid(1)))
    assert a.evolved + b.evolved == 1


def test_obliviationist_smuggler_offers_only_pairs_of_targets():
    state = start(first=0)
    enemies = [put(state, 1, demo.GIANT) for _ in range(3)]
    smuggler = give(state, 0, dragon.OBLIVIATIONIST_SMUGGLER)
    set_pp(state, 0, 7)
    options = {a.targets for a in plays(state, smuggler.uid)}
    assert options and all(len(t) == 2 for t in options)
    assert {frozenset(t) for t in options} == {frozenset(p) for p in combinations([e.uid for e in enemies], 2)}


def test_birds_eye_view_offers_the_six_pairs_of_modes():
    state = start(first=0)
    view = give(state, 0, dragon.BIRDS_EYE_VIEW)
    set_pp(state, 0, 3)
    assert {tuple(sorted(a.modes)) for a in plays(state, view.uid)} == set(combinations(range(4), 2))


def test_birds_eye_view_modes_one_and_three():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    ally = put(state, 0, demo.FOOTMAN)
    giant = put(state, 1, demo.GIANT)
    play(state, dragon.BIRDS_EYE_VIEW, modes=(0, 2), pp=3)     # summon, evidence: no buff, no damage
    assert count(p.hand, DIVINE_EVIDENCE) == 3 and ally.atk == 1 and giant.life == 5
    assert [f.defn for f in p.field] == [demo.FOOTMAN, dragon.INQUIRING_MISCHIEF]
    p.hand.clear()
    play(state, dragon.BIRDS_EYE_VIEW, modes=(1, 3), pp=3)     # buff, damage: no summon, no evidence
    assert ally.atk == 2 and giant.life == 1 and p.hand == [] and len(p.field) == 2


def test_leizaut_deals_exactly_eight():
    state = start(first=0)
    p = state.players[0]
    big = put(state, 1, demo.GIANT)
    big.life = big.max_life = 20
    p.hand.clear()
    _evidence_in_hand(state)
    play(state, dragon.LEIZAUT, pp=10)
    assert big.life == 12


def test_jerva_with_one_missing_defense_deals_one():
    state = start(first=0)
    enemy = state.players[1]
    giant = put(state, 1, demo.GIANT)
    enemy.leader_hp = enemy.leader_max_hp - 1
    play(state, dragon.JERVA, pp=6)
    assert giant.life == 4
