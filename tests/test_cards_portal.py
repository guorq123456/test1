"""Portalcraft cards, tokens, crests and Accelerate forms."""
import random

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import demo, portal
from svsim.cards import portal as P
from svsim.cards.pool import collectible
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, Fuse, PlayCard
from svsim.core.engine import apply, legal_actions, new_game, play_form, resolve_queue
from svsim.core.enums import Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, pass_turns, plays, put, set_pp, start, unlock_evolution


def hand_only(state, player, *defns):
    """Empty a player's hand, then give them these cards."""
    state.players[player].hand.clear()
    return [give(state, player, d) for d in defns]


def play(state, inst, targets=(), modes=()):
    apply(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def deck_of(state, player, defns):
    state.players[player].deck = [state.new_instance(d, player) for d in defns]


def highlander(state, player=0, extra=()):
    """A deck with no duplicates (the demo cards, plus `extra`)."""
    deck_of(state, player, list(demo.ALL) + list(extra))


def artifacts_destroyed(state, player, *defns):
    state.players[player].destroyed += list(defns)


THREE_ARTIFACTS = (P.ANCIENT_ARTIFACT, P.MYSTIC_ARTIFACT, P.RADIANT_ARTIFACT)


# --- tokens -------------------------------------------------------------------------------

def test_puppets_are_destroyed_at_the_end_of_the_opponents_turn():
    state = start(first=0)
    puppet, enhanced = put(state, 0, P.PUPPET), put(state, 0, P.ENHANCED_PUPPET)
    apply(state, EndTurn())
    assert puppet.fate == IN_PLAY and enhanced.fate == IN_PLAY
    apply(state, EndTurn())
    assert puppet.fate == DESTROYED and enhanced.fate == DESTROYED


def test_analyzing_artifact_draws_when_played_and_when_summoned():
    state = start()
    p = state.players[0]
    artifact, = hand_only(state, 0, P.ANALYZING_ARTIFACT)
    set_pp(state, 0, 1)
    play(state, artifact)
    assert p.field == [artifact] and len(p.hand) == 1
    portal.summon(state, 0, P.ANALYZING_ARTIFACT)
    resolve_queue(state)
    assert len(p.hand) == 2


def test_gears_cant_be_played_and_fuse_into_striker_or_fortifier():
    state = start()
    p = state.players[0]
    ambition, remembrance = hand_only(state, 0, P.GEAR_OF_AMBITION, P.GEAR_OF_REMEMBRANCE)
    set_pp(state, 0, 5)
    assert plays(state, ambition.uid) == [] and plays(state, remembrance.uid) == []
    assert Fuse(ambition.uid, (remembrance.uid,)) in legal_actions(state)
    apply(state, Fuse(ambition.uid, (remembrance.uid,)))
    assert p.hand == [ambition] and ambition.defn == P.STRIKER_ARTIFACT and p.shadows == 0
    ambition, remembrance = hand_only(state, 0, P.GEAR_OF_AMBITION, P.GEAR_OF_REMEMBRANCE)
    apply(state, Fuse(remembrance.uid, (ambition.uid,)))
    assert remembrance.defn == P.FORTIFIER_ARTIFACT


def test_striker_and_fortifier_transform_by_total_cost_fused():
    cases = [((P.GEAR_OF_AMBITION,), P.OMINOUS_ARTIFACT_ALPHA),
             ((P.GEAR_OF_AMBITION, P.GEAR_OF_REMEMBRANCE), P.OMINOUS_ARTIFACT_BETA),
             ((P.MYSTIC_ARTIFACT,), P.OMINOUS_ARTIFACT_GAMMA),
             ((P.OMINOUS_ARTIFACT_ALPHA,), P.OMINOUS_ARTIFACT_GAMMA)]
    for base in (P.STRIKER_ARTIFACT, P.FORTIFIER_ARTIFACT):
        for fodder, result in cases:
            state = start()
            target, *rest = hand_only(state, 0, base, *fodder)
            give(state, 0, demo.FOOTMAN)                  # not an Artifact: can't be fused
            action = Fuse(target.uid, tuple(c.uid for c in rest))
            assert action in legal_actions(state)
            apply(state, action)
            assert target.defn == result


def test_ominous_alpha_fuses_beta_and_gamma_over_two_turns():
    """Official Q&A: fusing β one turn and γ the next still makes Ω."""
    state = start(first=0)
    alpha, beta, gamma = hand_only(state, 0, P.OMINOUS_ARTIFACT_ALPHA, P.OMINOUS_ARTIFACT_BETA,
                                   P.OMINOUS_ARTIFACT_GAMMA)
    apply(state, Fuse(alpha.uid, (beta.uid,)))
    assert alpha.defn == P.OMINOUS_ARTIFACT_ALPHA
    assert not any(isinstance(a, Fuse) and a.uid == alpha.uid for a in legal_actions(state))
    pass_turns(state, 2)
    apply(state, Fuse(alpha.uid, (gamma.uid,)))
    assert alpha.defn == P.MASTERWORK_ARTIFACT_OMEGA and (alpha.atk, alpha.life) == (10, 10)


def test_ominous_artifacts_end_of_turn_abilities():
    state = start(first=0)
    p, opp = state.players
    p.leader_hp = 10
    put(state, 0, P.OMINOUS_ARTIFACT_ALPHA)
    put(state, 0, P.OMINOUS_ARTIFACT_BETA)
    put(state, 0, P.OMINOUS_ARTIFACT_GAMMA)
    giant = put(state, 1, demo.GIANT)
    apply(state, EndTurn())
    assert p.leader_hp == 13 and opp.leader_hp == 17 and giant.life == 2


def test_two_ominous_gammas_resolve_before_last_words():
    """Official Q&A (Rotting Zombie): both γ abilities resolve before the Last Words
    of the follower the first one destroyed, so its summon survives."""
    state = start(first=0)
    put(state, 0, P.OMINOUS_ARTIFACT_GAMMA)
    put(state, 0, P.OMINOUS_ARTIFACT_GAMMA)
    kratos = put(state, 1, P.KRATOS)
    E.damage(state, [kratos], 4)
    apply(state, EndTurn())
    assert kratos.fate == DESTROYED
    second, = state.players[1].field
    assert second.defn == P.KRATOS and second.life == 7


def test_masterwork_artifact_omega_fanfare():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    giant = put(state, 1, demo.GIANT)
    omega, = hand_only(state, 0, P.MASTERWORK_ARTIFACT_OMEGA)
    set_pp(state, 0, 10)
    play(state, omega)
    assert giant.fate == DESTROYED and p.leader_hp == 15
    assert omega.has(Keyword.STORM | Keyword.WARD | Keyword.AURA)


def test_warden_of_the_trigger_last_words():
    state = start()
    state.players[0].leader_hp = 10
    warden = put(state, 0, P.WARDEN_OF_THE_TRIGGER)
    E.destroy(state, warden)
    resolve_queue(state)
    assert state.players[0].leader_hp == 12


def test_depths_of_the_eld_axe_and_substandard_puppet_qa():
    """Official Q&A: a Substandard Puppet reduced to 2 by Depths of the Eld Axe is
    played normally, not Accelerated."""
    state = start()
    p = state.players[0]
    put(state, 0, demo.FOOTMAN)
    depths, = hand_only(state, 0, P.DEPTHS_OF_THE_ELD_AXE)
    set_pp(state, 0, 3)
    assert plays(state, depths.uid) == []                 # nothing with base cost 5 or more
    puppet = put(state, 0, P.SUBSTANDARD_PUPPET)
    E.buff(state, puppet, 2, 2)
    play(state, depths, (puppet.uid,))
    copy = p.hand[-1]
    assert copy.defn == P.SUBSTANDARD_PUPPET and copy.cost == 2 and copy.atk == 2   # not an exact copy
    assert play_form(p, copy).alt is None
    play(state, copy)
    assert p.pp == 1 and copy in p.field and copy.evolved
    assert count(p.field, P.SUBSTANDARD_PUPPET) == 3


# --- leader area / alternate forms ---------------------------------------------------------

def test_cutthroat_evolve_draws_bane_and_gains_crest_with_no_duplicates():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    highlander(state, extra=[P.CUTTHROAT])
    cutthroat = put(state, 0, P.CUTTHROAT)
    apply(state, Evolve(cutthroat.uid))
    assert p.hand[-1].defn == P.CUTTHROAT
    assert [c.defn for c in p.leader_area] == [P.CUTTHROAT_CREST]

    state = start()
    unlock_evolution(state, 0)
    cutthroat = put(state, 0, P.CUTTHROAT)
    apply(state, Evolve(cutthroat.uid))
    assert state.players[0].leader_area == []


def test_cutthroat_crest_evolves_the_first_follower_played_each_turn():
    state = start(first=0)
    p = state.players[0]
    E.add_to_leader_area(state, 0, P.CUTTHROAT_CREST)
    light, a, b = hand_only(state, 0, P.LIGHT_OF_THE_DEWDROP, demo.FOOTMAN, demo.FOOTMAN)
    set_pp(state, 0, 5)
    play(state, light)                                    # a spell doesn't use it up
    play(state, a)
    play(state, b)
    assert a.evolved and not b.evolved
    pass_turns(state, 2)
    c = give(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, c)
    assert c.evolved and p.ep == 2                        # no evolution points spent


def test_lu_woh_crest_weakens_storm_followers_attacking_a_leader():
    state = start(first=0)
    E.add_to_leader_area(state, 0, P.LU_WOH_CREST)
    apply(state, EndTurn())
    raider = put(state, 1, demo.RAIDER)                   # 2/1 Storm
    big = put(state, 1, demo.RAIDER)
    E.buff(state, big, 3, 0)                              # 5/1 Storm
    lancer = put(state, 1, demo.LANCER)                   # Rush, no Storm
    apply(state, Attack(raider.uid, leader_uid(0)))
    apply(state, Attack(big.uid, leader_uid(0)))
    apply(state, Attack(lancer.uid, leader_uid(0)))
    assert state.players[0].leader_hp == 20 - 0 - 2 - 3
    apply(state, EndTurn())
    assert (raider.atk, big.atk) == (2, 5)                # restored, never above the original


def test_slaus_crest_activates_each_bad_ability_once():
    state = start(first=0)
    opp = state.players[1]
    crest = E.add_to_leader_area(state, 1, P.SLAUS_CREST)
    giant = put(state, 1, demo.GIANT)
    for _ in range(3):
        apply(state, EndTurn())                           # opponent's turn starts
        last = crest.counters["wheel"][-1]
        if last == 0:
            assert sum(c.cost == 2 for c in opp.hand) == len(opp.hand) - 1   # all but the new draw
        apply(state, EndTurn())
    assert sorted(crest.counters["wheel"]) == [0, 1, 2]
    assert crest.fate == DESTROYED and opp.leader_area == []
    assert opp.leader_hp == 17 and (giant.atk, giant.life) == (3, 3)


def test_shoddy_plaything_fanfare_and_accelerate():
    state = start()
    p = state.players[0]
    toy, = hand_only(state, 0, P.SHODDY_PLAYTHING)
    set_pp(state, 0, 6)
    play(state, toy)
    assert len(p.hand) == 3
    toy, = hand_only(state, 0, P.SHODDY_PLAYTHING)
    set_pp(state, 0, 2)
    play(state, toy)
    assert len(p.hand) == 0 and count(p.field, P.SHODDY_PLAYTHING) == 2   # summoned: no Fanfare
    assert toy not in p.field and p.pp == 0


def test_substandard_puppet_fanfare_and_accelerate():
    state = start()
    p = state.players[0]
    puppet, = hand_only(state, 0, P.SUBSTANDARD_PUPPET)
    set_pp(state, 0, 5)
    play(state, puppet)
    assert count(p.followers, P.SUBSTANDARD_PUPPET) == 2 and all(f.evolved for f in p.followers)
    state = start()
    p = state.players[0]
    puppet, = hand_only(state, 0, P.SUBSTANDARD_PUPPET)
    set_pp(state, 0, 3)
    play(state, puppet)
    assert count(p.followers, P.SUBSTANDARD_PUPPET) == 2 and not any(f.evolved for f in p.followers)


def test_ludicrous_ordnance_fanfare_and_accelerate():
    state = start()
    p = state.players[0]
    gun, = hand_only(state, 0, P.LUDICROUS_ORDNANCE)
    set_pp(state, 0, 8)
    play(state, gun)
    assert count(p.field, P.LUDICROUS_ORDNANCE) == 3
    state = start()
    p = state.players[0]
    gun, = hand_only(state, 0, P.LUDICROUS_ORDNANCE)
    set_pp(state, 0, 4)
    play(state, gun)
    assert count(p.field, P.LUDICROUS_ORDNANCE) == 1


# --- set 10009 -------------------------------------------------------------------------------

def test_bluerust_underling_needs_no_duplicates():
    state = start()
    giant = put(state, 1, demo.GIANT)
    underling, = hand_only(state, 0, P.BLUERUST_UNDERLING)
    set_pp(state, 0, 1)
    assert plays(state, underling.uid) == [PlayCard(underling.uid)]     # duplicates: no target
    highlander(state)
    assert PlayCard(underling.uid, (giant.uid,)) in plays(state, underling.uid)
    play(state, underling, (giant.uid,))
    assert giant.fate == DESTROYED


def test_twindrone_engineer_fanfare_and_evolve():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    engineer, = hand_only(state, 0, P.TWINDRONE_ENGINEER)
    set_pp(state, 0, 4)
    play(state, engineer)
    assert count(p.field, P.ANALYZING_ARTIFACT) == 1 and len(p.hand) == 1
    apply(state, Evolve(engineer.uid))
    assert count(p.field, P.ANALYZING_ARTIFACT) == 2 and len(p.hand) == 2


def test_dimensional_selection_modes():
    state = start()
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    spell, = hand_only(state, 0, P.DIMENSIONAL_SELECTION)
    set_pp(state, 0, 6)
    assert {a.modes for a in plays(state, spell.uid)} == {(0,), (1,)}
    play(state, spell, modes=(1,))
    assert count(p.field, P.MYSTIC_ARTIFACT) == 2 and giant.life == 5
    spell, = hand_only(state, 0, P.DIMENSIONAL_SELECTION)
    set_pp(state, 0, 6)
    play(state, spell, modes=(0,))
    assert giant.fate == DESTROYED


def test_ironwork_bodyguard_with_no_duplicates():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    highlander(state)
    giant = put(state, 1, demo.GIANT)
    guard, = hand_only(state, 0, P.IRONWORK_BODYGUARD)
    set_pp(state, 0, 4)
    play(state, guard, (giant.uid,))
    assert giant.life == 1 and p.leader_hp == 14
    state = start()
    guard, = hand_only(state, 0, P.IRONWORK_BODYGUARD)
    put(state, 1, demo.GIANT)
    set_pp(state, 0, 4)
    assert plays(state, guard.uid) == [PlayCard(guard.uid)]


def test_blade_puppeteer_pings_for_each_puppet():
    state = start()
    p, opp = state.players
    puppeteer, puppet = hand_only(state, 0, P.BLADE_PUPPETEER, P.PUPPET)
    set_pp(state, 0, 6)
    play(state, puppeteer)
    assert count(p.field, P.PUPPET) == 1 and count(p.field, P.ENHANCED_PUPPET) == 1
    assert opp.leader_hp == 18
    play(state, puppet)
    assert opp.leader_hp == 17
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert opp.leader_hp == 17


def test_disgraceful_banishment():
    state = start()
    p = state.players[0]
    highlander(state, extra=[P.CUTTHROAT])
    spell, footman = hand_only(state, 0, P.DISGRACEFUL_BANISHMENT, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, spell, (footman.uid,))
    assert p.hand[0].defn == P.CUTTHROAT and len(p.hand) == 3 and p.shadows == 2
    state = start()
    p = state.players[0]
    p.deck.append(state.new_instance(P.CUTTHROAT, 0))
    spell, footman = hand_only(state, 0, P.DISGRACEFUL_BANISHMENT, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, spell, (footman.uid,))
    assert [c.defn for c in p.hand] == [P.CUTTHROAT]


def test_steelforged_right_hand():
    for unique in (False, True):
        state = start()
        if unique:
            highlander(state)
        giant = put(state, 1, demo.GIANT)
        hand, = hand_only(state, 0, P.STEELFORGED_RIGHT_HAND)
        set_pp(state, 0, 5)
        play(state, hand, (giant.uid,))
        assert giant.fate == DESTROYED and hand.has(Keyword.STORM) == unique


def test_soulforge():
    for unique in (False, True):
        state = start()
        if unique:
            highlander(state)
        a, b = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
        spell, = hand_only(state, 0, P.SOULFORGE)
        set_pp(state, 0, 3)
        play(state, spell, (a.uid,))
        assert a.fate == DESTROYED and (b.fate == DESTROYED) == unique


def test_aizeden_destroys_for_each_artifact():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    footman = put(state, 1, demo.FOOTMAN)
    aizeden, = hand_only(state, 0, P.AIZEDEN)
    set_pp(state, 0, 7)
    play(state, aizeden)
    assert count(p.field, P.WARDEN_OF_THE_TRIGGER) == 1 and footman.fate == DESTROYED
    giant = put(state, 1, demo.GIANT)
    apply(state, Evolve(aizeden.uid))                     # plain evolve: no replicate
    assert count(p.field, P.WARDEN_OF_THE_TRIGGER) == 1 and giant.fate == IN_PLAY
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    aizeden = put(state, 0, P.AIZEDEN)
    giant = put(state, 1, demo.GIANT)
    apply(state, Evolve(aizeden.uid, super_=True))
    assert count(p.field, P.WARDEN_OF_THE_TRIGGER) == 1 and giant.fate == DESTROYED


# --- set 10008 -------------------------------------------------------------------------------

def test_kratos_comes_back_once():
    state = start()
    p = state.players[0]
    kratos = put(state, 0, P.KRATOS)
    E.destroy(state, kratos)
    resolve_queue(state)
    second = p.field[0]
    assert second.defn == P.KRATOS and second is not kratos
    E.destroy(state, second)
    resolve_queue(state)
    assert p.field == []


def test_leona_super_evolve_gives_ambush():
    state = start()
    unlock_evolution(state, 0)
    leona, footman = put(state, 0, P.LEONA), put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(leona.uid, False, (footman.uid,)))
    assert not footman.has(Keyword.AMBUSH)
    state = start()
    unlock_evolution(state, 0)
    leona, footman = put(state, 0, P.LEONA), put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(leona.uid, True, (footman.uid,)))
    assert footman.has(Keyword.AMBUSH) and not leona.has(Keyword.AMBUSH)


def test_myuu_with_ambush_keeps_it_when_its_evolve_hits_nothing():
    """Official Q&A (Leona): Myuu given Ambush evolves with no enemy followers: it keeps Ambush."""
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    myuu = put(state, 0, P.MYUU)
    E.give_keywords(myuu, Keyword.AMBUSH)
    apply(state, Evolve(myuu.uid))
    assert count(p.field, P.ANCIENT_ARTIFACT) == 1 and myuu.has(Keyword.AMBUSH)


def test_zerk_adds_a_destroyed_artifact():
    state = start()
    p = state.players[0]
    zerk, = hand_only(state, 0, P.ZERK)
    set_pp(state, 0, 1)
    play(state, zerk)
    assert p.hand == []
    artifacts_destroyed(state, 0, demo.FOOTMAN, P.MYSTIC_ARTIFACT)
    zerk, = hand_only(state, 0, P.ZERK)
    set_pp(state, 0, 1)
    play(state, zerk)
    assert [c.defn for c in p.hand] == [P.MYSTIC_ARTIFACT]


def test_layla_lazuli_and_isaac_add_artifacts():
    state = start()
    p = state.players[0]
    p.hand.clear()
    for defn, token in ((P.LAYLA, P.ANCIENT_ARTIFACT), (P.ISAAC, P.STRIKER_ARTIFACT),
                        (P.CASSIUS, P.FORTIFIER_ARTIFACT)):
        E.destroy(state, put(state, 0, defn))
        resolve_queue(state)
        assert p.hand[-1].defn == token
    lazuli = give(state, 0, P.LAZULI)
    set_pp(state, 0, 3)
    play(state, lazuli)
    assert p.hand[-1].defn == P.RADIANT_ARTIFACT


def test_unsullied_days():
    for unlocked in (False, True):
        state = start()
        p = state.players[0]
        p.leader_hp = 10
        if unlocked:
            unlock_evolution(state, 0)
        spell, = hand_only(state, 0, P.UNSULLIED_DAYS)
        set_pp(state, 0, 3)
        play(state, spell)
        assert len(p.hand) == 2 and p.leader_hp == (12 if unlocked else 10)


def test_miriam():
    state = start()
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    miriam, = hand_only(state, 0, P.MIRIAM)
    set_pp(state, 0, 7)
    play(state, miriam, (giant.uid,))
    radiant = p.field[-1]
    assert giant.fate == DESTROYED and radiant.defn == P.RADIANT_ARTIFACT
    assert Attack(radiant.uid, leader_uid(1)) in legal_actions(state)        # Storm


def test_the_journey_ahead_recovers_an_evolution_point():
    for artifacts, ep in ((THREE_ARTIFACTS[:2], 0), (THREE_ARTIFACTS, 1)):
        state = start()
        p = state.players[0]
        p.ep = 0
        for defn in artifacts:
            put(state, 0, defn)
        giant = put(state, 1, demo.GIANT)
        spell, = hand_only(state, 0, P.THE_JOURNEY_AHEAD)
        set_pp(state, 0, 3)
        play(state, spell, (giant.uid,))
        assert giant.fate == DESTROYED and p.ep == ep


def test_asher_and_lydia():
    state = start()
    footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    asher, = hand_only(state, 0, P.ASHER_AND_LYDIA)
    set_pp(state, 0, 5)
    play(state, asher, (footman.uid,))
    assert footman.has(Keyword.WARD) and not asher.evolved
    state = start()
    footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    asher, = hand_only(state, 0, P.ASHER_AND_LYDIA)
    set_pp(state, 0, 9)
    play(state, asher, (footman.uid,))
    assert asher.evolved and asher.has(Keyword.STORM)
    assert footman.fate == DESTROYED and giant.fate == IN_PLAY      # only Ward followers
    state = start()
    unlock_evolution(state, 0)
    asher = put(state, 0, P.ASHER_AND_LYDIA)
    wards = [put(state, 1, demo.SHIELDBEARER) for _ in range(3)]
    apply(state, Evolve(asher.uid))
    assert sum(w.fate == DESTROYED for w in wards) == 2


def test_eudie():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    eudie, = hand_only(state, 0, P.EUDIE)
    set_pp(state, 0, 2)
    play(state, eudie)
    assert [c.defn for c in p.hand] == [P.ANALYZING_ARTIFACT]
    done, footman = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    E.evolve(state, done)
    resolve_queue(state)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == eudie.uid]
    assert {a.targets for a in evolves} == {(footman.uid,)}
    apply(state, Evolve(eudie.uid, False, (footman.uid,)))
    assert footman.evolved and p.ep == 1


# --- set 10007 -------------------------------------------------------------------------------

def test_brusque_barkeep():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    unlock_evolution(state, 0)
    barkeep = put(state, 0, P.BRUSQUE_BARKEEP)
    put(state, 0, P.ANCIENT_ARTIFACT)
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert p.leader_hp == 11
    apply(state, Evolve(barkeep.uid))
    assert count(p.field, P.MYSTIC_ARTIFACT) == 1 and p.leader_hp == 12


def test_beat_breaker():
    for artifacts, total in ((False, 2), (True, 3)):
        state = start()
        p = state.players[0]
        if artifacts:
            artifacts_destroyed(state, 0, *THREE_ARTIFACTS)
        breaker, = hand_only(state, 0, P.BEAT_BREAKER)
        set_pp(state, 0, 7)
        play(state, breaker)
        assert count(p.field, P.BEAT_BREAKER) == total


def test_freerunning_modes():
    state = start()
    p = state.players[0]
    spell, = hand_only(state, 0, P.FREERUNNING)
    set_pp(state, 0, 1)
    assert {a.modes for a in plays(state, spell.uid)} == {(0,), (1,)}
    play(state, spell, modes=(1,))
    assert [c.defn for c in p.hand] == [P.ANCIENT_ARTIFACT]
    artifacts_destroyed(state, 0, *THREE_ARTIFACTS)
    spell, = hand_only(state, 0, P.FREERUNNING)
    set_pp(state, 0, 1)
    assert [a.modes for a in plays(state, spell.uid)] == [(0, 1)]
    play(state, spell, modes=(0, 1))
    assert [c.defn for c in p.hand] == [P.ANALYZING_ARTIFACT, P.ANCIENT_ARTIFACT]


def test_artifacts_that_left_the_field_still_count():
    """Cards that ask note entering Artifacts from hand and deck, so banished ones count."""
    state = start()
    p = state.players[0]
    spell, = hand_only(state, 0, P.FREERUNNING)
    reader = state.new_instance(P.WARP_SLASH, 0)
    p.deck.append(reader)
    for defn in THREE_ARTIFACTS + (P.ANCIENT_ARTIFACT,):
        artifact = put(state, 0, defn)
        resolve_queue(state)
        E.banish(state, artifact)
    assert p.field == [] and p.destroyed == []
    assert P.artifacts_entered(state, 0) == 3
    assert len(reader.counters[P.SEEN_ARTIFACTS]) == 3
    set_pp(state, 0, 1)
    assert [a.modes for a in plays(state, spell.uid)] == [(0, 1)]
    assert P.artifacts_entered(state, 1) == 0


def test_cool_courier():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    courier, = hand_only(state, 0, P.COOL_COURIER)
    set_pp(state, 0, 2)
    play(state, courier)
    apply(state, Evolve(courier.uid))
    assert count(p.hand, P.ANCIENT_ARTIFACT) == 2


def test_audacious_artist():
    for artifacts in (False, True):
        state = start()
        p = state.players[0]
        if artifacts:
            artifacts_destroyed(state, 0, *THREE_ARTIFACTS)
        giant = put(state, 1, demo.GIANT)
        artist, = hand_only(state, 0, P.AUDACIOUS_ARTIST)
        set_pp(state, 0, 6)
        play(state, artist, (giant.uid,))
        assert giant.fate == DESTROYED
        assert [c.defn for c in p.field[1:]] == ([P.ANCIENT_ARTIFACT, P.MYSTIC_ARTIFACT] if artifacts else [])


def test_blink_step():
    for unlocked in (False, True):
        state = start()
        if unlocked:
            unlock_evolution(state, 0)
        footman = put(state, 0, demo.FOOTMAN)
        spell, held = hand_only(state, 0, P.BLINK_STEP, demo.FOOTMAN)
        set_pp(state, 0, 2)
        play(state, spell)
        assert footman.atk == 2 and held.atk == (2 if unlocked else 1)


def test_brazen_broadcaster():
    for pp, mystic in ((3, 0), (5, 1)):
        state = start()
        p = state.players[0]
        enemy = put(state, 1, demo.FOOTMAN)
        broadcaster, = hand_only(state, 0, P.BRAZEN_BROADCASTER)
        set_pp(state, 0, pp)
        play(state, broadcaster)
        artifacts = [f for f in p.field if f is not broadcaster]
        assert count(artifacts, P.ANALYZING_ARTIFACT) == 1 and count(artifacts, P.MYSTIC_ARTIFACT) == mystic
        assert all(a.has(Keyword.RUSH) for a in artifacts) and len(p.hand) == 1
        assert Attack(artifacts[0].uid, enemy.uid) in legal_actions(state)
        assert p.pp == pp - (5 if mystic else 3)


def test_warp_slash_and_scarlet_count_artifacts():
    state = start()
    p, opp = state.players
    artifacts_destroyed(state, 0, P.ANCIENT_ARTIFACT, P.ANCIENT_ARTIFACT, P.MYSTIC_ARTIFACT)
    put(state, 0, P.RADIANT_ARTIFACT)
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, 5)                            # 5/10
    slash, scarlet = hand_only(state, 0, P.WARP_SLASH, P.SCARLET)
    set_pp(state, 0, 3)
    play(state, slash)
    assert giant.life == 7 and opp.leader_hp == 19
    set_pp(state, 0, 8)
    play(state, scarlet)
    assert giant.life == 4 and opp.leader_hp == 19
    assert Attack(scarlet.uid, leader_uid(1)) in legal_actions(state)


def test_myuu():
    state = start()
    unlock_evolution(state, 0)
    myuu = put(state, 0, P.MYUU)
    giant = put(state, 1, demo.GIANT)
    portal.summon(state, 0, P.MYSTIC_ARTIFACT)
    resolve_queue(state)
    assert giant.life == 2
    apply(state, Evolve(myuu.uid, super_=True))           # Ancient Artifact: only 2 names so far
    assert giant.fate == DESTROYED and not myuu.has(Keyword.STORM)
    state = start()
    unlock_evolution(state, 0)
    artifacts_destroyed(state, 0, P.MYSTIC_ARTIFACT, P.RADIANT_ARTIFACT)
    myuu = put(state, 0, P.MYUU)
    apply(state, Evolve(myuu.uid, super_=True))           # the Ancient Artifact makes 3
    assert myuu.has(Keyword.STORM)
    state = start()
    unlock_evolution(state, 0)
    artifacts_destroyed(state, 0, *THREE_ARTIFACTS)
    myuu = put(state, 0, P.MYUU)
    apply(state, Evolve(myuu.uid))                        # plain evolve: no Storm
    assert not myuu.has(Keyword.STORM)


# --- set 10006 -------------------------------------------------------------------------------

def test_brilliant_inventor():
    state = start()
    p = state.players[0]
    inventor, = hand_only(state, 0, P.BRILLIANT_INVENTOR)
    set_pp(state, 0, 6)
    play(state, inventor)
    alpha = p.field[-1]
    assert alpha.defn == P.OMINOUS_ARTIFACT_ALPHA and alpha.has(Keyword.BANE | Keyword.WARD)


def test_advent_of_the_eld_axe():
    for big, cards in ((False, 0), (True, 1)):
        state = start()
        p = state.players[0]
        if big:
            put(state, 0, demo.GIANT)
        giant = put(state, 1, demo.GIANT)
        spell, = hand_only(state, 0, P.ADVENT_OF_THE_ELD_AXE)
        set_pp(state, 0, 2)
        play(state, spell, (giant.uid,))
        assert giant.life == 1 and len(p.hand) == cards


def test_timid_pioneer_banishes_a_small_follower():
    state = start()
    footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    pioneer, = hand_only(state, 0, P.TIMID_PIONEER)
    set_pp(state, 0, 4)
    assert {a.targets for a in plays(state, pioneer.uid)} == {(footman.uid,)}
    play(state, pioneer, (footman.uid,))
    assert footman.fate == BANISHED and giant.fate == IN_PLAY
    assert state.players[1].shadows == 0


def test_myriad_designs():
    state = start()
    p = state.players[0]
    spell, = hand_only(state, 0, P.MYRIAD_DESIGNS)
    set_pp(state, 0, 6)
    play(state, spell)
    assert [(f.defn, f.atk, f.life, f.evolved) for f in p.field] == [
        (P.LUDICROUS_ORDNANCE, 3, 5, False), (P.SHODDY_PLAYTHING, 1, 4, False),
        (P.SUBSTANDARD_PUPPET, 2, 2, False)]
    assert p.hand == []                                   # summoned: no Fanfares


def test_ludicrous_ordnance_splits_damage():
    state = start(first=0)
    unlock_evolution(state, 0)
    gun = put(state, 0, P.LUDICROUS_ORDNANCE)
    footman, giant = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    apply(state, EndTurn())
    assert footman.fate == DESTROYED and giant.life == 4      # oldest first
    apply(state, EndTurn())
    apply(state, Evolve(gun.uid))
    assert giant.life == 1


def test_unfeeling_eld_axe():
    state = start(first=0)
    p = state.players[0]
    axe, = hand_only(state, 0, P.UNFEELING_ELD_AXE)
    put(state, 0, demo.FOOTMAN)
    mine = put(state, 0, demo.GIANT)
    resolve_queue(state)
    assert axe.cost == 2
    apply(state, EndTurn())
    assert axe.cost == 3
    apply(state, EndTurn())
    enemy = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    play(state, axe)
    assert mine.evolved and enemy.fate == DESTROYED and p.ep == 2


def test_camiscilla():
    state = start()
    p, opp = state.players
    unlock_evolution(state, 0)
    camiscilla, = hand_only(state, 0, P.CAMISCILLA)
    set_pp(state, 0, 7)
    play(state, camiscilla)
    assert [f.defn for f in p.field] == [P.CAMISCILLA, P.SHODDY_PLAYTHING, P.SUBSTANDARD_PUPPET]
    assert [f.evolved for f in p.field] == [False, True, True]
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert not p.field[-1].evolved
    apply(state, Evolve(camiscilla.uid, super_=True))
    assert opp.leader_hp == 17


def test_yog_zentha():
    for big in (False, True):
        state = start()
        p = state.players[0]
        if big:
            put(state, 0, demo.GIANT)
        yog, = hand_only(state, 0, P.YOG_ZENTHA)
        set_pp(state, 0, 2)
        play(state, yog)
        assert [c.defn for c in p.hand] == ([P.DEPTHS_OF_THE_ELD_AXE] if big else [])


# --- set 10005 -------------------------------------------------------------------------------

def test_marionette_master():
    for pp, storm in ((4, False), (7, True)):
        state = start()
        p = state.players[0]
        master, = hand_only(state, 0, P.MARIONETTE_MASTER)
        set_pp(state, 0, pp)
        play(state, master)
        puppets = p.field[1:]
        assert [f.defn for f in puppets] == [P.ENHANCED_PUPPET, P.PUPPET]
        assert all(f.has(Keyword.STORM) == storm for f in puppets)


def test_flowering_artisan():
    state = start()
    p = state.players[0]
    p.deck.insert(0, state.new_instance(P.LIGHT_OF_THE_DEWDROP, 0))
    artisan, = hand_only(state, 0, P.FLOWERING_ARTISAN)
    set_pp(state, 0, 5)
    play(state, artisan)
    light = p.hand[0]
    assert light.defn == P.LIGHT_OF_THE_DEWDROP
    giant, footman = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    follower = give(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 2)
    play(state, follower)
    assert giant.life == 5
    play(state, light)
    assert giant.life == 2 and footman.fate == DESTROYED


def test_light_of_the_dewdrop():
    state = start()
    light, = hand_only(state, 0, P.LIGHT_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    play(state, light)
    assert len(state.players[0].hand) == 1


def test_new_age_cartographer():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    cartographer, = hand_only(state, 0, P.NEW_AGE_CARTOGRAPHER)
    set_pp(state, 0, 4)
    play(state, cartographer)
    beta, = p.hand
    assert beta.defn == P.OMINOUS_ARTIFACT_BETA
    analyzing = give(state, 0, P.ANALYZING_ARTIFACT)
    omega = give(state, 0, P.MASTERWORK_ARTIFACT_OMEGA)
    E.add_cost(analyzing, 1)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.super_]
    assert {a.targets for a in evolves} == {(beta.uid,), (analyzing.uid,)}
    apply(state, Evolve(cartographer.uid, True, (analyzing.uid,)))
    copy = p.field[-1]
    assert copy.defn == P.ANALYZING_ARTIFACT and copy is not analyzing and analyzing in p.hand
    assert copy.cost == 2                                 # an exact copy
    assert len(p.hand) == 4 and omega in p.hand           # it drew when it entered


def test_lunar_bunny():
    state = start()
    bunny = put(state, 0, P.LUNAR_BUNNY)
    footman, light = hand_only(state, 0, demo.FOOTMAN, P.LIGHT_OF_THE_DEWDROP)
    set_pp(state, 0, 2)
    play(state, footman)
    assert not bunny.evolved
    play(state, light)
    assert bunny.evolved and (bunny.atk, bunny.life) == (3, 3)
    state = start()
    bunny = put(state, 0, P.LUNAR_BUNNY)
    toy, = hand_only(state, 0, P.SHODDY_PLAYTHING)
    set_pp(state, 0, 2)
    play(state, toy)                                      # an Accelerated card is played as a spell
    assert bunny.evolved


def test_resurrection_tuner():
    state = start()
    p = state.players[0]
    p.destroyed += [demo.FOOTMAN, demo.FOOTMAN, demo.GIANT, demo.LANCER]
    spell, footman = hand_only(state, 0, P.RESURRECTION_TUNER, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, spell, (footman.uid,))
    names = [c.defn.name for c in p.hand]
    assert len(names) == 2 and len(set(names)) == 2
    assert set(names) <= {"Footman", "Giant", "Lancer"}
    assert p.shadows == 2
    spell, = hand_only(state, 0, P.RESURRECTION_TUNER)
    set_pp(state, 0, 1)
    assert plays(state, spell.uid) == []                  # nothing to discard


def test_neuron_disrupter():
    state = start()
    p = state.players[0]
    put(state, 0, demo.FOOTMAN)
    put(state, 0, demo.FOOTMAN)
    neuron, = hand_only(state, 0, P.NEURON_DISRUPTER)
    set_pp(state, 0, 5)
    play(state, neuron)
    assert p.pp == 2
    E.destroy(state, neuron)
    resolve_queue(state)
    assert len(p.hand) == 2


def test_sincerity_of_the_dewdrop():
    state = start()
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 2, 2)
    spell, = hand_only(state, 0, P.SINCERITY_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    play(state, spell, (giant.uid,))
    assert giant.defn == P.IMARIS_LITTLE_BUDDIES and (giant.atk, giant.life) == (3, 3)
    assert giant.has(Keyword.RUSH) and state.players[1].field == [giant]


def test_slaus_activates_each_ability_once_then_leaves_a_crest():
    state = start(first=0)
    p, opp = state.players
    p.leader_hp = 10
    slaus = put(state, 0, P.SLAUS)
    seen = []
    for _ in range(3):
        pass_turns(state, 2)
        last = slaus.counters["wheel"][-1]
        seen.append(last)
        if last == 0:
            assert sum(c.cost == 0 for c in p.hand) == len(p.hand) - 1
    assert sorted(seen) == [0, 1, 2]
    assert (slaus.atk, slaus.life) == (2, 4) and p.leader_hp == 13
    pass_turns(state, 2)
    assert len(slaus.counters["wheel"]) == 3              # nothing left to activate
    apply(state, EndTurn())
    assert slaus.fate == IN_PLAY and opp.leader_area == []   # not evolved
    apply(state, EndTurn())
    E.evolve(state, slaus)
    resolve_queue(state)
    apply(state, EndTurn())
    assert slaus.fate == BANISHED and [c.defn for c in opp.leader_area] == [P.SLAUS_CREST]


def test_imari():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [demo.FOOTMAN] * 5 + [P.LIGHT_OF_THE_DEWDROP])
    imari, footman = hand_only(state, 0, P.IMARI, demo.FOOTMAN)
    set_pp(state, 0, 3)
    play(state, imari, (footman.uid,))
    light, = p.hand
    assert light.defn == P.LIGHT_OF_THE_DEWDROP and p.shadows == 1
    play(state, light)
    assert count(p.field, P.IMARIS_LITTLE_BUDDIES) == 0     # not evolved yet
    p.hand.clear()
    deck_of(state, 0, [P.LIGHT_OF_THE_DEWDROP] * 3 + [P.DISGRACEFUL_BANISHMENT, P.BULLET_FROM_BEYOND])
    apply(state, Evolve(imari.uid, super_=True))
    assert sorted(c.defn.name for c in p.hand) == ["Disgraceful Banishment", "Light of the Dewdrop"]
    light = next(c for c in p.hand if c.defn == P.LIGHT_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    play(state, light)
    assert count(p.field, P.IMARIS_LITTLE_BUDDIES) == 1


# --- set 10000 (Basic) ---------------------------------------------------------------------------

def test_basic_followers_add_tokens():
    for defn, token in ((P.KITTY_CANNONEER, P.GEAR_OF_AMBITION), (P.PUPPET_LANCER, P.ENHANCED_PUPPET),
                        (P.ELECTRIC_WHIP_LASS, P.GEAR_OF_REMEMBRANCE)):
        state = start()
        follower, = hand_only(state, 0, defn)
        set_pp(state, 0, 3)
        play(state, follower)
        assert [c.defn for c in state.players[0].hand] == [token]


def test_bullet_from_beyond():
    """Official Q&A: it can't be played without an enemy follower."""
    state = start()
    p = state.players[0]
    bullet, = hand_only(state, 0, P.BULLET_FROM_BEYOND)
    set_pp(state, 0, 4)
    assert plays(state, bullet.uid) == []
    giant = put(state, 1, demo.GIANT)
    play(state, bullet, (giant.uid,))
    assert giant.fate == DESTROYED
    assert [c.defn for c in p.hand] == [P.GEAR_OF_AMBITION, P.GEAR_OF_REMEMBRANCE]


def test_mecha_cavalier():
    for super_, total in ((False, 2), (True, 3)):
        state = start()
        unlock_evolution(state, 0)
        cavalier = put(state, 0, P.MECHA_CAVALIER)
        apply(state, Evolve(cavalier.uid, super_=super_))
        assert count(state.players[0].field, P.MECHA_CAVALIER) == total


def test_puppet_theater():
    state = start(first=0)
    p = state.players[0]
    theater, = hand_only(state, 0, P.PUPPET_THEATER)
    set_pp(state, 0, 2)
    play(state, theater)
    assert count(p.hand, P.PUPPET) == 1
    apply(state, EndTurn())
    assert count(p.hand, P.PUPPET) == 2
    for _ in range(2):
        pass_turns(state, 2)
    assert theater.fate == DESTROYED and count(p.hand, P.PUPPET) == 3


# --- set 10004 ---------------------------------------------------------------------------------

def test_sho_gets_barrier_once_super_evolution_is_unlocked():
    for unlocked in (False, True):
        state = start()
        if unlocked:
            unlock_evolution(state, 0)
        sho, = hand_only(state, 0, P.SHO)
        set_pp(state, 0, 3)
        play(state, sho)
        assert sho.has(Keyword.BARRIER) == unlocked


def test_tsubasa_fills_skybound_gauges():
    state = start()
    tsubasa, legion, footman = hand_only(state, 0, P.TSUBASA, P.CHAOS_LEGION, demo.FOOTMAN)
    set_pp(state, 0, 2)
    play(state, tsubasa)
    assert E.skybound_gauge(state, legion) == 2 and footman.counters is None


def test_eustace():
    state = start()
    p = state.players[0]
    footman = put(state, 0, demo.FOOTMAN)
    eustace, = hand_only(state, 0, P.EUSTACE)
    set_pp(state, 0, 5)
    play(state, eustace, (footman.uid,))
    assert not eustace.evolved and not footman.evolved
    state = start()
    p = state.players[0]
    p.turns_taken = 10
    footman = put(state, 0, demo.FOOTMAN)
    eustace, = hand_only(state, 0, P.EUSTACE)
    set_pp(state, 0, 5)
    play(state, eustace, (footman.uid,))
    assert eustace.evolved and footman.evolved and p.ep == 2
    state = start()
    state.players[0].turns_taken = 10
    eustace, = hand_only(state, 0, P.EUSTACE)
    set_pp(state, 0, 5)
    play(state, eustace)                                  # no other follower: it still evolves
    assert eustace.evolved


def test_eustace_clash():
    state = start()
    eustace = put(state, 0, P.EUSTACE)
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, 2)                            # 5/7: survives 5, not 3 + 5
    apply(state, Attack(eustace.uid, giant.uid))
    assert giant.fate == DESTROYED


def test_ilsa_modes():
    state = start()
    giant = put(state, 1, demo.GIANT)
    ilsa, = hand_only(state, 0, P.ILSA)
    set_pp(state, 0, 7)
    play(state, ilsa, modes=(0,))
    assert giant.fate == DESTROYED and state.players[1].leader_hp == 20
    ilsa, = hand_only(state, 0, P.ILSA)
    set_pp(state, 0, 7)
    play(state, ilsa, modes=(1,))
    assert state.players[1].leader_hp == 16


def test_stone_breaker():
    state = start()
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, 3)
    spell, = hand_only(state, 0, P.STONE_BREAKER)
    set_pp(state, 0, 3)
    play(state, spell)
    assert giant.life == 2


def test_cassius():
    """Official Q&A: with no Artifact follower in hand, the Fanfare deals 0 damage."""
    state = start()
    giant = put(state, 1, demo.GIANT)
    cassius, footman = hand_only(state, 0, P.CASSIUS, demo.FOOTMAN)
    set_pp(state, 0, 5)
    assert plays(state, cassius.uid) == [PlayCard(cassius.uid)]
    play(state, cassius)
    assert giant.life == 5
    cassius, striker = hand_only(state, 0, P.CASSIUS, P.STRIKER_ARTIFACT)
    set_pp(state, 0, 5)
    play(state, cassius, (striker.uid,))
    assert giant.fate == DESTROYED and striker in state.players[0].hand


def test_chaos_legion():
    for turns, amount in ((1, 3), (15, 6)):
        state = start()
        state.players[0].turns_taken = turns
        giant = put(state, 1, demo.GIANT)
        E.buff(state, giant, 0, 5)
        spell, = hand_only(state, 0, P.CHAOS_LEGION)
        set_pp(state, 0, 6)
        play(state, spell)
        assert giant.life == 10 - amount and state.players[1].leader_hp == 20 - amount


def test_lu_woh():
    for turns, crest in ((1, False), (10, True)):
        state = start()
        p, opp = state.players
        p.turns_taken = turns
        giant = put(state, 1, demo.GIANT)
        E.buff(state, giant, 0, 3)
        lu_woh, = hand_only(state, 0, P.LU_WOH)
        set_pp(state, 0, 5)
        play(state, lu_woh)
        assert giant.life == 2
        assert all(c.atk == 2 for c in opp.hand if c.defn == demo.FOOTMAN)
        assert ([c.defn for c in p.leader_area] == [P.LU_WOH_CREST]) == crest


def test_beelzebub_removes_abilities_and_deals_nine():
    state = start()
    angel = put(state, 1, demo.ANGEL)                     # Barrier
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, 7)
    E.give_keywords(giant, Keyword.WARD)
    beelzebub, = hand_only(state, 0, P.BEELZEBUB)
    set_pp(state, 0, 9)
    play(state, beelzebub, (angel.uid, giant.uid))
    assert angel.fate == DESTROYED
    assert giant.life == 3 and giant.keywords == Keyword.NONE


# --- random games ----------------------------------------------------------------------------

def random_deck(rng):
    pool = [c for c in collectible(Craft.PORTAL) if has_script(c.card_id) or c in P.VANILLA]
    deck = []
    while len(deck) < 40:
        c = rng.choice(pool)
        if deck.count(c) < 3:
            deck.append(c)
    return deck


def test_random_portal_games():
    for g in range(100):
        rng = random.Random(g)
        deck = random_deck(rng)
        state = new_game(deck, list(deck), seed=g)
        agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
        assert play_game(state, agents) in (0, 1, -1)
        assert state.over
