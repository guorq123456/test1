"""Pirate Sword cards and tokens."""
from svsim.cards import demo, sword
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Keyword
from svsim.core.state import BANISHED, DESTROYED, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution

RUSH_BANE = Keyword.RUSH | Keyword.BANE


def test_open_sea_scout_flag_and_its_countdown():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 2)
    scout = give(state, 0, sword.OPEN_SEA_SCOUT)
    apply(state, PlayCard(scout.uid))
    flag = p.field[-1]
    assert flag.defn == sword.DREAD_PIRATES_FLAG and flag.countdown == 7
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert flag.countdown == 6                       # ticks at the start of its controller's turn


def test_open_sea_scout_evolve_adds_gilded_boots():
    state = start()
    unlock_evolution(state, 0)
    scout = put(state, 0, sword.OPEN_SEA_SCOUT)
    apply(state, Evolve(scout.uid))
    assert state.players[0].hand[-1].defn == sword.GILDED_BOOTS


def test_whirlpool_gunner():
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 3)
    gunner = give(state, 0, sword.WHIRLPOOL_GUNNER)
    apply(state, PlayCard(gunner.uid))
    assert count(p.field, sword.DREAD_PIRATES_FLAG) == 1
    assert p.hand[-1].defn == sword.GILDED_GOBLET
    assert Attack(gunner.uid, enemy.uid) in legal_actions(state)     # Rush


def test_spells_tick_flags_and_flags_burst():
    state = start()
    for _ in range(3):
        put(state, 0, sword.DREAD_PIRATES_FLAG).countdown = 1
    set_pp(state, 0, 1)
    goblet = give(state, 0, sword.GILDED_GOBLET)
    apply(state, PlayCard(goblet.uid))
    assert sword.flags(state.players[0]) == [] and state.players[1].leader_hp == 14


def test_barbaros_advances_every_flag_by_five():
    state = start()
    a, b = put(state, 0, sword.DREAD_PIRATES_FLAG), put(state, 0, sword.DREAD_PIRATES_FLAG)
    b.countdown = 4
    set_pp(state, 0, 7)
    barbaros = give(state, 0, sword.BARBAROS)
    apply(state, PlayCard(barbaros.uid))
    assert b.fate == DESTROYED and state.players[1].leader_hp == 18
    assert [c.countdown for c in sword.flags(state.players[0])] == [2, 2]  # old one and new one
    assert Attack(barbaros.uid, leader_uid(1)) in legal_actions(state)    # Storm


def test_severed_ties_returns_a_one_cost_copy_once():
    state = start()
    p = state.players[0]
    first, second = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)   # 5/5
    set_pp(state, 0, 4)
    ties = give(state, 0, sword.SEVERED_TIES)
    apply(state, PlayCard(ties.uid, (first.uid,)))
    copy = p.hand[-1]
    assert first.fate == DESTROYED and copy.defn == sword.SEVERED_TIES and copy.cost == 1
    apply(state, PlayCard(copy.uid, (second.uid,)))
    assert second.fate == DESTROYED and count(p.hand, sword.SEVERED_TIES) == 0 and p.pp == 0


def test_splendor_of_the_goldbloom():
    for pp, golds in ((3, 2), (5, 4)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        set_pp(state, 0, pp)
        card = give(state, 0, sword.SPLENDOR_OF_THE_GOLDBLOOM)
        apply(state, PlayCard(card.uid))
        assert count(p.hand, sword.GLITTERING_GOLD) == golds and p.pp == 0


def test_glittering_gold_modes():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 0)
    enemy = put(state, 1, demo.RAIDER)               # 2/1
    gold = give(state, 0, sword.GLITTERING_GOLD)
    apply(state, PlayCard(gold.uid, modes=(1,)))
    assert enemy.fate == DESTROYED
    gold = give(state, 0, sword.GLITTERING_GOLD)
    apply(state, PlayCard(gold.uid, modes=(0,)))
    assert len(p.hand) == 1                          # drew a card


def test_zeta_and_bea():
    state = start()
    p = state.players[0]
    set_pp(state, 0, 4)
    zeta = give(state, 0, sword.ZETA_AND_BEA)
    apply(state, PlayCard(zeta.uid))
    twin = p.field[-1]
    assert twin is not zeta and twin.defn == sword.ZETA_AND_BEA
    assert not twin.has(Keyword.BANE) and not zeta.has(Keyword.STORM)

    state = start()
    p = state.players[0]
    set_pp(state, 0, 6)
    zeta = give(state, 0, sword.ZETA_AND_BEA)
    apply(state, PlayCard(zeta.uid))                 # Enhance (6)
    twin = p.field[-1]
    assert twin.keywords & RUSH_BANE == RUSH_BANE and zeta.has(Keyword.STORM)
    assert Attack(zeta.uid, leader_uid(1)) in legal_actions(state)
    assert p.pp == 0


def test_lage_dor():
    for pp, flags, damage in ((4, 1, 2), (6, 2, 4)):
        state = start()
        enemy = put(state, 1, demo.GIANT)            # 5/5
        set_pp(state, 0, pp)
        card = give(state, 0, sword.LAGE_DOR)
        apply(state, PlayCard(card.uid))
        assert len(sword.flags(state.players[0])) == flags and enemy.life == 5 - damage


def test_unkei_banishes_and_gives_gold():
    state = start()
    bomber = put(state, 1, demo.BOMBER)              # its Last Words would hit player 0
    set_pp(state, 0, 5)
    unkei = give(state, 0, sword.UNKEI)
    apply(state, PlayCard(unkei.uid, (bomber.uid,)))
    assert bomber.fate == BANISHED and state.players[1].shadows == 0
    assert state.players[0].leader_hp == 20
    assert state.players[0].hand[-1].defn == sword.GLITTERING_GOLD


def test_unkei_crest_gives_four_golds_then_expires():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    unkei = put(state, 0, sword.UNKEI)
    apply(state, Evolve(unkei.uid, super_=True))
    crest = E.leader_area_card(state, 0, sword.UNKEI_CREST)
    assert crest is not None and crest.countdown == 4
    golds = 0
    for _ in range(4):
        p.hand.clear()
        apply(state, EndTurn())                      # end of own turn: a Gold
        golds += count(p.hand, sword.GLITTERING_GOLD)
        apply(state, EndTurn())                      # own turn starts: countdown ticks
    assert golds == 4 and E.leader_area_card(state, 0, sword.UNKEI_CREST) is None


def test_roughwater_first_mate():
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    e1, e2 = put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.SHIELDBEARER)   # 1/3
    set_pp(state, 0, 5)
    mate = give(state, 0, sword.ROUGHWATER_FIRST_MATE)
    apply(state, PlayCard(mate.uid, (e1.uid,)))
    assert e1.fate == DESTROYED and len(sword.flags(p)) == 1
    apply(state, Evolve(mate.uid, super_=True, targets=(e2.uid,)))   # Evolve + Super-Evolve
    assert e2.fate == DESTROYED and len(sword.flags(p)) == 2
    blade, necklace = p.hand[-2:]
    assert (blade.defn, blade.cost) == (sword.GILDED_BLADE, 0)
    assert (necklace.defn, necklace.cost) == (sword.GILDED_NECKLACE, 0)


def test_golden_knight_modes():
    state = start()
    set_pp(state, 0, 6)
    knight = give(state, 0, sword.GOLDEN_KNIGHT)
    assert {a.modes for a in plays(state, knight.uid)} == {(0,), (1,), (2,)}
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, PlayCard(knight.uid, modes=(0,)))
    assert knight.super_evolved and (knight.atk, knight.life) == (9, 9)
    assert Attack(knight.uid, enemy.uid) in legal_actions(state)
    assert state.players[0].sep == 2                 # effect evolution costs no points


def test_golden_knight_enhanced_activates_every_mode():
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    enemy = put(state, 1, demo.GIANT)                # 5/5
    set_pp(state, 0, 8)
    knight = give(state, 0, sword.GOLDEN_KNIGHT)
    assert plays(state, knight.uid) == [PlayCard(knight.uid, modes=(0, 1, 2))]
    apply(state, PlayCard(knight.uid, modes=(0, 1, 2)))
    assert knight.super_evolved and enemy.life == 1 and p.leader_hp == 14


def test_orchestrated_silence_and_rally():
    for rally, knights in ((0, 1), (10, 2)):
        state = start()
        p = state.players[0]
        p.hand.clear()
        p.rally = rally
        set_pp(state, 0, 1)
        card = give(state, 0, sword.ORCHESTRATED_SILENCE)
        apply(state, PlayCard(card.uid))
        assert count(p.hand, sword.STEELCLAD_KNIGHT) == knights
        assert all(c.has(Keyword.RUSH) for c in p.hand)


def test_yidmetra_and_enhanced_depths_raise_faith():
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    p = state.players[0]
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    set_pp(state, 0, 2)
    yidmetra = give(state, 0, sword.YIDMETRA)
    apply(state, PlayCard(yidmetra.uid))
    depths = p.hand[-1]
    assert depths.defn == sword.DEPTHS_OF_THE_ELD_SWORD
    enemy = put(state, 1, demo.GIANT)                # 5/5
    set_pp(state, 0, 1)
    apply(state, PlayCard(depths.uid, (enemy.uid,)))  # Enhance (1): 3 damage
    assert enemy.life == 2 and faith.counters["value"] == 1


def test_yidmetra_evolve_spends_five_faith_for_a_buff_ability():
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    E.counters(faith)["value"] = 6
    unlock_evolution(state, 0)
    yidmetra = put(state, 0, sword.YIDMETRA)
    ally = put(state, 0, demo.FOOTMAN)               # 1/2
    apply(state, Evolve(yidmetra.uid))
    assert faith.counters == {"value": 1, "buffs": 1}
    set_pp(state, 0, 5)
    card = give(state, 0, sword.SPLENDOR_OF_THE_GOLDBLOOM)   # Enhanced at 5 PP
    apply(state, PlayCard(card.uid))
    assert (ally.atk, ally.life) == (2, 3) and (yidmetra.atk, yidmetra.life) == (4, 5)
    assert faith.counters["value"] == 2


def test_yidmetra_evolve_without_five_faith_does_nothing():
    """Confirmed by a player: below 5 faith, nothing happens."""
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    E.counters(faith)["value"] = 4
    unlock_evolution(state, 0)
    yidmetra = put(state, 0, sword.YIDMETRA)
    apply(state, Evolve(yidmetra.uid))
    assert faith.counters == {"value": 4}


def test_yidmetra_buff_abilities_stack():
    """Confirmed by a player: two evolved Yidmetras give +2/+2 per Enhanced card."""
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    E.counters(faith)["value"] = 10
    unlock_evolution(state, 0)
    first, second = put(state, 0, sword.YIDMETRA), put(state, 0, sword.YIDMETRA)
    apply(state, Evolve(first.uid))
    apply(state, EndTurn())
    apply(state, EndTurn())                          # one point evolution per turn
    apply(state, Evolve(second.uid))
    assert faith.counters == {"value": 0, "buffs": 2}
    ally = put(state, 0, demo.FOOTMAN)               # 1/2
    set_pp(state, 0, 5)
    card = give(state, 0, sword.SPLENDOR_OF_THE_GOLDBLOOM)
    apply(state, PlayCard(card.uid))
    assert (ally.atk, ally.life) == (3, 4)


def test_faith_buff_includes_the_enhanced_follower_itself():
    """Confirmed by a player: the Enhanced follower that triggers the buff gets it too."""
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39)
    faith = E.leader_area_card(state, 0, sword.ELD_SWORD_FAITH)
    E.counters(faith)["buffs"] = 1
    set_pp(state, 0, 6)
    zeta = give(state, 0, sword.ZETA_AND_BEA)
    apply(state, PlayCard(zeta.uid))                 # Enhance (6)
    twin = state.players[0].field[-1]
    assert (zeta.atk, zeta.life) == (4, 3) and (twin.atk, twin.life) == (4, 3)


def test_gilded_tokens():
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 4)
    fresh = put(state, 0, demo.FOOTMAN, ready=False)
    enemy = put(state, 1, demo.FOOTMAN)
    boots = give(state, 0, sword.GILDED_BOOTS)
    apply(state, PlayCard(boots.uid, (fresh.uid,)))
    assert fresh.atk == 2 and Attack(fresh.uid, enemy.uid) in legal_actions(state)
    necklace = give(state, 0, sword.GILDED_NECKLACE)
    apply(state, PlayCard(necklace.uid, (fresh.uid,)))
    assert fresh.life == 3 and fresh.has(Keyword.WARD)
    blade = give(state, 0, sword.GILDED_BLADE)
    apply(state, PlayCard(blade.uid, (leader_uid(1),)))
    assert state.players[1].leader_hp == 19
    p.leader_hp = 15
    goblet = give(state, 0, sword.GILDED_GOBLET)
    apply(state, PlayCard(goblet.uid))
    assert p.leader_hp == 17 and p.pp == 0
