"""Runecraft cards, their tokens, crests and faith."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import demo, rune
from svsim.cards.pool import POOL, ROTATION_IDS, collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, has_script
from svsim.core.state import DESTROYED, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution
from test_fuzz import check_invariants

OTS = rune.OBSESSED_TEST_SUBJECT
KEYWORDS_ONLY = {rune.CRYSTALSPAWN.card_id, rune.CLAY_GOLEM.card_id, rune.GUARDIAN_GOLEM.card_id}


def needs_script(defn) -> bool:
    """Whether a card has abilities beyond keywords (pool data without the flag:
    every Rune card but the keyword-only ones, and every other card)."""
    fallback = defn.craft != Craft.RUNE or defn.card_id not in KEYWORDS_ONLY
    return getattr(defn, "has_ability", fallback)


def sigils(state, player=0, n=None):
    """Earth sigils on `player`'s field; with `n`, first gain n of them."""
    if n is not None:
        E.gain_earth_sigils(state, player, n, rune.MAGIC_SEDIMENT)
    return E.earth_sigils(state, player)


def boost(state, card, times=1, player=0):
    E.spellboost(state, player, times, cards=[card])
    resolve_queue(state)


def on_field(state, player, defn):
    return [c for c in state.players[player].field if c.defn.card_id == defn.card_id]


def kill(state, inst):
    E.destroy(state, inst)
    resolve_queue(state)


class ThreeAttacks(CardScript):
    attacks_per_turn = 3


# --- coverage ------------------------------------------------------------------------------

def test_every_rune_card_with_abilities_has_a_script():
    rune_cards = [POOL[i] for i in ROTATION_IDS if POOL[i].craft == Craft.RUNE]
    missing = [c.name for c in rune_cards if needs_script(c) and not has_script(c.card_id)]
    assert missing == []
    assert not any(has_script(i) for i in KEYWORDS_ONLY)
    assert all(has_script(c.card_id) for c in rune.LEADER_AREA)


# --- set 9 -----------------------------------------------------------------------------------

def test_obsessed_test_subject_qa_counts_copies_as_they_enter():
    """Official Q&A: four have entered, Sephie's Fanfare summons two: 2/2 then 5/5."""
    state = start()
    p = state.players[0]
    for _ in range(4):
        set_pp(state, 0, 2)
        ots = give(state, 0, OTS)
        apply(state, PlayCard(ots.uid))
        assert (ots.atk, ots.life) == (2, 2)
        kill(state, ots)                              # gone, but still counted
    assert rune.entered_test_subjects(state, 0) == 4
    set_pp(state, 0, 7)
    sephie = give(state, 0, rune.SEPHIE)
    apply(state, PlayCard(sephie.uid))
    first, second = on_field(state, 0, OTS)
    assert (first.atk, first.life) == (2, 2) and (second.atk, second.life) == (5, 5)
    assert rune.entered_test_subjects(state, 0) == 6
    assert rune.entered_test_subjects(state, 1) == 0
    set_pp(state, 0, 2)
    played = give(state, 0, OTS)
    apply(state, PlayCard(played.uid))
    enemy = put(state, 1, demo.FOOTMAN)
    assert (played.atk, played.life) == (5, 5) and p.field[-1] is played
    assert Attack(played.uid, enemy.uid) in legal_actions(state)        # Rush


def test_key_spirit_fanfare_and_evolve_spellboosts_a_card_four_times():
    state = start()
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    spirit = give(state, 0, rune.KEY_SPIRIT)
    apply(state, PlayCard(spirit.uid, (enemy.uid,)))
    assert enemy.fate == DESTROYED and state.players[1].leader_hp == 16
    unlock_evolution(state, 0)
    blast = give(state, 0, rune.STORMY_BLAST)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == spirit.uid]
    assert {a.targets for a in evolves} == {(blast.uid,)}     # Footmen have no On Spellboost
    apply(state, Evolve(spirit.uid, False, (blast.uid,)))
    assert blast.counters["x"] == 6 and blast.counters["spellboost"] == 4


def test_miscalculated_experiment_and_truth_summons():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.MISCALCULATED_EXPERIMENT).uid))
    assert count(p.hand, rune.TRUTH_SUMMONS) == 3
    set_pp(state, 0, 2)
    summons = next(c for c in p.hand if c.defn == rune.TRUTH_SUMMONS)
    apply(state, PlayCard(summons.uid))
    assert [c.defn for c in p.field] == [rune.CLAY_GOLEM]


def test_enamored_researcher_enhance_and_evolve():
    state = start()
    set_pp(state, 0, 4)
    researcher = give(state, 0, rune.ENAMORED_RESEARCHER)
    apply(state, PlayCard(researcher.uid))
    subjects = on_field(state, 0, OTS)
    assert len(subjects) == 2 and not any(s.has(Keyword.WARD) for s in subjects)
    unlock_evolution(state, 0)
    apply(state, Evolve(researcher.uid, False, (subjects[0].uid,)))
    assert subjects[0].has(Keyword.BANE) and not subjects[1].has(Keyword.BANE)

    state = start()
    set_pp(state, 0, 8)
    researcher = give(state, 0, rune.ENAMORED_RESEARCHER)
    apply(state, PlayCard(researcher.uid))
    subjects = on_field(state, 0, OTS)
    assert len(subjects) == 3 and all(s.has(Keyword.WARD) for s in subjects)
    assert state.players[0].pp == 0


def test_noble_philosopher_redraws_the_hand():
    state = start()
    p = state.players[0]
    give(state, 0, rune.FORESIGHT)
    philosopher = give(state, 0, rune.NOBLE_PHILOSOPHER)
    set_pp(state, 0, 3)
    hand, deck = len(p.hand) - 1, len(p.deck)
    apply(state, PlayCard(philosopher.uid))
    assert len(p.hand) == hand and len(p.deck) == deck


def test_humane_love():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 3)
    apply(state, PlayCard(give(state, 0, rune.HUMANE_LOVE).uid))
    (summoned,) = on_field(state, 0, OTS)
    assert (summoned.atk, summoned.life) == (3, 2)
    assert p.hand[-1].defn == OTS and p.hand[-1].atk == 3
    set_pp(state, 0, 2)
    apply(state, PlayCard(p.hand[-1].uid))
    assert on_field(state, 0, OTS)[-1].atk == 3          # the buff stays with the card


def test_ecstatic_scholar_fuse_enables_drain():
    for fused in (True, False):
        state = start()
        p = state.players[0]
        scholar = give(state, 0, rune.ECSTATIC_SCHOLAR)
        foresight = give(state, 0, rune.FORESIGHT)
        if fused:
            assert Fuse(scholar.uid, (foresight.uid,)) in legal_actions(state)
            apply(state, Fuse(scholar.uid, (foresight.uid,)))
        hand = len(p.hand)
        set_pp(state, 0, 5)
        apply(state, PlayCard(scholar.uid))
        assert len(p.hand) == hand - 1 + 2
        (subject,) = on_field(state, 0, OTS)
        unlock_evolution(state, 0)
        apply(state, Evolve(scholar.uid, True, (subject.uid,)))
        assert subject.has(Keyword.DRAIN) == fused


def test_obsidian_raven():
    state = start()
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.OBSIDIAN_RAVEN).uid))
    assert a.fate == DESTROYED and b.fate == DESTROYED
    assert len(on_field(state, 0, OTS)) == 1


def test_sephie_fuse_spends_two_play_points():
    state = start()
    p = state.players[0]
    sephie = give(state, 0, rune.SEPHIE)
    fodder = give(state, 0, rune.FORESIGHT)
    set_pp(state, 0, 3)
    apply(state, Fuse(sephie.uid, (fodder.uid,)))
    assert p.pp == 1 and len(on_field(state, 0, OTS)) == 1
    other = give(state, 0, rune.SEPHIE)
    apply(state, Fuse(other.uid, (give(state, 0, rune.FORESIGHT).uid,)))
    assert p.pp == 1 and len(on_field(state, 0, OTS)) == 1   # can't spend 2: nothing
    set_pp(state, 0, 7)
    apply(state, PlayCard(sephie.uid))
    assert len(on_field(state, 0, OTS)) == 3
    unlock_evolution(state, 0)
    apply(state, Evolve(sephie.uid, True))
    assert [c.defn for c in p.leader_area] == [rune.SEPHIE_CREST]


def test_sephie_crest_gives_storm_once_per_turn():
    state = start(first=0)
    E.add_to_leader_area(state, 0, rune.SEPHIE_CREST)
    set_pp(state, 0, 4)
    first, second = give(state, 0, OTS), give(state, 0, OTS)
    apply(state, PlayCard(first.uid))
    apply(state, PlayCard(second.uid))
    assert first.has(Keyword.STORM) and not second.has(Keyword.STORM)
    assert Attack(first.uid, leader_uid(1)) in legal_actions(state)


def test_spellboost_cost_reducers():
    for defn in (rune.PHYLENE, rune.BLAZE_DESTROYER, rune.SAMMY_AND_MARIE,
                 rune.WOODSONG_HAIKUMASTER, rune.ARA):
        state = start()
        card = give(state, 0, defn)
        set_pp(state, 0, 1)
        apply(state, PlayCard(give(state, 0, rune.FORESIGHT).uid))
        assert card.cost == defn.cost - 1, defn.name
        boost(state, card, 3)
        assert card.cost == defn.cost - 4


# --- set 8 -----------------------------------------------------------------------------------

def test_meowskers_fanfare_and_evolve():
    state = start()
    enemy = put(state, 1, demo.FOOTMAN)
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    set_pp(state, 0, 2)
    meow = give(state, 0, rune.MEOWSKERS)
    apply(state, PlayCard(meow.uid, (enemy.uid,)))
    assert enemy.life == 1 and blaze.cost == 9
    unlock_evolution(state, 0)
    apply(state, Evolve(meow.uid, False, (enemy.uid,)))
    assert enemy.fate == DESTROYED and blaze.cost == 8


def test_poppy_and_mysterian_missile():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.POPPY).uid))
    missile = p.hand[-1]
    assert missile.defn == rune.MYSTERIAN_MISSILE
    set_pp(state, 0, 1)
    apply(state, PlayCard(missile.uid))
    assert enemy.fate == DESTROYED


def test_stormy_blast_both_prints():
    for defn in (rune.STORMY_BLAST, rune.STORMY_BLAST_REPRINT):
        state = start()
        a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
        blast = give(state, 0, defn)
        set_pp(state, 0, 1)
        apply(state, PlayCard(blast.uid, (a.uid,)))
        assert a.life == 3                                   # X starts at 2
        blast = give(state, 0, defn)
        set_pp(state, 0, 1)
        apply(state, PlayCard(give(state, 0, rune.FORESIGHT).uid))
        set_pp(state, 0, 1)
        apply(state, PlayCard(blast.uid, (b.uid,)))
        assert b.life == 2                                   # spellboosted once: 3


def test_sammy_and_marie_draws_for_both():
    state = start()
    me, opp = state.players
    set_pp(state, 0, 5)
    card = give(state, 0, rune.SAMMY_AND_MARIE)
    mine, theirs = len(me.hand) - 1, len(opp.hand)
    apply(state, PlayCard(card.uid))
    assert len(me.hand) == mine + 2 and len(opp.hand) == theirs + 1


def test_harmonious_meal_spellboosts_twice():
    state = start()
    p = state.players[0]
    p.leader_hp = 15
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.HARMONIOUS_MEAL).uid))
    assert p.leader_hp == 17 and blaze.cost == 8


def test_earth_shattering_bolt():
    state = start()
    p = state.players[0]
    small, big = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.EARTH_SHATTERING_BOLT).uid))
    assert big.fate == DESTROYED and small.life == 2 and state.players[1].leader_hp == 18
    assert count(p.hand, rune.EARTH_SHATTERING_BOLT) == 0
    sigils(state, 0, 2)
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.EARTH_SHATTERING_BOLT).uid))
    assert small.fate == DESTROYED and count(p.hand, rune.EARTH_SHATTERING_BOLT) == 1
    assert sigils(state) == 0


def test_tico_missiles_evolve_discount_and_crest():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 3)
    tico = give(state, 0, rune.TICO)
    apply(state, PlayCard(tico.uid))
    missiles = [c for c in p.hand if c.defn == rune.MYSTERIAN_MISSILE]
    assert len(missiles) == 2
    foresight = give(state, 0, rune.FORESIGHT)
    unlock_evolution(state, 0)
    apply(state, Evolve(tico.uid, True))
    assert [m.cost for m in missiles] == [0, 0] and foresight.cost == 1
    assert [c.defn for c in p.leader_area] == [rune.TICO_CREST]
    set_pp(state, 0, 1)
    apply(state, PlayCard(missiles[0].uid))
    assert state.players[1].leader_hp == 19                  # Mysteria spell
    apply(state, PlayCard(foresight.uid))
    assert state.players[1].leader_hp == 19                  # not Mysteria


def test_amethysts_naptime_threshold():
    for boosts, healed in ((4, False), (5, True)):
        state = start()
        p = state.players[0]
        p.leader_hp = 10
        nap = give(state, 0, rune.AMETHYSTS_NAPTIME)
        boost(state, nap, boosts)
        set_pp(state, 0, 5)
        hand = len(p.hand) - 1
        apply(state, PlayCard(nap.uid))
        assert len(p.hand) == hand + 2
        assert (p.leader_hp, p.pp) == ((12, 4) if healed else (10, 2))


def test_tetra_and_ladica_thresholds():
    for boosts, added in ((9, []), (10, [rune.DELTA_CANNON]),
                          (20, [rune.DELTA_CANNON, rune.SEND_EM_PACKING])):
        state = start()
        p = state.players[0]
        p.hand.clear()
        tetra = give(state, 0, rune.TETRA_AND_LADICA)
        boost(state, tetra, boosts)
        set_pp(state, 0, 6)
        apply(state, PlayCard(tetra.uid))
        assert [c.defn for c in p.hand] == added
        assert Attack(tetra.uid, leader_uid(1)) in legal_actions(state)    # Storm


def test_delta_cannon_and_send_em_packing():
    state = start()
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.DELTA_CANNON).uid))
    assert a.fate == DESTROYED and b.fate == DESTROYED
    raider = put(state, 0, demo.RAIDER)
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.SEND_EM_PACKING).uid, (raider.uid,)))
    for _ in range(2):
        apply(state, Attack(raider.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 16
    assert Attack(raider.uid, leader_uid(1)) not in legal_actions(state)


def test_send_em_packing_qa_keeps_three_attacks():
    """Official Q&A: on a follower that can attack 3 times per turn, it still attacks 3 times."""
    state = start()
    raider = put(state, 0, demo.RAIDER)
    E.grant(raider, ThreeAttacks())
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.SEND_EM_PACKING).uid, (raider.uid,)))
    assert raider.max_attacks == 3


def test_ginger_gives_rush_and_spellboosts():
    state = start()
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    set_pp(state, 0, 7)
    ginger = give(state, 0, rune.GINGER)
    apply(state, PlayCard(ginger.uid))
    golems = on_field(state, 0, rune.GUARDIAN_GOLEM)
    assert len(golems) == 2 and all(g.has(Keyword.RUSH) for g in golems)
    assert not ginger.has(Keyword.RUSH) and blaze.cost == 8
    footman = state.players[0].hand[0]
    set_pp(state, 0, 1)
    apply(state, PlayCard(footman.uid))
    assert footman.has(Keyword.RUSH) and blaze.cost == 7
    unlock_evolution(state, 0)
    apply(state, Evolve(ginger.uid))
    assert len(on_field(state, 0, rune.GUARDIAN_GOLEM)) == 3


# --- set 7 -----------------------------------------------------------------------------------

def test_dainty_horror_earth_rite_evolves_it():
    for n in (0, 1):
        state = start()
        if n:
            sigils(state, 0, n)
        set_pp(state, 0, 4)
        horror = give(state, 0, rune.DAINTY_HORROR)
        apply(state, PlayCard(horror.uid))
        assert horror.evolved == bool(n) and sigils(state) == 0
        assert (horror.atk, horror.life) == ((4, 8) if n else (2, 6))


def test_little_beastie_fanfare_and_evolve():
    state = start()
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 2)
    beastie = give(state, 0, rune.LITTLE_BEASTIE)
    apply(state, PlayCard(beastie.uid, (enemy.uid,)))
    assert enemy.life == 1 and sigils(state) == 1
    assert state.players[0].field[-1].defn == rune.MAGIC_SEDIMENT
    unlock_evolution(state, 0)
    apply(state, Evolve(beastie.uid, False, (enemy.uid,)))
    assert enemy.fate == DESTROYED and sigils(state) == 2


def test_heel_my_dearie_gets_cheaper_on_earth_rite():
    state = start()
    p = state.players[0]
    heel = give(state, 0, rune.HEEL_MY_DEARIE)
    gluttony = give(state, 0, rune.BOTTOMLESS_GLUTTONY)
    sigils(state, 0, 2)
    assert E.earth_rite(state, 0, 1)
    resolve_queue(state)
    assert heel.cost == 3 and gluttony.cost == 3
    set_pp(state, 0, 3)
    hand = len(p.hand) - 1
    apply(state, PlayCard(heel.uid))
    assert len(p.hand) == hand + 2 and sigils(state) == 2


def test_charming_monster_last_words_and_super_evolve():
    state = start()
    monster = put(state, 0, rune.CHARMING_MONSTER)
    kill(state, monster)
    assert sigils(state) == 2
    other = put(state, 0, rune.CHARMING_MONSTER)
    unlock_evolution(state, 0)
    apply(state, Evolve(other.uid, True))
    assert len(on_field(state, 0, rune.CHARMING_MONSTER)) == 3 and sigils(state) == 0


def test_pretty_predator():
    state = start()
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.PRETTY_PREDATOR).uid))
    assert sigils(state) == 2


def test_haphazard_snacking_modes():
    state = start()
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.HAPHAZARD_SNACKING).uid, modes=(1,)))
    assert enemy.life == 2                                   # no sigils: nothing
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.HAPHAZARD_SNACKING).uid, modes=(0,)))
    assert sigils(state) == 4
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.HAPHAZARD_SNACKING).uid, modes=(1,)))
    assert enemy.fate == DESTROYED and sigils(state) == 2


def test_sweet_abomination_earth_rite_modes():
    state = start()
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    sweet = give(state, 0, rune.SWEET_ABOMINATION)
    apply(state, PlayCard(sweet.uid, modes=(0,)))
    assert giant.life == 5                                   # no sigils: nothing
    sigils(state, 0, 2)
    unlock_evolution(state, 0)
    hand = len(p.hand)
    apply(state, Evolve(sweet.uid, False, (), (1,)))
    assert len(p.hand) == hand + 2 and sigils(state) == 1
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.SWEET_ABOMINATION).uid, modes=(0,)))
    assert giant.life == 2 and sigils(state) == 0


def test_bottomless_gluttony():
    state = start()
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.BOTTOMLESS_GLUTTONY).uid, (giant.uid,)))
    assert giant.fate == DESTROYED and sigils(state) == 2


def test_lilanthim_evolve_performs_earth_rite_without_a_target():
    # Confirmed by the player: the Earth Rite happens even with no enemy follower to select.
    state = start()
    unlock_evolution(state, 0)
    lilanthim = put(state, 0, rune.LILANTHIM)
    sigils(state, 0, 1)
    apply(state, Evolve(lilanthim.uid))
    assert sigils(state) == 0


def test_lilanthim_crest_summons_an_evolved_copy_then_expires():
    state = start(first=0)
    p = state.players[0]
    sigils(state, 0, 1)
    set_pp(state, 0, 7)
    lilanthim = give(state, 0, rune.LILANTHIM)
    apply(state, PlayCard(lilanthim.uid))
    assert [c.defn for c in p.leader_area] == [rune.LILANTHIM_CREST] and sigils(state) == 0
    apply(state, EndTurn())
    apply(state, EndTurn())                                  # end of the opponent's turn
    copies = on_field(state, 0, rune.LILANTHIM)
    assert len(copies) == 2 and copies[1].evolved and (copies[1].atk, copies[1].life) == (6, 6)
    assert p.leader_area == []                               # Countdown (1) ran out


def test_lilanthim_evolve_destroys_with_earth_rite():
    state = start()
    giant = put(state, 1, demo.GIANT)
    lilanthim = put(state, 0, rune.LILANTHIM)
    unlock_evolution(state, 0)
    apply(state, Evolve(lilanthim.uid, False, (giant.uid,)))
    assert giant.fate != DESTROYED                           # no sigils
    state = start()
    giant = put(state, 1, demo.GIANT)
    lilanthim = put(state, 0, rune.LILANTHIM)
    sigils(state, 0, 1)
    unlock_evolution(state, 0)
    apply(state, Evolve(lilanthim.uid, False, (giant.uid,)))
    assert giant.fate == DESTROYED and sigils(state) == 0


def test_beloved_masterpiece():
    state = start()
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 8)
    masterpiece = give(state, 0, rune.BELOVED_MASTERPIECE)
    apply(state, PlayCard(masterpiece.uid))
    assert giant.fate == DESTROYED
    unlock_evolution(state, 0)
    apply(state, Evolve(masterpiece.uid, True))
    assert len(on_field(state, 0, rune.BELOVED_MASTERPIECE)) == 2
    sigils(state, 0, 2)
    kill(state, on_field(state, 0, rune.BELOVED_MASTERPIECE)[1])
    assert state.players[1].leader_hp == 17 and sigils(state) == 0
    kill(state, masterpiece)
    assert state.players[1].leader_hp == 17                  # no sigils left


# --- set 6 -----------------------------------------------------------------------------------

def test_daydream_librarian():
    state = start()
    footman = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 6)
    librarian = give(state, 0, rune.DAYDREAM_LIBRARIAN)
    apply(state, PlayCard(librarian.uid))
    (mammoth,) = on_field(state, 0, rune.CARAVAN_MAMMOTH)
    unlock_evolution(state, 0)
    apply(state, Evolve(librarian.uid, True))
    assert footman.has(Keyword.RUSH) and mammoth.has(Keyword.RUSH)
    assert not librarian.has(Keyword.RUSH)


def test_advent_of_the_eld_crystals():
    state = start()
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.ADVENT_OF_THE_ELD_CRYSTALS).uid))
    assert len(on_field(state, 0, rune.CRYSTALSPAWN)) == 2


def test_enraptured_student_heals_per_crystalspawn():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.ENRAPTURED_STUDENT).uid))
    assert len(on_field(state, 0, rune.CRYSTALSPAWN)) == 2 and p.leader_hp == 12
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert p.leader_hp == 12


def test_adventurous_grimoire():
    state = start()
    set_pp(state, 0, 3)
    grimoire = give(state, 0, rune.ADVENTUROUS_GRIMOIRE)
    apply(state, PlayCard(grimoire.uid))
    assert len(on_field(state, 0, rune.ADVENTUROUS_GRIMOIRE)) == 1
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    kill(state, grimoire)
    assert blaze.cost == 9                                   # Last Words
    set_pp(state, 0, 6)
    apply(state, PlayCard(give(state, 0, rune.ADVENTUROUS_GRIMOIRE).uid))
    assert len(on_field(state, 0, rune.ADVENTUROUS_GRIMOIRE)) == 3


def test_reaved_order_needs_a_crystalspawn():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 1)
    order = give(state, 0, rune.REAVED_ORDER)
    put(state, 0, demo.FOOTMAN)
    assert plays(state, order.uid) == []
    spawn = put(state, 0, rune.CRYSTALSPAWN)
    assert plays(state, order.uid) == [PlayCard(order.uid, (spawn.uid,))]
    hand = len(p.hand) - 1
    apply(state, PlayCard(order.uid, (spawn.uid,)))
    assert spawn.fate == DESTROYED and len(p.hand) == hand + 2


def test_spellbound_professor():
    state = start()
    set_pp(state, 0, 4)
    professor = give(state, 0, rune.SPELLBOUND_PROFESSOR)
    apply(state, PlayCard(professor.uid))
    spawns = on_field(state, 0, rune.CRYSTALSPAWN)
    assert len(spawns) == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(professor.uid))
    assert [s.atk for s in spawns] == [2, 2]


def test_bewitching_eld_crystals_modes_and_enhance():
    state = start()
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.BEWITCHING_ELD_CRYSTALS).uid, modes=(0,)))
    (spawn,) = on_field(state, 0, rune.CRYSTALSPAWN)
    assert (spawn.atk, spawn.life) == (2, 1) and spawn.has(Keyword.STORM)

    state = start()
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.BEWITCHING_ELD_CRYSTALS).uid, modes=(1,)))
    spawns = on_field(state, 0, rune.CRYSTALSPAWN)
    assert [(s.atk, s.has(Keyword.STORM)) for s in spawns] == [(2, False), (2, False)]

    state = start()
    set_pp(state, 0, 6)
    card = give(state, 0, rune.BEWITCHING_ELD_CRYSTALS)
    assert {a.modes for a in plays(state, card.uid)} == {(0, 1)}
    apply(state, PlayCard(card.uid, modes=(0, 1)))
    assert len(on_field(state, 0, rune.CRYSTALSPAWN)) == 3


def test_shymm_and_its_crest():
    state = start()
    set_pp(state, 0, 3)
    shymm = give(state, 0, rune.SHYMM)
    apply(state, PlayCard(shymm.uid))
    spawn = on_field(state, 0, rune.CRYSTALSPAWN)[0]
    unlock_evolution(state, 0)
    apply(state, Evolve(shymm.uid, True))
    assert [c.defn for c in state.players[0].leader_area] == [rune.SHYMM_CREST]
    enemy = put(state, 1, demo.FOOTMAN)                      # 1/2
    apply(state, Attack(spawn.uid, enemy.uid))               # Rush; +1/+0 as it attacks
    assert enemy.fate == DESTROYED and spawn.fate == DESTROYED


def test_calge_danthla_in_hand_discount_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    calge = give(state, 0, rune.CALGE_DANTHLA)
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.ADVENT_OF_THE_ELD_CRYSTALS).uid))
    assert calge.cost == 8
    for spawn in on_field(state, 0, rune.CRYSTALSPAWN):
        kill(state, spawn)
    set_pp(state, 0, 8)
    apply(state, PlayCard(calge.uid))
    spawns = on_field(state, 0, rune.CRYSTALSPAWN)
    assert len(spawns) == 2 and all(s.has(Keyword.STORM) for s in spawns)
    assert calge.cost == 8                                   # only while in hand
    unlock_evolution(state, 0)
    apply(state, Evolve(calge.uid))
    assert p.hand[-1].defn == rune.DEPTHS_OF_THE_ELD_CRYSTALS


def test_eld_crystals_faith_starts_in_the_leader_area_and_counts_crystalspawns():
    deck = [rune.CALGE_DANTHLA] * 3 + [demo.FOOTMAN] * 37
    state = new_game(deck, [demo.FOOTMAN] * 40, seed=0, first=0)
    p = state.players[0]
    assert [c.defn for c in p.leader_area] == [rune.ELD_CRYSTALS_FAITH]
    assert E.faith_value(state, 0, rune.ELD_CRYSTALS_FAITH) == 0
    for _ in range(3):
        put(state, 0, rune.CRYSTALSPAWN)
    put(state, 0, demo.FOOTMAN)
    put(state, 1, rune.CRYSTALSPAWN)
    resolve_queue(state)
    assert E.faith_value(state, 0, rune.ELD_CRYSTALS_FAITH) == 3


def test_depths_of_the_eld_crystals_splits_the_faith_value():
    state = start()
    p, opp = state.players
    E.add_to_leader_area(state, 0, rune.ELD_CRYSTALS_FAITH)
    E.change_faith(state, 0, rune.ELD_CRYSTALS_FAITH, 5)
    p.leader_hp = 10
    set_pp(state, 0, 6)
    apply(state, PlayCard(give(state, 0, rune.DEPTHS_OF_THE_ELD_CRYSTALS).uid))
    (spawn,) = on_field(state, 0, rune.CRYSTALSPAWN)
    x, y, z = spawn.atk - 1, p.leader_hp - 10, 20 - opp.leader_hp
    assert spawn.life == 1 + x and x + y + z == 5
    assert E.faith_value(state, 0, rune.ELD_CRYSTALS_FAITH) == 6     # the new Crystalspawn


def test_depths_of_the_eld_crystals_qa_distribution():
    """Official Q&A: with value 3, X=Y=Z=1 (6/27) is likelier than X=3 (1/27)."""
    base = start()
    E.add_to_leader_area(base, 0, rune.ELD_CRYSTALS_FAITH)
    E.change_faith(base, 0, rune.ELD_CRYSTALS_FAITH, 3)
    base.players[0].leader_hp = 10
    set_pp(base, 0, 6)
    depths = give(base, 0, rune.DEPTHS_OF_THE_ELD_CRYSTALS)
    outcomes = {}
    for seed in range(540):
        state = base.clone()
        state.rng.seed(seed)
        apply(state, PlayCard(depths.uid))
        spawn = on_field(state, 0, rune.CRYSTALSPAWN)[0]
        key = (spawn.atk - 1, state.players[0].leader_hp - 10, 20 - state.players[1].leader_hp)
        assert sum(key) == 3
        outcomes[key] = outcomes.get(key, 0) + 1
    assert len(outcomes) == 10
    assert outcomes[(1, 1, 1)] > 3 * outcomes[(3, 0, 0)]


# --- set 5 -----------------------------------------------------------------------------------

def test_terraforming_wizard():
    state = start()
    set_pp(state, 0, 3)
    wizard = give(state, 0, rune.TERRAFORMING_WIZARD)
    apply(state, PlayCard(wizard.uid))
    assert sigils(state) == 2
    unlock_evolution(state, 0)
    apply(state, Evolve(wizard.uid, True))
    assert len(on_field(state, 0, rune.GUARDIAN_GOLEM)) == 2


def test_waterbending_charmwielder():
    state = start()
    giants = [put(state, 1, demo.GIANT) for _ in range(4)]
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    set_pp(state, 0, 6)
    apply(state, PlayCard(give(state, 0, rune.WATERBENDING_CHARMWIELDER).uid))
    assert sorted(g.life for g in giants) == [2, 2, 2, 5]
    assert blaze.cost == 7


def test_metamorphosis_of_the_dawnblossom():
    state = start()
    p = state.players[0]
    p.hand.clear()
    card = give(state, 0, rune.METAMORPHOSIS_OF_THE_DAWNBLOSSOM)
    set_pp(state, 0, 2)
    assert plays(state, card.uid) == []                      # needs a card to discard
    other = give(state, 0, demo.FOOTMAN)
    apply(state, PlayCard(card.uid, (other.uid,)))
    assert len(p.hand) == 2 and other not in p.hand and p.shadows == 2


def test_insomniac_witch_evolve_destroys_the_crest():
    state = start()
    p = state.players[0]
    giant, footman = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 4)
    witch = give(state, 0, rune.INSOMNIAC_WITCH)
    apply(state, PlayCard(witch.uid))
    assert [c.defn for c in p.leader_area] == [rune.INSOMNIAC_WITCH_CREST]
    unlock_evolution(state, 0)
    apply(state, Evolve(witch.uid))
    assert p.leader_area == [] and footman.fate == DESTROYED
    assert giant.life == 2 and (witch.atk, witch.life) == (5, 2)


def test_insomniac_witch_crest_counts_down():
    state = start(first=0)
    p = state.players[0]
    E.add_to_leader_area(state, 0, rune.INSOMNIAC_WITCH_CREST)
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.GIANT)
    for _ in range(2):
        apply(state, EndTurn())
        apply(state, EndTurn())
    assert p.leader_area == [] and mine.life == 2 and theirs.life == 2


def test_woodsong_haikumaster():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 6)
    haiku = give(state, 0, rune.WOODSONG_HAIKUMASTER)
    hand = len(p.hand) - 1
    apply(state, PlayCard(haiku.uid))
    assert len(p.hand) == hand + 1
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    kill(state, haiku)
    assert blaze.cost == 9


def test_kitty_cunning():
    state = start()
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.KITTY_CUNNING).uid))
    assert state.players[0].field == []                      # no sigils: nothing
    seen = set()
    for seed in range(12):
        state = start(seed=seed)
        p = state.players[0]
        p.leader_hp = 10
        sigils(state, 0, 2)
        set_pp(state, 0, 1)
        apply(state, PlayCard(give(state, 0, rune.KITTY_CUNNING).uid))
        done = (bool(on_field(state, 0, rune.CLAY_GOLEM)), p.leader_hp == 12, sigils(state) == 3)
        assert sum(done) == 2
        seen.add(done)
    assert len(seen) == 3


def test_emperor_of_elements_evolves_golems_with_earth_rite():
    state = start()
    p = state.players[0]
    sigils(state, 0, 3)
    set_pp(state, 0, 7)
    apply(state, PlayCard(give(state, 0, rune.EMPEROR_OF_ELEMENTS).uid))
    golems = on_field(state, 0, rune.GUARDIAN_GOLEM)
    assert len(golems) == 2 and all(g.evolved for g in golems) and sigils(state) == 1
    set_pp(state, 0, 2)
    apply(state, PlayCard(give(state, 0, rune.TRUTH_SUMMONS).uid))
    assert on_field(state, 0, rune.CLAY_GOLEM)[0].evolved and sigils(state) == 0
    assert len(p.field) == 4                                 # the sigil amulet is gone

    state = start()
    set_pp(state, 0, 7)
    apply(state, PlayCard(give(state, 0, rune.EMPEROR_OF_ELEMENTS).uid))
    assert not any(g.evolved for g in on_field(state, 0, rune.GUARDIAN_GOLEM))


def test_grandeur_of_the_dawnblossom_qa_independent_choices():
    """Official Q&A: each follower picks its own random deck follower (repeats allowed)."""
    results = set()
    for seed in range(30):
        state = start(seed=seed)
        p = state.players[0]
        p.deck = [state.new_instance(demo.GIANT, 0), state.new_instance(demo.LANCER, 0),
                  state.new_instance(rune.FORESIGHT, 0)]
        E.buff(state, p.deck[0], 1, 1)                      # copies are exact
        a, b = put(state, 0, rune.CLAY_GOLEM), put(state, 0, rune.CLAY_GOLEM)
        set_pp(state, 0, 7)
        apply(state, PlayCard(give(state, 0, rune.GRANDEUR_OF_THE_DAWNBLOSSOM).uid))
        assert p.field == [a, b] and len(p.deck) == 3
        for f in (a, b):
            assert (f.defn, f.atk, f.life) in ((demo.GIANT, 6, 6), (demo.LANCER, 3, 2))
            assert not any(isinstance(x, Attack) and x.attacker == f.uid
                           for x in legal_actions(state))
        results.add((a.defn.card_id, b.defn.card_id))
    assert len(results) == 4


def test_lhynkal_crest_and_super_evolve():
    state = start()
    p, opp = state.players
    set_pp(state, 0, 1)
    first = give(state, 0, rune.LHYNKAL)
    apply(state, PlayCard(first.uid))
    assert [c.defn for c in p.leader_area] == [rune.LHYNKAL_CREST]
    assert opp.leader_max_hp == 20                           # the crest came after it entered
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, rune.LHYNKAL).uid))
    assert (opp.leader_max_hp, opp.leader_hp) == (18, 18)
    deck = len(p.deck)
    unlock_evolution(state, 0)
    apply(state, Evolve(first.uid, True))
    assert len(p.deck) == deck + 10 and count(p.deck, rune.LHYNKAL) == 10


def test_ara_fanfare_and_evolve_transform():
    state = start()
    giant = put(state, 1, demo.GIANT)
    mine = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 10)
    ara = give(state, 0, rune.ARA)
    apply(state, PlayCard(ara.uid, (giant.uid,)))
    assert giant.fate == DESTROYED
    enemy = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    targets = {a.targets for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == ara.uid}
    assert targets == {(mine.uid,), (enemy.uid,)}
    apply(state, Evolve(ara.uid, False, (enemy.uid,)))
    assert enemy.defn == rune.REGAL_FALCON and (enemy.atk, enemy.life) == (4, 4)


# --- set 4 -----------------------------------------------------------------------------------

def test_philosophia_draws_a_spell():
    state = start()
    p = state.players[0]
    p.deck.insert(0, state.new_instance(rune.FORESIGHT, 0))
    set_pp(state, 0, 3)
    apply(state, PlayCard(give(state, 0, rune.PHILOSOPHIA).uid))
    assert p.hand[-1].defn == rune.FORESIGHT and count(p.deck, rune.FORESIGHT) == 0


def test_suframare_end_of_turn_spellboost_and_evolve():
    state = start(first=0)
    sufra = put(state, 0, rune.SUFRAMARE)
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    apply(state, EndTurn())
    assert blaze.cost == 9
    apply(state, EndTurn())
    unlock_evolution(state, 0)
    apply(state, Evolve(sufra.uid))
    assert not any(isinstance(a, Attack) and a.attacker == sufra.uid for a in legal_actions(state))
    apply(state, EndTurn())
    assert blaze.cost == 6                                   # attack 3 now


def test_rune_portal():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    giant, mine = put(state, 1, demo.GIANT), put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 7)
    apply(state, PlayCard(give(state, 0, rune.RUNE_PORTAL).uid))
    assert giant.fate == DESTROYED and mine.life == 2 and p.leader_hp == 13


def test_ezecrain():
    state = start()
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    set_pp(state, 0, 6)
    apply(state, PlayCard(give(state, 0, rune.EZECRAIN).uid, (a.uid, b.uid)))
    assert (a.life, b.life) == (1, 1) and sigils(state) == 2


def test_mireille_and_risette_qa_skybound_gauge_rises_by_two():
    """Official Q&A: the Earth Rite evolves two followers: Skybound Art gauges +2."""
    state = start()
    flare = give(state, 0, rune.ALCHEMIC_FLARE)
    sigils(state, 0, 2)
    set_pp(state, 0, 5)
    duo = give(state, 0, rune.MIREILLE_AND_RISETTE)
    gauge = E.skybound_gauge(state, flare)
    apply(state, PlayCard(duo.uid))
    twins = on_field(state, 0, rune.MIREILLE_AND_RISETTE)
    assert len(twins) == 2 and all(t.evolved for t in twins) and sigils(state) == 0
    assert E.skybound_gauge(state, flare) == gauge + 2

    state = start()
    set_pp(state, 0, 5)
    apply(state, PlayCard(give(state, 0, rune.MIREILLE_AND_RISETTE).uid))
    twins = on_field(state, 0, rune.MIREILLE_AND_RISETTE)
    assert len(twins) == 2 and not any(t.evolved for t in twins)


def test_unleashed_modes():
    state = start()
    p = state.players[0]
    giants = [put(state, 1, demo.GIANT) for _ in range(3)]
    set_pp(state, 0, 4)
    hand = len(p.hand)
    apply(state, PlayCard(give(state, 0, rune.UNLEASHED).uid, modes=(0,)))
    assert len(p.hand) == hand + 1 and sorted(g.life for g in giants) == [1, 5, 5]
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.UNLEASHED).uid, modes=(1,)))
    assert len(p.hand) == hand + 3 and p.leader_hp == 18
    assert sum(5 - g.life for g in giants) == 4 + 2 * 4             # two different giants hit


def test_elmott_removes_printed_last_words():
    state = start(first=0)
    bomber = put(state, 1, demo.BOMBER)                     # Last Words: 2 damage to my leader
    E.buff(state, bomber, 0, 3)
    set_pp(state, 0, 3)
    apply(state, PlayCard(give(state, 0, rune.ELMOTT).uid, (bomber.uid,)))
    E.destroy(state, bomber)
    resolve_queue(state)
    assert bomber.fate == DESTROYED and state.players[0].leader_hp == 20


def test_obsessed_test_subject_counts_however_it_enters():
    state = start()
    state.players[0].entered[OTS.card_id] = 5
    ots = E.summon(state, 0, OTS)                           # any summon, not just Rune's
    resolve_queue(state)
    assert (ots.atk, ots.life) == (5, 5) and rune.entered_test_subjects(state, 0) == 6


def test_elmott_removes_abilities_and_crest():
    state = start(first=0)
    giant = put(state, 1, demo.GIANT)
    E.give_keywords(giant, Keyword.WARD | Keyword.DRAIN)
    E.grant(giant, ThreeAttacks())
    E.buff(state, giant, 1, 1)
    set_pp(state, 0, 3)
    elmott = give(state, 0, rune.ELMOTT)
    apply(state, PlayCard(elmott.uid, (giant.uid,)))
    assert giant.keywords == Keyword.NONE and giant.max_attacks == 1
    assert (giant.atk, giant.life) == (6, 3)                 # buffs stay
    unlock_evolution(state, 0)
    apply(state, Evolve(elmott.uid, True))
    assert [c.defn for c in state.players[0].leader_area] == [rune.ELMOTT_CREST]
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert state.players[1].leader_hp == 19


def test_alchemic_flare_skybound_art():
    for turns, leader in ((9, 20), (10, 18)):
        state = start()
        p = state.players[0]
        giant = put(state, 1, demo.GIANT)
        p.turns_taken = turns
        set_pp(state, 0, 2)
        apply(state, PlayCard(give(state, 0, rune.ALCHEMIC_FLARE).uid, (giant.uid,)))
        assert giant.life == 1 and sigils(state) == 1 and state.players[1].leader_hp == leader


def test_wamdus_grows_on_spellboost_and_super_evolve_modes():
    state = start()
    wamdus = give(state, 0, rune.WAMDUS)
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    boost(state, wamdus, 2)
    assert (wamdus.atk, wamdus.life) == (2, 3)
    set_pp(state, 0, 3)
    apply(state, PlayCard(wamdus.uid))
    assert blaze.cost == 9 and (wamdus.atk, wamdus.life) == (2, 3)
    ally = put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(wamdus.uid, True, (), (0,)))
    assert ally.has(Keyword.BARRIER) and not wamdus.has(Keyword.BARRIER)

    state = start()
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    wamdus = put(state, 0, rune.WAMDUS)
    E.buff(state, wamdus, 2, 0)                              # 2/1, 5/4 after super-evolving
    unlock_evolution(state, 0)
    apply(state, Evolve(wamdus.uid, True, (), (1,)))
    assert a.fate == DESTROYED and b.life == 2               # 5 split: 2 then 3


def test_cagliostro_skybound_arts_and_crest():
    for turns, evolved, crest in ((9, False, False), (10, True, False), (15, True, True)):
        state = start()
        p = state.players[0]
        p.turns_taken = turns
        set_pp(state, 0, 4)
        cag = give(state, 0, rune.CAGLIOSTRO)
        apply(state, PlayCard(cag.uid))
        assert sigils(state) == 2 and p.hand[-1].defn == rune.ARS_MAGNA
        assert cag.evolved == evolved and bool(p.leader_area) == crest

    state = start(first=0)
    p = state.players[0]
    E.add_to_leader_area(state, 0, rune.CAGLIOSTRO_CREST)
    sigils(state, 0, 1)
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert count(p.hand, rune.ARS_MAGNA) == 1 and sigils(state) == 0
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert count(p.hand, rune.ARS_MAGNA) == 1                # no sigils left


def test_ars_magna():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    set_pp(state, 0, 1)
    magna = give(state, 0, rune.ARS_MAGNA)
    assert PlayCard(magna.uid, (leader_uid(1),)) in plays(state, magna.uid)
    apply(state, PlayCard(magna.uid, (leader_uid(1),)))
    assert state.players[1].leader_hp == 18 and p.leader_hp == 11


# --- Basic -----------------------------------------------------------------------------------

def test_dazzling_runeknight_modes_and_qa():
    state = start()
    blaze = give(state, 0, rune.BLAZE_DESTROYER)
    set_pp(state, 0, 3)
    apply(state, PlayCard(give(state, 0, rune.DAZZLING_RUNEKNIGHT).uid, modes=(0,)))
    assert blaze.cost == 8

    # Official Q&A: mode 2 can be chosen without earth sigils; nothing happens.
    state = start()
    set_pp(state, 0, 3)
    knight = give(state, 0, rune.DAZZLING_RUNEKNIGHT)
    assert PlayCard(knight.uid, (), (1,)) in plays(state, knight.uid)
    apply(state, PlayCard(knight.uid, modes=(1,)))
    assert (knight.atk, knight.life) == (2, 2) and not knight.has(Keyword.WARD)

    sigils(state, 0, 1)
    set_pp(state, 0, 3)
    knight = give(state, 0, rune.DAZZLING_RUNEKNIGHT)
    apply(state, PlayCard(knight.uid, modes=(1,)))
    assert (knight.atk, knight.life) == (4, 4) and knight.has(Keyword.WARD) and sigils(state) == 0


def test_witchs_new_brew_qa_engage_again_after_merging():
    """Official Q&A: engage one Brew, play another (they merge): the new one can engage."""
    state = start()
    p = state.players[0]
    set_pp(state, 0, 4)
    brew = give(state, 0, rune.WITCHS_NEW_BREW)
    hand = len(p.hand) - 1
    apply(state, PlayCard(brew.uid))
    assert len(p.hand) == hand + 1 and sigils(state) == 1
    apply(state, Engage(brew.uid))
    assert sigils(state) == 2 and p.pp == 2
    assert Engage(brew.uid) not in legal_actions(state)
    second = give(state, 0, rune.WITCHS_NEW_BREW)
    apply(state, PlayCard(second.uid))
    assert p.field == [second] and sigils(state) == 3
    assert Engage(second.uid) in legal_actions(state)
    apply(state, Engage(second.uid))
    assert sigils(state) == 4 and p.pp == 0


def test_magic_sediment_engage():
    state = start()
    p = state.players[0]
    sigils(state, 0, 1)
    sediment = p.field[0]
    set_pp(state, 0, 1)
    apply(state, Engage(sediment.uid))
    assert sigils(state) == 2 and p.pp == 0
    set_pp(state, 0, 1)
    assert Engage(sediment.uid) not in legal_actions(state)  # once per turn


def test_foresight_draws():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 1)
    card = give(state, 0, rune.FORESIGHT)
    hand = len(p.hand) - 1
    apply(state, PlayCard(card.uid))
    assert len(p.hand) == hand + 1


def test_remi_and_rami():
    state = start()
    set_pp(state, 0, 4)
    remi = give(state, 0, rune.REMI_AND_RAMI)
    apply(state, PlayCard(remi.uid))
    assert on_field(state, 0, rune.GUARDIAN_GOLEM) == []     # no sigils
    sigils(state, 0, 1)
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.REMI_AND_RAMI).uid))
    (golem,) = on_field(state, 0, rune.GUARDIAN_GOLEM)
    put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    options = {(a.super_, a.targets) for a in legal_actions(state)
               if isinstance(a, Evolve) and a.uid == remi.uid}
    assert options == {(False, ()), (True, (golem.uid,))}      # only the Super-Evolve selects
    apply(state, Evolve(remi.uid, True, (golem.uid,)))
    assert golem.evolved and (golem.atk, golem.life) == (8, 8)


def test_arcane_eruption():
    state = start()
    p = state.players[0]
    mine, theirs = put(state, 0, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 4)
    hand = len(p.hand)
    apply(state, PlayCard(give(state, 0, rune.ARCANE_ERUPTION).uid))
    assert mine.life == 3 and theirs.fate == DESTROYED and len(p.hand) == hand
    sigils(state, 0, 1)
    set_pp(state, 0, 4)
    apply(state, PlayCard(give(state, 0, rune.ARCANE_ERUPTION).uid))
    assert mine.life == 1 and len(p.hand) == hand + 1 and sigils(state) == 0


# --- random games ------------------------------------------------------------------------------

def random_rune_deck(rng):
    """A random legal Rotation Runecraft deck (up to 3 copies), using only cards that
    are scripted or need no script."""
    options = [c for c in collectible(Craft.RUNE) if has_script(c.card_id) or not needs_script(c)]
    deck = []
    while len(deck) < 40:
        c = rng.choice(options)
        if deck.count(c) < 3:
            deck.append(c)
    return deck


def test_random_rune_games():
    rng = random.Random(0)
    for g in range(100):
        d0, d1 = random_rune_deck(rng), random_rune_deck(rng)
        state = new_game(d0, d1, seed=g)
        agents = [RandomAgent(2 * g, end_turn_weight=0.2), RandomAgent(2 * g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
        assert state.over
