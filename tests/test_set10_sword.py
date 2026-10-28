"""Swordcraft cards of set 10 (Deicide in Nacreheim, 2026-10-28) and Crest: Almaelys."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, neutral, rune, sword
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Engage, Evolve, PlayCard
from svsim.core.engine import apply, new_game, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY

from helpers import count, give, put, set_pp, start, unlock_evolution
from test_cards_sword import WALL, check_invariants, random_sword_deck

BANE, DRAIN, WARD, STORM, RUSH, BARRIER = (Keyword.BANE, Keyword.DRAIN, Keyword.WARD, Keyword.STORM,
                                           Keyword.RUSH, Keyword.BARRIER)


def fresh(pp=10):
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, pp)
    return state


def play(state, card, targets=()):
    apply(state, PlayCard(card.uid, tuple(targets)))
    return card


def engage_a_clue(state):
    """Player 0 plays a Divine Evidence and engages it (2 play points)."""
    evidence = play(state, give(state, 0, neutral.DIVINE_EVIDENCE))
    apply(state, Engage(E.clue_amulet(state, 0).uid))
    return evidence


def stats(inst):
    return inst.atk, inst.life, inst.max_life


# --- the four "swap on a Clue Engage" followers -------------------------------------------------

def test_clue_engage_swaps_a_card_in_hand_and_gives_plus_one_attack():
    state = fresh()
    newsie = give(state, 0, sword.GUILELESS_NEWSIE)            # 2/1
    architect = give(state, 0, sword.CHEEKY_ARCHITECT)         # 1/4
    dilettante = give(state, 0, sword.PLACID_DILETTANTE)       # 5/1
    no_life = give(state, 0, sword.NO_LIFE)                    # 5/6
    engage_a_clue(state)
    assert stats(newsie) == (2, 2, 2) and stats(architect) == (5, 1, 1)
    assert stats(dilettante) == (2, 5, 5) and stats(no_life) == (7, 5, 5)


def test_clue_engage_swaps_on_the_field_too_from_current_defense():
    state = fresh()
    architect = put(state, 0, sword.CHEEKY_ARCHITECT)           # 1/4
    architect.life = 3                                          # damaged
    engage_a_clue(state)
    assert stats(architect) == (4, 1, 1)


def test_a_follower_swapped_to_zero_defense_dies():
    state = fresh()
    newsie = put(state, 0, sword.GUILELESS_NEWSIE)
    newsie.atk = 0
    engage_a_clue(state)
    assert newsie.fate == DESTROYED


def test_engaging_an_amulet_that_is_not_a_clue_swaps_nothing():
    state = fresh()
    newsie = give(state, 0, sword.GUILELESS_NEWSIE)
    brew = E.summon(state, 0, rune.WITCHS_NEW_BREW)
    apply(state, Engage(brew.uid))
    assert stats(newsie) == (2, 1, 1)


def test_the_opponents_clue_engage_does_not_swap_mine():
    state = fresh()
    newsie = give(state, 1, sword.GUILELESS_NEWSIE)
    engage_a_clue(state)
    assert stats(newsie) == (2, 1, 1)


def test_swapped_stats_are_kept_when_played():
    state = fresh()
    architect = give(state, 0, sword.CHEEKY_ARCHITECT)
    engage_a_clue(state)                                        # 1/4 -> 5/1
    enemy = put(state, 1, WALL)
    play(state, architect, (enemy.uid,))
    assert stats(architect) == (5, 1, 1) and enemy.life == 20 - 5


# --- Guileless Newsie --------------------------------------------------------------------------

def test_guileless_newsie_enhance_summons_an_exact_copy():
    for pp, copies in ((2, 0), (4, 1)):
        state = fresh(pp)
        newsie = give(state, 0, sword.GUILELESS_NEWSIE)
        newsie.atk, newsie.life, newsie.max_life = 3, 4, 4
        play(state, newsie)
        others = [f for f in state.players[0].followers if f is not newsie]
        assert len(others) == copies and newsie.has(RUSH)
        assert all(c.defn.card_id == sword.GUILELESS_NEWSIE.card_id and stats(c) == (3, 4, 4)
                   for c in others)


def test_guileless_newsie_last_words_summon_a_divine_evidence():
    state = fresh()
    newsie = put(state, 0, sword.GUILELESS_NEWSIE)
    E.destroy(state, newsie)
    resolve_queue(state)
    assert E.clue_amulet(state, 0) is not None and E.clues(state, 0) == 1


# --- Bejeweled Lady ----------------------------------------------------------------------------

def test_bejeweled_lady_adds_a_necklace_and_hits_all_enemies_once_a_turn():
    state = fresh()
    p, o = state.players
    play(state, give(state, 0, sword.BEJEWELED_LADY))
    assert count(p.hand, sword.GILDED_NECKLACE) == 1
    enemies = [put(state, 1, WALL), put(state, 1, WALL)]
    hp = o.leader_hp
    play(state, give(state, 0, sword.GILDED_GOBLET))
    assert [e.life for e in enemies] == [18, 18] and o.leader_hp == hp - 2
    play(state, give(state, 0, sword.GILDED_GOBLET))            # once per turn
    assert [e.life for e in enemies] == [18, 18] and o.leader_hp == hp - 2
    play(state, give(state, 0, sword.STEELCLAD_KNIGHT))         # not a spell
    apply(state, EndTurn())
    apply(state, EndTurn())
    set_pp(state, 0, 10)
    play(state, give(state, 0, sword.GILDED_GOBLET))            # a new turn
    assert [e.life for e in enemies] == [16, 16] and o.leader_hp == hp - 4


# --- Onward, Charge! ---------------------------------------------------------------------------

def test_onward_charge_summons_two_evolved_barrier_knights():
    state = fresh()
    play(state, give(state, 0, sword.ONWARD_CHARGE))
    knights = state.players[0].followers
    assert len(knights) == 2 and all(k.defn.card_id == sword.STEELCLAD_KNIGHT.card_id for k in knights)
    assert all(k.evolved and k.has(BARRIER) for k in knights)


# --- Cheeky Architect --------------------------------------------------------------------------

def test_cheeky_architect_deals_its_attack_summons_evidence_and_evolve_summons_a_newsie():
    state = fresh()
    enemy = put(state, 1, WALL)
    architect = give(state, 0, sword.CHEEKY_ARCHITECT)
    architect.atk = 3
    play(state, architect, (enemy.uid,))
    assert enemy.life == 17 and E.clues(state, 0) == 1
    architect.entered_turn = -1
    unlock_evolution(state, 0)
    apply(state, Evolve(architect.uid))
    assert count(state.players[0].field, sword.GUILELESS_NEWSIE) == 1


# --- Errant Knight -----------------------------------------------------------------------------

def test_errant_knight_banishes_only_with_an_allied_amulet():
    for amulet in (False, True):
        state = fresh()
        enemy = put(state, 1, WALL)
        if amulet:
            E.summon(state, 0, rune.WITCHS_NEW_BREW)
        knight = play(state, give(state, 0, sword.ERRANT_KNIGHT), (enemy.uid,))
        assert knight.has(WARD)
        assert enemy.fate == (BANISHED if amulet else IN_PLAY)


def test_errant_knight_super_evolve_replicates_and_plain_evolve_does_not():
    for super_ in (False, True):
        state = fresh()
        enemy = put(state, 1, WALL)
        E.summon(state, 0, neutral.DIVINE_EVIDENCE)
        knight = put(state, 0, sword.ERRANT_KNIGHT)
        unlock_evolution(state, 0)
        apply(state, Evolve(knight.uid, super_=super_, targets=(enemy.uid,) if super_ else ()))
        assert enemy.fate == (BANISHED if super_ else IN_PLAY)


# --- Dichotomous Forensics ---------------------------------------------------------------------

def test_dichotomous_forensics_deals_10_after_a_clue_engage():
    for engaged, dealt in ((False, 5), (True, 10)):
        state = fresh()
        enemy = put(state, 1, WALL)
        if engaged:
            engage_a_clue(state)
        play(state, give(state, 0, sword.DICHOTOMOUS_FORENSICS), (enemy.uid,))
        assert enemy.life == 20 - dealt


# --- Placid Dilettante -------------------------------------------------------------------------

def test_placid_dilettante_summons_newsies_with_its_stats_and_evolve_gives_bane():
    state = fresh()
    dilettante = give(state, 0, sword.PLACID_DILETTANTE)
    engage_a_clue(state)                                        # 5/1 -> 2/5
    play(state, dilettante)
    newsies = [f for f in state.players[0].followers if f is not dilettante]
    assert len(newsies) == 2 and all(stats(n) == (2, 5, 5) for n in newsies)
    assert all(n.defn.card_id == sword.GUILELESS_NEWSIE.card_id for n in newsies)
    dilettante.entered_turn = -1
    unlock_evolution(state, 0)
    apply(state, Evolve(dilettante.uid))
    assert all(n.has(BANE) for n in newsies) and not dilettante.has(BANE)


# --- No Life's Cross-Examination ---------------------------------------------------------------

def test_cross_examination_summons_evidence_and_a_newsie_after_a_clue_engage():
    for engaged in (False, True):
        state = fresh()
        if engaged:
            engage_a_clue(state)
        play(state, give(state, 0, sword.NO_LIFES_CROSS_EXAMINATION))
        assert E.clue_amulet(state, 0) is not None
        assert count(state.players[0].field, sword.GUILELESS_NEWSIE) == int(engaged)


# --- No Life ------------------------------------------------------------------------------------

def test_no_life_copies_itself_and_keywords_follow_its_stats():
    cases = (((5, 6), BANE, DRAIN), ((7, 5), WARD, STORM), ((5, 5), None, None))
    for (atk, life), copy_kw, own_kw in cases:
        state = fresh()
        no_life = give(state, 0, sword.NO_LIFE)
        no_life.atk, no_life.life, no_life.max_life = atk, life, life
        play(state, no_life)
        copies = [f for f in state.players[0].followers if f is not no_life]
        assert len(copies) == 1 and stats(copies[0]) == (atk, life, life) and no_life.has(RUSH)
        copy = copies[0]
        for kw in (BANE, DRAIN, WARD, STORM):
            assert copy.has(kw) == (kw == copy_kw)
            assert no_life.has(kw) == (kw == own_kw)


# --- Almaelys and her crest --------------------------------------------------------------------

def test_almaelys_adds_gold_and_evolve_gains_the_crest():
    state = fresh()
    almaelys = play(state, give(state, 0, sword.ALMAELYS))
    assert count(state.players[0].hand, sword.GLITTERING_GOLD) == 1
    almaelys.entered_turn = -1
    unlock_evolution(state, 0)
    apply(state, Evolve(almaelys.uid))
    crest = E.leader_area_card(state, 0, sword.ALMAELYS_CREST)
    assert crest is not None and crest.countdown == 2


def test_almaelys_super_evolve_delays_the_crest_by_2():
    state = fresh()
    almaelys = put(state, 0, sword.ALMAELYS)
    unlock_evolution(state, 0)
    apply(state, Evolve(almaelys.uid, super_=True))
    assert E.leader_area_card(state, 0, sword.ALMAELYS_CREST).countdown == 4


def test_almaelys_crest_gives_free_blade_then_goblet_and_repeats():
    state = fresh()
    p = state.players[0]
    crest = E.add_to_leader_area(state, 0, sword.ALMAELYS_CREST)
    crest.countdown = 5
    got = []
    for _ in range(3):
        apply(state, EndTurn())
        new = p.hand[-1]
        got.append((new.defn.card_id, new.cost))
        apply(state, EndTurn())                                  # player 0 draws at turn start
    blade, goblet = sword.GILDED_BLADE.card_id, sword.GILDED_GOBLET.card_id
    assert got == [(blade, 0), (goblet, 0), (blade, 0)]


def test_almaelys_crest_runs_twice_on_its_own_count():
    state = fresh()
    p = state.players[0]
    E.add_to_leader_area(state, 0, sword.ALMAELYS_CREST)
    for _ in range(3):
        apply(state, EndTurn())
        apply(state, EndTurn())
    golds = count(p.hand, sword.GILDED_BLADE) + count(p.hand, sword.GILDED_GOBLET)
    assert golds == 2 and E.leader_area_card(state, 0, sword.ALMAELYS_CREST) is None


# --- fuzz ---------------------------------------------------------------------------------------

SET_10 = [sword.GUILELESS_NEWSIE, sword.BEJEWELED_LADY, sword.ONWARD_CHARGE, sword.CHEEKY_ARCHITECT,
          sword.ERRANT_KNIGHT, sword.DICHOTOMOUS_FORENSICS, sword.PLACID_DILETTANTE,
          sword.NO_LIFES_CROSS_EXAMINATION, sword.NO_LIFE, sword.ALMAELYS]


def set_10_deck(rng: random.Random) -> list:
    """2 copies of each set-10 Swordcraft card, the rest from a random Swordcraft deck."""
    deck = SET_10 * 2
    while len(deck) < decks.DECK_SIZE:
        for c in random_sword_deck(rng):
            if len(deck) < decks.DECK_SIZE and deck.count(c) < decks.MAX_COPIES:
                deck.append(c)
    return deck


def test_random_swordcraft_decks_with_set_10_play_out():
    for g in range(20):
        rng = random.Random(1000 + g)
        deck0, deck1 = set_10_deck(rng), set_10_deck(rng)
        assert decks.validate(deck0, Craft.SWORD) == [] and decks.validate(deck1, Craft.SWORD) == []
        state = new_game(deck0, deck1, seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        winner = play_game(state, agents, on_action=check_invariants)
        assert state.over and winner in (0, 1, -1)
