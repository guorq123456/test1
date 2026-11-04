"""Regression tests for the tournament Pirate Sword list (旗皇比赛版, pirate-t).

One test per card of the list (core cards, then the other standard cards, then
the free-slot cards), each checking the official behaviour on a small position.
The tokens, crest and faith the cards create are exercised inside the tests of
the cards that make them. Existing tests in test_pirate_sword.py and
test_cards_sword.py already cover the basic cases; these add what they miss
(super-evolution also firing Evolve abilities, Enhance thresholds, full
fields, Aura, Rush / Storm timing, ...).
"""
from svsim.cards import demo, sword
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import has_script
from svsim.core.state import BANISHED, DESTROYED, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution

WALL = CardDef(7951, "Wall", Craft.NEUTRAL, CardType.FOLLOWER, 5, 0, 20)   # 0/20, no ability
WARD, STORM, RUSH, BANE, AURA = Keyword.WARD, Keyword.STORM, Keyword.RUSH, Keyword.BANE, Keyword.AURA
FLAG = sword.DREAD_PIRATES_FLAG
GOLD = sword.GLITTERING_GOLD


def attacks_of(state, uid) -> set:
    return {a.target for a in legal_actions(state) if isinstance(a, Attack) and a.attacker == uid}


def evolve_targets(state, uid, super_=False) -> set:
    return {a.targets for a in legal_actions(state)
            if isinstance(a, Evolve) and a.uid == uid and a.super_ == super_}


def fresh_state(deck=None):
    """Player 0 to act on turn 1 with an empty hand."""
    state = start(deck=deck)
    state.players[0].hand.clear()
    return state


# =====================================================================================
# Core cards
# =====================================================================================

def test_yidmetra_eld_sword():
    # Fanfare: add a Depths of the Eld Sword (0 cost: 1 damage, Enhance 1: 3 damage).
    # Evolve: spend 5 faith so the faith buffs all allied followers +1/+1 per Enhanced
    # card. Super-evolving with points also fires the Evolve ability.
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    p = state.players[0]
    p.hand.clear()
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    wall = put(state, 1, WALL)
    set_pp(state, 0, 2)
    yidmetra = give(state, 0, sword.YIDMETRA)
    apply(state, PlayCard(yidmetra.uid))
    depths = p.hand[-1]
    assert depths.defn == sword.DEPTHS_OF_THE_ELD_SWORD and depths.cost == 0
    apply(state, PlayCard(depths.uid, (wall.uid,)))           # 0 PP: not Enhanced
    assert wall.life == 19 and E.counters(faith).get("value", 0) == 0

    E.counters(faith)["value"] = 5
    unlock_evolution(state, 0)
    apply(state, Evolve(yidmetra.uid, super_=True))
    assert faith.counters["value"] == 0 and faith.counters["buffs"] == 1
    ally = put(state, 0, demo.FOOTMAN)                         # 1/2
    set_pp(state, 0, 1)
    depths = give(state, 0, sword.DEPTHS_OF_THE_ELD_SWORD)
    apply(state, PlayCard(depths.uid, (wall.uid,)))           # Enhance (1): 3 damage
    assert wall.life == 16 and p.pp == 0
    assert (ally.atk, ally.life) == (2, 3)
    assert (yidmetra.atk, yidmetra.life) == (1 + 3 + 1, 2 + 3 + 1)
    assert faith.counters["value"] == 1


def test_open_sea_scout():
    # Fanfare: summon a Dread Pirate's Flag. Evolve: add a Gilded Boots (fires on
    # super-evolution too). Boots: +1/+0 and Rush to an allied follower.
    state = fresh_state()
    p = state.players[0]
    set_pp(state, 0, 2)
    scout = give(state, 0, sword.OPEN_SEA_SCOUT)
    apply(state, PlayCard(scout.uid))
    flag = p.field[-1]
    assert flag.defn == FLAG and flag.countdown == 7 and (scout.atk, scout.life) == (2, 2)
    unlock_evolution(state, 0)
    apply(state, Evolve(scout.uid, super_=True))
    assert [c.defn for c in p.hand] == [sword.GILDED_BOOTS]
    newcomer = put(state, 0, demo.FOOTMAN, ready=False)
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 1)
    boots = p.hand[0]
    assert boots.cost == 1
    apply(state, PlayCard(boots.uid, (newcomer.uid,)))
    assert newcomer.atk == 2 and attacks_of(state, newcomer.uid) == {enemy.uid}   # Rush, not Storm
    assert flag.countdown == 6                                 # Boots is a spell


def test_splendor_of_the_goldbloom():
    # Add 2 Glittering Gold; Enhance (5): add 4. Gold: 0 cost spell, Mode: draw a
    # card / 2 damage to a random enemy follower.
    for pp, golds in ((4, 2), (5, 4)):
        state = fresh_state()
        p = state.players[0]
        flag = put(state, 0, FLAG)
        set_pp(state, 0, pp)
        card = give(state, 0, sword.SPLENDOR_OF_THE_GOLDBLOOM)
        apply(state, PlayCard(card.uid))
        assert count(p.hand, GOLD) == golds and p.pp == pp - (5 if golds == 4 else 3)
        assert flag.countdown == 6
    gold = p.hand[0]
    assert gold.cost == 0 and {a.modes for a in plays(state, gold.uid)} == {(0,), (1,)}
    enemy = put(state, 1, demo.FOOTMAN)                        # 1/2, the only enemy follower
    apply(state, PlayCard(gold.uid, modes=(1,)))
    assert enemy.fate == DESTROYED and flag.countdown == 5
    gold = p.hand[0]
    apply(state, PlayCard(gold.uid, modes=(0,)))
    assert len(p.hand) == 3                                    # 2 Golds left + the drawn card


def test_whirlpool_gunner():
    # Fanfare: summon a Flag and add a Gilded Goblet (restore 2). Rush. 3 cost 4/2.
    state = fresh_state()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 3)
    gunner = give(state, 0, sword.WHIRLPOOL_GUNNER)
    apply(state, PlayCard(gunner.uid))
    assert (gunner.atk, gunner.life) == (4, 2)
    assert count(p.field, FLAG) == 1 and [c.defn for c in p.hand] == [sword.GILDED_GOBLET]
    assert attacks_of(state, gunner.uid) == {enemy.uid}        # Rush: followers only
    p.leader_hp = 15
    set_pp(state, 0, 1)
    apply(state, PlayCard(p.hand[0].uid))
    assert p.leader_hp == 17 and p.pp == 0


def test_zeta_and_bea_crimson_and_blue():
    # Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush.
    state = fresh_state()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 5)
    zeta = give(state, 0, sword.ZETA_AND_BEA)
    apply(state, PlayCard(zeta.uid))                           # 5 PP: not Enhanced
    twin = p.field[-1]
    assert twin is not zeta and twin.defn == sword.ZETA_AND_BEA and p.pp == 1
    assert not twin.has(BANE) and not zeta.has(STORM)
    assert attacks_of(state, zeta.uid) == {enemy.uid} == attacks_of(state, twin.uid)

    # Enhanced with the field nearly full: no room for the twin, Storm still comes.
    state = fresh_state()
    p = state.players[0]
    for _ in range(4):
        put(state, 0, FLAG)
    set_pp(state, 0, 6)
    zeta = give(state, 0, sword.ZETA_AND_BEA)
    apply(state, PlayCard(zeta.uid))
    assert count(p.field, sword.ZETA_AND_BEA) == 1 and zeta.has(STORM) and p.pp == 0
    assert leader_uid(1) in attacks_of(state, zeta.uid)


def test_lage_dor():
    # Summon a Flag, 2 damage to all enemy followers; Enhance (6): 2 Flags, 4 damage.
    # Hits Aura followers (no selection); flags it summons are not advanced by it.
    state = fresh_state()
    p = state.players[0]
    old_flag = put(state, 0, FLAG)
    aura = put(state, 1, sword.BELTEZORE)                      # 2/12 Aura
    footman = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 6)
    card = give(state, 0, sword.LAGE_DOR)
    apply(state, PlayCard(card.uid))
    assert aura.life == 8 and footman.fate == DESTROYED and p.pp == 0
    assert old_flag.countdown == 6 and [f.countdown for f in sword.flags(p)] == [6, 7, 7]

    state = fresh_state()
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 5)
    card = give(state, 0, sword.LAGE_DOR)
    apply(state, PlayCard(card.uid))                           # 5 PP: not Enhanced
    assert giant.life == 3 and len(sword.flags(p)) == 1 and p.pp == 1


def test_roughwater_first_mate():
    # Fanfare: 3 damage to a selected enemy follower and summon a Flag. Evolve:
    # replicate the Fanfare. Super-Evolve only: Gilded Blade + Gilded Necklace at 0 cost.
    state = fresh_state()
    p = state.players[0]
    set_pp(state, 0, 5)
    mate = give(state, 0, sword.ROUGHWATER_FIRST_MATE)
    assert plays(state, mate.uid) == [PlayCard(mate.uid)]      # no enemy: still playable
    apply(state, PlayCard(mate.uid))
    assert len(sword.flags(p)) == 1 and (mate.atk, mate.life) == (3, 3)

    aura = put(state, 1, sword.BELTEZORE)
    giant = put(state, 1, demo.GIANT)
    unlock_evolution(state, 0)
    assert evolve_targets(state, mate.uid) == {(giant.uid,)}   # Aura can't be selected
    apply(state, Evolve(mate.uid, targets=(giant.uid,)))
    assert giant.life == 2 and aura.life == 12 and len(sword.flags(p)) == 2
    assert p.hand == []                                        # no loot on a plain evolve


def test_golden_knight_true_kings_blade():
    # Fanfare: Mode, pick 1: super-evolve itself / 4 damage to all enemy followers /
    # restore 4 to your leader. Enhance (8): all. Below 8 PP only one mode.
    state = fresh_state()
    p = state.players[0]
    giant, aura = put(state, 1, demo.GIANT), put(state, 1, sword.BELTEZORE)
    set_pp(state, 0, 7)
    knight = give(state, 0, sword.GOLDEN_KNIGHT)
    assert {a.modes for a in plays(state, knight.uid)} == {(0,), (1,), (2,)}
    apply(state, PlayCard(knight.uid, modes=(1,)))
    assert giant.life == 1 and aura.life == 8 and not knight.evolved and p.pp == 1
    assert (knight.atk, knight.life) == (6, 6) and attacks_of(state, knight.uid) == set()

    state = fresh_state()
    p = state.players[0]
    p.leader_hp = 10
    set_pp(state, 0, 6)
    knight = give(state, 0, sword.GOLDEN_KNIGHT)
    apply(state, PlayCard(knight.uid, modes=(2,)))
    assert p.leader_hp == 14 and not knight.evolved and p.pp == 0


def test_barbaros_rebellious_convict():
    # Fanfare: summon a Flag, then advance every allied Flag by 5. Storm. 7 cost 4/3.
    # With the field full after Barbaros enters, no Flag fits but the others still advance.
    state = fresh_state()
    p = state.players[0]
    a, b = put(state, 0, FLAG), put(state, 0, FLAG)
    b.countdown = 5
    put(state, 0, demo.FOOTMAN)
    put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 7)
    barbaros = give(state, 0, sword.BARBAROS)
    apply(state, PlayCard(barbaros.uid))
    assert (barbaros.atk, barbaros.life) == (4, 3)
    assert sword.flags(p) == [a] and a.countdown == 2 and b.fate == DESTROYED
    assert state.players[1].leader_hp == 18                    # the Flag's Last Words
    assert leader_uid(1) in attacks_of(state, barbaros.uid)    # Storm
    apply(state, Attack(barbaros.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 14


# =====================================================================================
# Other cards of the standard list
# =====================================================================================

def test_flashstep_quickblader():
    # Vanilla 1 cost 1/1 with Storm.
    assert not has_script(sword.FLASHSTEP_QUICKBLADER.card_id)
    state = fresh_state()
    set_pp(state, 0, 1)
    blader = give(state, 0, sword.FLASHSTEP_QUICKBLADER)
    apply(state, PlayCard(blader.uid))
    assert (blader.atk, blader.life, blader.keywords) == (1, 1, STORM)
    assert leader_uid(1) in attacks_of(state, blader.uid)
    apply(state, Attack(blader.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 19


def test_sharp_eared_operative():
    # Last Words: summon a Knight (0 cost 1/1 Officer). Evolve: 3 damage to a
    # selected enemy follower (fires on super-evolution too).
    state = fresh_state()
    p = state.players[0]
    unlock_evolution(state, 0)
    operative = put(state, 0, sword.SHARP_EARED_OPERATIVE)
    assert (operative.atk, operative.life) == (2, 1)
    wall = put(state, 1, WALL)
    apply(state, Evolve(operative.uid, super_=True, targets=(wall.uid,)))
    assert wall.life == 17
    E.destroy(state, operative, by_ability=False)              # (super-evolved: invincible to abilities now)
    resolve_queue(state)
    knight = p.field[-1]
    assert knight.defn == sword.KNIGHT and (knight.atk, knight.life) == (1, 1)
    assert E.has_trait(knight, sword.OFFICER)

    state = fresh_state()                                      # dies in combat
    p = state.players[0]
    operative = put(state, 0, sword.SHARP_EARED_OPERATIVE)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Attack(operative.uid, enemy.uid))
    assert operative.fate == DESTROYED and count(p.field, sword.KNIGHT) == 1


def test_severed_ties():
    # 5 damage to a selected enemy follower; if this card's cost is 3, add a Severed
    # Ties costing 1. A spell: needs a target (Aura can't be selected), advances Flags.
    state = fresh_state()
    p = state.players[0]
    flag = put(state, 0, FLAG)
    put(state, 1, sword.BELTEZORE)
    set_pp(state, 0, 3)
    ties = give(state, 0, sword.SEVERED_TIES)
    assert plays(state, ties.uid) == []
    giant = put(state, 1, demo.GIANT)
    assert plays(state, ties.uid) == [PlayCard(ties.uid, (giant.uid,))]
    apply(state, PlayCard(ties.uid, (giant.uid,)))
    assert giant.fate == DESTROYED and flag.countdown == 6
    copy = p.hand[-1]
    assert copy.defn == sword.SEVERED_TIES and copy.cost == 1

    state = fresh_state()                                      # cost changed to 2: no copy
    p = state.players[0]
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 3)
    ties = give(state, 0, sword.SEVERED_TIES)
    E.add_cost(ties, -1)
    apply(state, PlayCard(ties.uid, (giant.uid,)))
    assert giant.fate == DESTROYED and p.hand == [] and p.pp == 1


def test_unkei_goldbloom():
    # Fanfare: banish a selected enemy follower, add a Glittering Gold. Super-Evolve
    # only: Crest (Countdown 4, a Gold at the end of your turn). 5 cost 2/4.
    state = fresh_state()
    p = state.players[0]
    aura = put(state, 1, sword.BELTEZORE)
    spy = put(state, 1, sword.SHARP_EARED_OPERATIVE)           # Last Words: summon a Knight
    set_pp(state, 0, 5)
    unkei = give(state, 0, sword.UNKEI)
    assert plays(state, unkei.uid) == [PlayCard(unkei.uid, (spy.uid,))]   # Aura can't be selected
    apply(state, PlayCard(unkei.uid, (spy.uid,)))
    assert spy.fate == BANISHED and state.players[1].field == [aura]       # no Last Words
    assert state.players[1].shadows == 0 and [c.defn for c in p.hand] == [GOLD]
    assert (unkei.atk, unkei.life) == (2, 4)
    unlock_evolution(state, 0)
    apply(state, Evolve(unkei.uid))                            # plain evolve: no crest
    assert E.leader_area_card(state, 0, sword.UNKEI_CREST) is None

    state = fresh_state()
    p = state.players[0]
    unlock_evolution(state, 0)
    unkei = put(state, 0, sword.UNKEI)
    apply(state, Evolve(unkei.uid, super_=True))
    crest = E.leader_area_card(state, 0, sword.UNKEI_CREST)
    assert crest is not None and crest.countdown == 4 and p.hand == []
    apply(state, EndTurn())
    assert [c.defn for c in p.hand] == [GOLD]                  # end of your turn
    hand = len(p.hand)
    apply(state, EndTurn())                                    # opponent's turn end: nothing
    assert len(p.hand) == hand + 1 and crest.countdown == 3    # only the turn draw
    second = put(state, 0, sword.UNKEI)                        # same-name crest: no second one
    apply(state, Evolve(second.uid, super_=True))
    assert [c for c in p.leader_area if c.defn == sword.UNKEI_CREST] == [crest]
    assert crest.countdown == 3


def test_beltezore_valorous_revenant():
    # Storm, Bane, Ward, Aura; can attack 3 times per turn. 10 cost 2/12.
    state = fresh_state()
    opp = state.players[1]
    set_pp(state, 0, 10)
    beltezore = give(state, 0, sword.BELTEZORE)
    apply(state, PlayCard(beltezore.uid))
    assert (beltezore.atk, beltezore.life) == (2, 12)
    assert beltezore.keywords == WARD | STORM | BANE | AURA
    for _ in range(3):
        assert leader_uid(1) in attacks_of(state, beltezore.uid)
        apply(state, Attack(beltezore.uid, leader_uid(1)))
    assert opp.leader_hp == 14 and attacks_of(state, beltezore.uid) == set()

    apply(state, EndTurn())                                    # opponent's turn
    raider = put(state, 1, demo.RAIDER)                        # 2/1 Storm
    assert attacks_of(state, raider.uid) == {beltezore.uid}    # Ward
    set_pp(state, 1, 5)
    ties = give(state, 1, sword.SEVERED_TIES)
    unkei = give(state, 1, sword.UNKEI)
    assert plays(state, ties.uid) == []                        # Aura: not selectable
    assert plays(state, unkei.uid) == [PlayCard(unkei.uid)]

    apply(state, EndTurn())
    wall = put(state, 1, WALL)
    assert wall.uid in attacks_of(state, beltezore.uid)
    apply(state, Attack(beltezore.uid, wall.uid))              # Bane
    assert wall.fate == DESTROYED


# =====================================================================================
# Free-slot cards
# =====================================================================================

def test_orchestrated_silence():
    # Add a Steelclad Knight (1 cost 2/2 Officer) with Rush; Rally (10): add 2.
    for rally, knights in ((9, 1), (10, 2)):
        state = fresh_state()
        p = state.players[0]
        p.rally = rally
        set_pp(state, 0, 1)
        card = give(state, 0, sword.ORCHESTRATED_SILENCE)
        apply(state, PlayCard(card.uid))
        assert count(p.hand, sword.STEELCLAD_KNIGHT) == knights
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 1)
    knight = p.hand[0]
    apply(state, PlayCard(knight.uid))                         # Rush kept on the field
    assert (knight.atk, knight.life) == (2, 2) and E.has_trait(knight, sword.OFFICER)
    assert attacks_of(state, knight.uid) == {enemy.uid}


def test_ruthless_eld_sword():
    # Mode: draw a card / 3 damage to a random enemy follower; Enhance (3): both.
    state = fresh_state()
    p = state.players[0]
    set_pp(state, 0, 2)
    card = give(state, 0, sword.RUTHLESS_ELD_SWORD)
    assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}   # 2 PP: no Enhance
    giant = put(state, 1, demo.GIANT)
    apply(state, PlayCard(card.uid, modes=(1,)))
    assert giant.life == 2 and p.hand == [] and p.pp == 1

    state = fresh_state()
    p = state.players[0]
    flag = put(state, 0, FLAG)
    set_pp(state, 0, 3)
    card = give(state, 0, sword.RUTHLESS_ELD_SWORD)
    assert plays(state, card.uid) == [PlayCard(card.uid, modes=(0, 1))]
    apply(state, PlayCard(card.uid, modes=(0, 1)))             # no enemy follower: draw only
    assert len(p.hand) == 1 and p.pp == 0 and flag.countdown == 6


def test_slice_of_domesticity():
    # Mode: 4 damage to a random enemy follower / restore 2; with 2+ allied cards on
    # the field (amulets count), both.
    state = fresh_state()
    p = state.players[0]
    put(state, 0, FLAG)
    set_pp(state, 0, 2)
    card = give(state, 0, sword.SLICE_OF_DOMESTICITY)
    assert {a.modes for a in plays(state, card.uid)} == {(0,), (1,)}
    put(state, 0, FLAG)
    assert plays(state, card.uid) == [PlayCard(card.uid, modes=(0, 1))]
    p.leader_hp = 15
    wall = put(state, 1, WALL)
    apply(state, PlayCard(card.uid, modes=(0, 1)))
    assert wall.life == 16 and p.leader_hp == 17


def test_mordred_illusory_lion():
    # Storm. Evolve: summon an Arthur, Staunch Dragon (3 cost 2/3 Ward); also on super-evolution.
    state = fresh_state()
    p = state.players[0]
    set_pp(state, 0, 3)
    mordred = give(state, 0, sword.MORDRED)
    apply(state, PlayCard(mordred.uid))
    assert (mordred.atk, mordred.life) == (2, 1)
    assert leader_uid(1) in attacks_of(state, mordred.uid)
    unlock_evolution(state, 0)
    apply(state, Evolve(mordred.uid, super_=True))
    arthur = p.field[-1]
    assert arthur.defn == sword.ARTHUR and (arthur.atk, arthur.life) == (2, 3) and arthur.has(WARD)


def test_mars_conflagrant_commander():
    # Fanfare: 3 Knights. Storm, Bane. Allied Officer followers entering get +2/+0
    # and Rush, Mars +1/+0. Super-Evolve only: summon a Knight. 8 cost 1/5.
    state = fresh_state()
    p = state.players[0]
    set_pp(state, 0, 8)
    mars = give(state, 0, sword.MARS)
    apply(state, PlayCard(mars.uid))
    assert mars.keywords == STORM | BANE and mars.life == 5 and mars.atk == 1 + 3
    assert leader_uid(1) in attacks_of(state, mars.uid)
    apply(state, EndTurn())
    apply(state, EndTurn())
    p.hand.clear()
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 1)
    knight = give(state, 0, sword.STEELCLAD_KNIGHT)            # played from hand
    apply(state, PlayCard(knight.uid))
    assert (knight.atk, knight.life) == (4, 2) and enemy.uid in attacks_of(state, knight.uid)
    assert mars.atk == 5
    E.banish(state, knight)                                    # make room on the field
    unlock_evolution(state, 0)
    apply(state, Evolve(mars.uid))                             # plain evolve: no Knight
    assert count(p.field, sword.KNIGHT) == 3 and len(p.field) == 4 and mars.atk == 7


# =====================================================================================
# Printed stats and keywords of every card of the list and the tokens they make
# =====================================================================================

def test_card_stats_and_keywords():
    expected = {
        sword.YIDMETRA: (2, 1, 2, ()), sword.OPEN_SEA_SCOUT: (2, 2, 2, ()),
        sword.SPLENDOR_OF_THE_GOLDBLOOM: (3, 0, 0, ()), sword.WHIRLPOOL_GUNNER: (3, 4, 2, (RUSH,)),
        sword.ZETA_AND_BEA: (4, 3, 2, (RUSH,)), sword.LAGE_DOR: (4, 0, 0, ()),
        sword.ROUGHWATER_FIRST_MATE: (5, 3, 3, ()), sword.GOLDEN_KNIGHT: (6, 6, 6, ()),
        sword.BARBAROS: (7, 4, 3, (STORM,)), sword.FLASHSTEP_QUICKBLADER: (1, 1, 1, (STORM,)),
        sword.SHARP_EARED_OPERATIVE: (2, 2, 1, ()), sword.SEVERED_TIES: (3, 0, 0, ()),
        sword.UNKEI: (5, 2, 4, ()), sword.BELTEZORE: (10, 2, 12, (STORM, BANE, WARD, AURA)),
        sword.ORCHESTRATED_SILENCE: (1, 0, 0, ()), sword.RUTHLESS_ELD_SWORD: (1, 0, 0, ()),
        sword.SLICE_OF_DOMESTICITY: (2, 0, 0, ()), sword.MORDRED: (3, 2, 1, (STORM,)),
        sword.MARS: (8, 1, 5, (STORM, BANE)),
        # tokens
        sword.STEELCLAD_KNIGHT: (1, 2, 2, ()), sword.KNIGHT: (0, 1, 1, ()),
        sword.DEPTHS_OF_THE_ELD_SWORD: (0, 0, 0, ()), FLAG: (1, 0, 0, ()),
        sword.GILDED_BLADE: (1, 0, 0, ()), sword.GILDED_GOBLET: (1, 0, 0, ()),
        sword.GILDED_BOOTS: (1, 0, 0, ()), sword.GILDED_NECKLACE: (1, 0, 0, ()),
        GOLD: (0, 0, 0, ()), sword.ARTHUR: (3, 2, 3, (WARD,)),
    }
    for defn, (cost, atk, life, kws) in expected.items():
        want = Keyword.NONE
        for k in kws:
            want |= k
        assert (defn.cost, defn.atk, defn.life, defn.keywords) == (cost, atk, life, want), defn.name
    spells = [sword.SPLENDOR_OF_THE_GOLDBLOOM, sword.LAGE_DOR, sword.SEVERED_TIES,
              sword.ORCHESTRATED_SILENCE, sword.RUTHLESS_ELD_SWORD, sword.SLICE_OF_DOMESTICITY,
              sword.DEPTHS_OF_THE_ELD_SWORD, sword.GILDED_BLADE, sword.GILDED_GOBLET,
              sword.GILDED_BOOTS, sword.GILDED_NECKLACE, GOLD]
    assert all(d.is_spell for d in spells)
    assert FLAG.type == CardType.COUNTDOWN_AMULET and FLAG.countdown == 7
    assert sword.UNKEI_CREST.countdown == 4
    assert sword.STEELCLAD_KNIGHT.has_trait(sword.OFFICER) and sword.KNIGHT.has_trait(sword.OFFICER)
