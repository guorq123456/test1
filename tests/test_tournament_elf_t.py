"""Tournament deck audit: 连击妖 (elf-t), Combo Forestcraft.

One regression test per card of the tournament list (core cards first, then the
other cards of the standard list, then the free-slot cards), plus one combined
test for printed stats and keywords. Each test builds a small position and
plays it through legal actions. Comments paraphrase the official card text.
"""
import importlib

from svsim.cards import demo, forest, neutral
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import CardType, Keyword
from svsim.core.state import leader_uid

from helpers import count, give, put, set_pp, start, unlock_evolution

importlib.import_module("svsim.cards.library")     # register every card script

QUAKE_GOLIATH = card(10001130)                     # neutral 4-cost 4/5 Ward, no ability


# --- helpers ---------------------------------------------------------------------------------

def fresh(first: int = 0, deck=None):
    """A started game, player 0 to act on turn 1, both hands empty."""
    state = start(first=first, deck=deck)
    for p in state.players:
        p.hand.clear()
    return state


def act(state, action):
    """Apply an action, checking that it is legal."""
    assert action in legal_actions(state), action
    apply(state, action)


def play(state, inst, targets=(), modes=()):
    act(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def evolve(state, inst, super_=False, targets=(), modes=()):
    act(state, Evolve(inst.uid, super_, tuple(targets), tuple(modes)))


def play_options(state, inst):
    return [a for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == inst.uid]


def evolve_options(state, inst, super_=False):
    return [a for a in legal_actions(state)
            if isinstance(a, Evolve) and a.uid == inst.uid and a.super_ == super_]


def can_attack(state, attacker, target_uid) -> bool:
    return Attack(attacker.uid, target_uid) in legal_actions(state)


def bounties(state, n: int):
    """Play n zero-cost Deepwood Bounty spells to build Combo."""
    for _ in range(n):
        play(state, give(state, 0, forest.DEEPWOOD_BOUNTY))


def on_field(state, inst) -> bool:
    return state.on_field(inst.uid) is inst


def end_turn(state):
    act(state, EndTurn())


# =============================================================================================
# Core cards
# =============================================================================================

def test_world_of_games():
    # Countdown (5). Whenever you play another card, if another card on the field (either
    # side) has the same base cost as it, advance the count by 1. Last Words: draw 2.
    # Q&A: with only an enemy 4-cost on the field, a 4-cost spell that destroys it still
    # advances the count (5 -> 4).
    state = fresh()
    p = state.players[0]
    wog = put(state, 0, neutral.WORLD_OF_GAMES)
    assert wog.countdown == 5
    set_pp(state, 0, 10)

    # Base cost, not current cost: a Crimson Incense reduced to 3 is still a 4-cost card.
    miroku = put(state, 1, forest.MIROKU)                # enemy 3-cost
    cheap = give(state, 0, forest.CRIMSON_INCENSE)
    E.add_cost(cheap, -1)
    play(state, cheap, [miroku.uid])
    assert not on_field(state, miroku) and wog.countdown == 5

    # The official Q&A position: an enemy 4-cost destroyed by the 4-cost spell itself.
    goliath = put(state, 1, QUAKE_GOLIATH)
    incense = give(state, 0, forest.CRIMSON_INCENSE)
    play(state, incense, [goliath.uid])
    assert not on_field(state, goliath) and wog.countdown == 4

    # A 2-cost follower with no other 2-cost card on the field: no advance.
    set_pp(state, 0, 10)
    fencer = give(state, 0, forest.VIREWIND_FENCER)
    play(state, fencer)
    assert wog.countdown == 4
    # A second 2-cost follower: the first one matches.
    lieutenant = give(state, 0, forest.VIRID_LIEUTENANT)
    play(state, lieutenant)
    assert wog.countdown == 3
    # A 1-cost card: the amulet itself is another 1-cost card on the field.
    play(state, give(state, 0, forest.SPROUTING_INITIATE))
    assert wog.countdown == 2

    # Only its controller's plays count.
    end_turn(state)
    set_pp(state, 1, 1)
    play(state, give(state, 1, forest.SPROUTING_INITIATE))
    assert wog.countdown == 2
    end_turn(state)                                      # own turn start: 2 -> 1
    assert wog.countdown == 1

    # Last Words when the count runs out: draw 2.
    set_pp(state, 0, 1)
    p.hand.clear()
    play(state, give(state, 0, forest.MOELLE))           # 1-cost, empty hand: draws 1 itself
    assert not on_field(state, wog)
    assert len(p.hand) == 3                              # Moelle's draw + 2 from Last Words


def test_sprouting_initiate():
    # Fanfare: Combo (3) - draw a card. Rush.
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    first = give(state, 0, forest.SPROUTING_INITIATE)
    set_pp(state, 0, 10)
    play(state, first)                                   # Combo 1
    assert len(p.hand) == 0
    bounties(state, 1)                                   # Combo 2
    third = give(state, 0, forest.SPROUTING_INITIATE)
    play(state, third)                                   # Combo 3: draws
    assert len(p.hand) == 1 and p.hand[0].defn == demo.FOOTMAN
    # Rush: may attack a follower but not the leader on the turn it enters.
    assert can_attack(state, third, enemy.uid)
    assert not can_attack(state, third, leader_uid(1))


def test_virid_lieutenant():
    # Fanfare: Combo (3) - draw 2. Evolve: select another allied follower, +1/+1 and Rush.
    # Evolve abilities also activate on a super-evolution with points.
    for super_ in (False, True):
        state = fresh()
        p = state.players[0]
        unlock_evolution(state, 0)
        set_pp(state, 0, 10)
        enemy = put(state, 1, demo.GIANT)
        lead = give(state, 0, forest.VIRID_LIEUTENANT)
        play(state, lead)                                # Combo 1: no draw
        assert len(p.hand) == 0
        bounties(state, 1)
        ally = give(state, 0, forest.VIRID_LIEUTENANT)
        play(state, ally)                                # Combo 3: draw 2
        assert len(p.hand) == 2
        assert not can_attack(state, ally, enemy.uid)   # entered this turn, no Rush yet
        options = evolve_options(state, lead, super_)
        assert Evolve(lead.uid, super_, (ally.uid,), ()) in options
        assert all(lead.uid not in a.targets for a in options)    # "another" follower
        evolve(state, lead, super_, [ally.uid])
        assert (ally.atk, ally.life) == (2, 4) and ally.has(Keyword.RUSH)
        assert can_attack(state, ally, enemy.uid)


def test_miroku_swarmpetal():
    # Fanfare: choose 1 mode: (1) add 2 Fairies to hand, (2) recover 2 PP, (3) 3 damage split
    # between enemy followers (oldest first, each up to its defense). Evolve: activate the
    # Fanfare again (a new mode choice), also on super-evolution.
    # (1) two Fairies (1-cost 1/1 Rush tokens)
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 3)
    miroku = give(state, 0, forest.MIROKU)
    assert {a.modes for a in play_options(state, miroku)} == {(0,), (1,), (2,)}
    play(state, miroku, modes=(0,))
    assert count(p.hand, forest.FAIRY) == 2
    fairy = p.hand[0]
    assert (fairy.defn.cost, fairy.atk, fairy.life) == (1, 1, 1) and fairy.has(Keyword.RUSH)

    # (2) recover 2 PP
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    play(state, give(state, 0, forest.MIROKU), modes=(1,))
    assert p.pp == 9                                     # 10 - 3 + 2

    # (3) split 3 damage, oldest enemy follower first
    state = fresh()
    set_pp(state, 0, 3)
    wisp = put(state, 1, demo.WISP)                      # 1/1, oldest
    wall = put(state, 1, demo.SHIELDBEARER)              # 1/3
    footman = put(state, 1, demo.FOOTMAN)                # 1/2, newest
    play(state, give(state, 0, forest.MIROKU), modes=(2,))
    assert not on_field(state, wisp) and wall.life == 1 and footman.life == 2

    # Evolve and super-evolve replicate the Fanfare with a fresh choice.
    for super_ in (False, True):
        state = fresh()
        p = state.players[0]
        unlock_evolution(state, 0)
        set_pp(state, 0, 5)
        miroku = give(state, 0, forest.MIROKU)
        play(state, miroku, modes=(1,))                  # 5 - 3 + 2 = 4
        assert p.pp == 4
        assert {a.modes for a in evolve_options(state, miroku, super_)} == {(0,), (1,), (2,)}
        evolve(state, miroku, super_, modes=(0,))
        assert count(p.hand, forest.FAIRY) == 2


def test_magachiyo_aromatic_convict():
    # Fanfare: select an enemy follower, 4 damage. Combo (3): 4 damage to all enemy followers
    # instead. Super-Evolve: gain Storm (a plain evolution does not).
    state = fresh()
    set_pp(state, 0, 10)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    mag = give(state, 0, forest.MAGACHIYO)
    assert {o.targets for o in play_options(state, mag)} == {(a.uid,), (b.uid,)}
    play(state, mag, [a.uid])
    assert (a.life, b.life) == (1, 5)

    state = fresh()
    set_pp(state, 0, 10)
    a, b = put(state, 1, demo.GIANT), put(state, 1, demo.GIANT)
    shade = put(state, 1, demo.SHADE)                    # Ambush: not selectable, still hit
    bounties(state, 2)
    mag = give(state, 0, forest.MAGACHIYO)
    play(state, mag, play_options(state, mag)[0].targets)
    assert (a.life, b.life) == (1, 1) and not on_field(state, shade)

    for super_, storm in ((False, False), (True, True)):
        state = fresh()
        unlock_evolution(state, 0)
        set_pp(state, 0, 3)
        mag = give(state, 0, forest.MAGACHIYO)
        play(state, mag)
        evolve(state, mag, super_)
        assert mag.has(Keyword.STORM) == storm
        assert can_attack(state, mag, leader_uid(1)) == storm


def test_thestae_anathema_of_distortion():
    # Fanfare: select an enemy follower, give it -0/-X (X = this follower's attack); increase
    # your Combo by 1. Evolve: gain Crest: Thestae (Countdown 3; at the end of your turn,
    # Combo (3) - give all followers in your deck +1/+1).
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    giant = put(state, 1, demo.GIANT)
    thestae = give(state, 0, forest.THESTAE)
    play(state, thestae, [giant.uid])                    # first card of the turn
    assert (giant.atk, giant.life, giant.max_life) == (5, 2, 2)
    assert p.combo == 2                                  # 1 card played + 1
    play(state, give(state, 0, forest.SPROUTING_INITIATE))   # the 2nd card reaches Combo (3)
    assert len(p.hand) == 1

    # -0/-X is not damage: Barrier doesn't stop it. With no enemy follower, Combo still +1.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    angel = put(state, 1, demo.ANGEL)                    # 2/3 Barrier
    play(state, give(state, 0, forest.THESTAE), [angel.uid])
    assert not on_field(state, angel)
    play(state, give(state, 0, forest.THESTAE))          # no enemy follower left
    assert p.combo == 4

    # X follows its current attack.
    state = fresh()
    set_pp(state, 0, 10)
    giant = put(state, 1, demo.GIANT)
    thestae = give(state, 0, forest.THESTAE)
    E.buff(state, thestae, 1, 1)                         # a 4/4 Thestae in hand
    play(state, thestae, [giant.uid])
    assert giant.life == 1

    # Evolve: the crest; its end-of-turn buff needs Combo (3); it lasts 3 of your turns.
    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 4)
    thestae = give(state, 0, forest.THESTAE)
    play(state, thestae)                                 # Combo 2 (1 + 1)
    evolve(state, thestae)
    crest = E.leader_area_card(state, 0, forest.THESTAE_CREST)
    assert crest is not None and crest.countdown == 3
    end_turn(state)                                      # Combo 2: nothing
    assert all((c.atk, c.life) == (1, 2) for c in p.deck)
    end_turn(state)
    assert crest.countdown == 2
    p.hand.clear()
    bounties(state, 3)
    end_turn(state)
    assert all((c.atk, c.life) == (2, 3) for c in p.deck)
    end_turn(state)
    assert crest.countdown == 1
    p.hand.clear()
    bounties(state, 3)
    end_turn(state)
    assert all((c.atk, c.life) == (3, 4) for c in p.deck)
    end_turn(state)                                      # start of the 4th turn: gone
    assert E.leader_area_card(state, 0, forest.THESTAE_CREST) is None


def test_setus_and_maisha_bladerights():
    # Fanfare: select an enemy follower and destroy it; give all OTHER allied followers +1/+1.
    # Storm, Ward.
    state = fresh()
    set_pp(state, 0, 7)
    giant = put(state, 1, demo.GIANT)
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    setus = give(state, 0, forest.SETUS_AND_MAISHA)
    play(state, setus, [giant.uid])
    assert not on_field(state, giant)
    assert (a.atk, a.life) == (2, 3) and (b.atk, b.life) == (2, 3)
    assert (setus.atk, setus.life) == (4, 6)
    assert setus.has(Keyword.WARD) and setus.has(Keyword.STORM)
    assert can_attack(state, setus, leader_uid(1))


# =============================================================================================
# Other cards of the standard list
# =============================================================================================

def test_sathanid_eld_lance():
    # Faith (placed at match start): starts at 0, +1 whenever an allied follower evolves.
    # Fanfare: reduce the faith by 10 to add a Depths of the Eld Lance (1-cost spell: evolve
    # an unevolved allied follower) and give the faith "whenever an allied follower evolves,
    # 1 damage to the enemy leader". Drain.
    deck = [forest.SATHANID] + [demo.FOOTMAN] * 39
    state = start(first=0, deck=deck)
    p = state.players[0]
    p.hand.clear()
    faith = E.leader_area_card(state, 0, forest.SATHANID_FAITH)
    assert faith is not None and E.faith_value(state, 0, forest.SATHANID_FAITH) == 0
    unlock_evolution(state, 0)
    set_pp(state, 0, 10)
    evolve(state, put(state, 0, demo.FOOTMAN))           # evolution with a point counts
    assert E.faith_value(state, 0, forest.SATHANID_FAITH) == 1

    low = give(state, 0, forest.SATHANID)
    play(state, low)                                     # faith 1: nothing happens
    assert p.hand == [] and E.faith_value(state, 0, forest.SATHANID_FAITH) == 1
    assert low.has(Keyword.DRAIN)

    E.change_faith(state, 0, forest.SATHANID_FAITH, 10)  # 11
    play(state, give(state, 0, forest.SATHANID))
    assert E.faith_value(state, 0, forest.SATHANID_FAITH) == 1
    (depths,) = p.hand
    assert depths.defn == forest.DEPTHS_OF_THE_ELD_LANCE and depths.cost == 1
    assert {a.targets for a in play_options(state, depths)} == {(low.uid,), (p.field[-1].uid,)}
    play(state, depths, [low.uid])
    assert low.evolved and state.players[1].leader_hp == 19
    assert E.faith_value(state, 0, forest.SATHANID_FAITH) == 2


def test_moelle_gloomy_maiden():
    # Fanfare: select a card in your hand, return it to the deck; draw a card. Ward.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 1)
    keep = give(state, 0, forest.SETUS_AND_MAISHA)
    moelle = give(state, 0, forest.MOELLE)
    assert [a.targets for a in play_options(state, moelle)] == [(keep.uid,)]   # must pick one
    deck_before = len(p.deck)
    play(state, moelle, [keep.uid])
    assert (keep in p.deck) != (keep in p.hand)                 # shuffled in (may be redrawn)
    assert len(p.hand) == 1 and len(p.deck) == deck_before     # +1 returned, -1 drawn

    # With an empty hand it just draws.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 1)
    moelle = give(state, 0, forest.MOELLE)
    assert [a.targets for a in play_options(state, moelle)] == [()]
    play(state, moelle)
    assert len(p.hand) == 1
    assert moelle.has(Keyword.WARD)


def test_lyria_skydestined():
    # Enhance (8): draw a follower costing 7 or more, then recover 7 PP. Barrier.
    state = fresh()
    p = state.players[0]
    for _ in range(5):
        p.deck.append(state.new_instance(forest.GREAT_HART, 0))     # 6-cost: not eligible
    setus = state.new_instance(forest.SETUS_AND_MAISHA, 0)
    p.deck.insert(0, setus)
    set_pp(state, 0, 10)
    lyria = give(state, 0, neutral.LYRIA)
    play(state, lyria)
    assert p.hand == [setus]
    assert p.pp == 9                                     # 10 - 8 + 7
    assert lyria.has(Keyword.BARRIER)

    # No eligible follower in the deck: still recovers 7.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 9)
    play(state, give(state, 0, neutral.LYRIA))
    assert p.hand == [] and p.pp == 8                    # 9 - 8 + 7

    # Not enough PP for Enhance: a plain 2-cost 1/1.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 7)
    play(state, give(state, 0, neutral.LYRIA))
    assert p.hand == [] and p.pp == 5


def test_virewind_fencer():
    # Fanfare: Combo (3) - gain Storm.
    state = fresh()
    set_pp(state, 0, 10)
    early = give(state, 0, forest.VIREWIND_FENCER)
    play(state, early)
    assert not early.has(Keyword.STORM) and not can_attack(state, early, leader_uid(1))
    bounties(state, 1)
    late = give(state, 0, forest.VIREWIND_FENCER)
    play(state, late)
    assert late.has(Keyword.STORM) and can_attack(state, late, leader_uid(1))


def test_leafshadow_assassin():
    # Fanfare: add a Fairy to your hand. Combo (3) - give that Fairy Bane.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    play(state, give(state, 0, forest.LEAFSHADOW_ASSASSIN))
    (plain,) = p.hand
    assert plain.defn == forest.FAIRY and not plain.has(Keyword.BANE)
    p.hand.clear()
    bounties(state, 1)
    play(state, give(state, 0, forest.LEAFSHADOW_ASSASSIN))
    (fairy,) = p.hand
    assert fairy.defn == forest.FAIRY and fairy.has(Keyword.BANE)
    play(state, fairy)
    assert fairy.has(Keyword.BANE) and fairy.has(Keyword.RUSH)   # keeps it on the field


def test_grace_of_the_swarmpetal():
    # Draw X cards, X = your Combo (counting this card).
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    bounties(state, 2)
    play(state, give(state, 0, forest.GRACE_OF_THE_SWARMPETAL))
    assert len(p.hand) == 3


def test_crimson_incense():
    # In hand: at the end of your turn, Combo (3) - this card costs 1 less (stays reduced).
    # Spell: select an enemy follower and destroy it; draw a card.
    state = fresh()
    p = state.players[0]
    incense = give(state, 0, forest.CRIMSON_INCENSE)
    end_turn(state)                                      # Combo 0
    assert incense.cost == 4
    end_turn(state)
    set_pp(state, 0, 10)
    bounties(state, 3)
    end_turn(state)                                      # Combo 3
    assert incense.cost == 3
    end_turn(state)
    assert incense.cost == 3                             # not just until the end of the turn
    set_pp(state, 0, 3)
    assert play_options(state, incense) == []            # needs an enemy follower to select
    giant = put(state, 1, demo.GIANT)
    hand_before = len(p.hand)
    play(state, incense, [giant.uid])
    assert not on_field(state, giant) and len(p.hand) == hand_before   # -1 played, +1 drawn


def test_yuel_and_societte_dancing_duo():
    # Fanfare: twice, 4 damage to a random enemy follower. Super-Evolve: gain Crest: Yuel &
    # Societte (Countdown 4; once on each of your turns, when you play a follower, evolve it).
    state = fresh()
    set_pp(state, 0, 5)
    giant = put(state, 1, demo.GIANT)                    # 5/5: survives one hit, not two
    play(state, give(state, 0, forest.YUEL_AND_SOCIETTE))
    assert not on_field(state, giant)

    state = fresh()
    unlock_evolution(state, 0)
    set_pp(state, 0, 5)
    yuel = give(state, 0, forest.YUEL_AND_SOCIETTE)
    play(state, yuel)
    evolve(state, yuel, super_=False)
    assert E.leader_area_card(state, 0, forest.YUEL_CREST) is None

    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 10)
    yuel = give(state, 0, forest.YUEL_AND_SOCIETTE)
    play(state, yuel)
    evolve(state, yuel, super_=True)
    crest = E.leader_area_card(state, 0, forest.YUEL_CREST)
    assert crest is not None and crest.countdown == 4
    bounties(state, 1)                                   # a spell doesn't use it
    ally = put(state, 0, demo.FOOTMAN)
    lieutenant = give(state, 0, forest.VIRID_LIEUTENANT)
    second = give(state, 0, forest.VIREWIND_FENCER)
    play(state, lieutenant)
    play(state, second)
    assert lieutenant.evolved and not lieutenant.super_evolved and not second.evolved
    assert (ally.atk, ally.life) == (1, 2)               # no Evolve ability without points


def test_great_hart_of_the_glacial_realm():
    # Fanfare: add 2 Deepwood Bounty (0-cost: restore 1 to your leader). At the end of your
    # turn, X damage split between enemy followers, X = its attack. Super-Evolve: gain
    # Crest: Great Hart (Countdown 3; at the end of your turn, Combo (3) - add a Deepwood
    # Bounty to your hand).
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 6)
    a, b, c = put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER), put(state, 1, demo.GIANT)
    hart = give(state, 0, forest.GREAT_HART)
    play(state, hart)
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 2
    p.leader_hp = 10
    play(state, p.hand[0])
    assert p.leader_hp == 11
    end_turn(state)                                      # 5 damage: 2, 3, then 0
    assert not on_field(state, a) and not on_field(state, b) and c.life == 5

    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 6)
    hart = give(state, 0, forest.GREAT_HART)
    play(state, hart)
    p.hand.clear()
    evolve(state, hart, super_=False)
    assert E.leader_area_card(state, 0, forest.GREAT_HART_CREST) is None

    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 6)
    giant = put(state, 1, demo.GIANT)
    giant2 = put(state, 1, demo.GIANT)
    hart = give(state, 0, forest.GREAT_HART)
    play(state, hart)
    p.hand.clear()
    evolve(state, hart, super_=True)                     # 8/8
    crest = E.leader_area_card(state, 0, forest.GREAT_HART_CREST)
    assert crest is not None and crest.countdown == 3
    end_turn(state)                                      # Combo 1: no Bounty; 8 damage
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 0
    assert not on_field(state, giant) and giant2.life == 2
    end_turn(state)
    p.hand.clear()
    set_pp(state, 0, 10)
    bounties(state, 3)
    end_turn(state)
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 1


# =============================================================================================
# Free-slot cards
# =============================================================================================

def test_elven_trapper():
    # Fanfare: select a card in your hand and return it to the deck; add 2 Fairies.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 1)
    keep = give(state, 0, forest.SETUS_AND_MAISHA)
    trapper = give(state, 0, forest.ELVEN_TRAPPER)
    assert [a.targets for a in play_options(state, trapper)] == [(keep.uid,)]
    play(state, trapper, [keep.uid])
    assert keep in p.deck and count(p.hand, forest.FAIRY) == 2 and len(p.hand) == 2


def test_tia_eternal_crystalian():
    # Enhance (4): all allied followers +1/+1. Rush. Once on each of your turns, when it is
    # given + attack or defense on the field, add an Eve, Blade of Crystalia (3/3 Storm Ward).
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    ally = put(state, 0, demo.FOOTMAN)
    tia = give(state, 0, forest.TIA)
    play(state, tia)                                     # enhanced
    assert (ally.atk, ally.life) == (2, 3) and (tia.atk, tia.life) == (3, 3)
    assert count(p.hand, forest.EVE) == 1
    eve = p.hand[0]
    assert (eve.atk, eve.life) == (3, 3) and eve.has(Keyword.STORM) and eve.has(Keyword.WARD)
    set_pp(state, 0, 7)
    play(state, give(state, 0, forest.SETUS_AND_MAISHA))   # buffed again: once per turn
    assert count(p.hand, forest.EVE) == 1
    assert tia.has(Keyword.RUSH)
    end_turn(state)
    E.buff(state, tia, 1, 0)                             # during the opponent's turn: nothing
    resolve_queue(state)
    assert count(p.hand, forest.EVE) == 1
    end_turn(state)
    set_pp(state, 0, 7)
    play(state, give(state, 0, forest.SETUS_AND_MAISHA))   # a new turn of its controller
    assert count(p.hand, forest.EVE) == 2

    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 2)
    tia = give(state, 0, forest.TIA)
    play(state, tia)                                     # not enhanced
    assert (tia.atk, tia.life) == (2, 2) and count(p.hand, forest.EVE) == 0


def test_flight_of_the_swarmpetal():
    # 3 damage split between enemy followers; add a Fairy.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 2)
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)
    play(state, give(state, 0, forest.FLIGHT_OF_THE_SWARMPETAL))
    assert not on_field(state, a) and b.life == 4
    assert count(p.hand, forest.FAIRY) == 1


def test_verdant_ring_kindred():
    # Choose 1 mode: (1) 4 damage to a random enemy follower, (2) add a Deepwood Bounty and a
    # Fairy. Combo (3): activate both instead.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    giant = put(state, 1, demo.GIANT)
    vrk = give(state, 0, forest.VERDANT_RING_KINDRED)
    assert {a.modes for a in play_options(state, vrk)} == {(0,), (1,)}
    play(state, vrk, modes=(1,))
    assert giant.life == 5 and count(p.hand, forest.DEEPWOOD_BOUNTY) == 1
    assert count(p.hand, forest.FAIRY) == 1
    p.hand.clear()
    bounties(state, 1)                                   # Combo 3 with the next card
    vrk = give(state, 0, forest.VERDANT_RING_KINDRED)
    play(state, vrk, play_options(state, vrk)[0].targets, play_options(state, vrk)[0].modes)
    assert giant.life == 1
    assert count(p.hand, forest.DEEPWOOD_BOUNTY) == 1 and count(p.hand, forest.FAIRY) == 1


def test_ewiyar_wind_personified():
    # Fanfare: Skybound Art - recover 1 evolution point. Rush.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 2)
    p.ep = 0
    ewiyar = give(state, 0, forest.EWIYAR)
    play(state, ewiyar)                                  # gauge far below 10
    assert p.ep == 0 and ewiyar.has(Keyword.RUSH)

    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 2)
    p.ep = 0
    p.turns_taken = 10
    play(state, give(state, 0, forest.EWIYAR))
    assert p.ep == 1

    # Gauge = turn count + allied evolutions while it is in hand: 9 + 1.
    state = fresh()
    p = state.players[0]
    p.turns_taken = 9
    set_pp(state, 0, 2)
    ewiyar = give(state, 0, forest.EWIYAR)
    evolve(state, put(state, 0, demo.FOOTMAN))
    assert p.ep == 1
    play(state, ewiyar)
    assert p.ep == 2


def test_intrepid_newshound():
    # Last Words: draw a card. Super-Evolve: summon 2 Intrepid Newshounds.
    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 3)
    hound = give(state, 0, neutral.INTREPID_NEWSHOUND)
    play(state, hound)
    evolve(state, hound, super_=False)
    assert len(p.field) == 1

    state = fresh()
    p = state.players[0]
    unlock_evolution(state, 0)
    set_pp(state, 0, 3)
    hound = give(state, 0, neutral.INTREPID_NEWSHOUND)
    play(state, hound)
    evolve(state, hound, super_=True)
    assert count(p.field, neutral.INTREPID_NEWSHOUND) == 3
    copy = p.field[1]
    E.destroy(state, copy)
    resolve_queue(state)
    assert len(p.hand) == 1


def test_michelle_kind_mindreader():
    # Fanfare: summon a Lycoris, Barbs of Passion; give all allied followers Barrier. Ward.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 6)
    ally = put(state, 0, demo.FOOTMAN)
    michelle = give(state, 0, forest.MICHELLE)
    play(state, michelle)
    assert count(p.field, forest.LYCORIS) == 1 and count(p.field, forest.MICHELLE) == 1
    assert all(f.has(Keyword.BARRIER) for f in p.followers) and len(p.followers) == 3
    lycoris = next(f for f in p.followers if f.defn == forest.LYCORIS)
    assert (lycoris.atk, lycoris.life) == (3, 4)
    assert lycoris.has(Keyword.RUSH) and lycoris.has(Keyword.BANE)
    assert michelle.has(Keyword.WARD)


def test_hien_redolent_revenant():
    # In hand: whenever you play a card, it costs 1 less until the end of the turn.
    # Fanfare: select an enemy follower, 4 damage. Last Words: summon a Hien.
    state = fresh()
    p = state.players[0]
    set_pp(state, 0, 10)
    hien = give(state, 0, forest.HIEN)
    bounties(state, 3)
    assert hien.cost == 6
    end_turn(state)
    assert hien.cost == 9
    end_turn(state)
    set_pp(state, 0, 9)
    giant = put(state, 1, demo.GIANT)
    play(state, hien, [giant.uid])
    assert giant.life == 1
    E.destroy(state, hien)
    resolve_queue(state)
    assert count(p.field, forest.HIEN) == 1 and p.field[0] is not hien


# =============================================================================================
# Printed stats and keywords (cards and the tokens they create)
# =============================================================================================

# (cost, attack, defense, keywords) from the official data.
OFFICIAL_STATS = {
    neutral.WORLD_OF_GAMES: (1, 0, 0, Keyword.NONE),
    forest.SPROUTING_INITIATE: (1, 1, 1, Keyword.RUSH),
    forest.VIRID_LIEUTENANT: (2, 1, 3, Keyword.NONE),
    forest.MIROKU: (3, 2, 2, Keyword.NONE),
    forest.MAGACHIYO: (3, 2, 2, Keyword.NONE),
    forest.THESTAE: (4, 3, 3, Keyword.NONE),
    forest.SETUS_AND_MAISHA: (7, 4, 6, Keyword.WARD | Keyword.STORM),
    forest.SATHANID: (1, 1, 1, Keyword.DRAIN),
    forest.MOELLE: (1, 1, 1, Keyword.WARD),
    neutral.LYRIA: (2, 1, 1, Keyword.BARRIER),
    forest.VIREWIND_FENCER: (2, 2, 2, Keyword.NONE),
    forest.LEAFSHADOW_ASSASSIN: (2, 2, 2, Keyword.NONE),
    forest.GRACE_OF_THE_SWARMPETAL: (3, 0, 0, Keyword.NONE),
    forest.CRIMSON_INCENSE: (4, 0, 0, Keyword.NONE),
    forest.YUEL_AND_SOCIETTE: (5, 4, 3, Keyword.NONE),
    forest.GREAT_HART: (6, 5, 5, Keyword.NONE),
    forest.ELVEN_TRAPPER: (1, 1, 1, Keyword.NONE),
    forest.TIA: (2, 2, 2, Keyword.RUSH),
    forest.FLIGHT_OF_THE_SWARMPETAL: (2, 0, 0, Keyword.NONE),
    forest.VERDANT_RING_KINDRED: (2, 0, 0, Keyword.NONE),
    forest.EWIYAR: (2, 2, 1, Keyword.RUSH),
    neutral.INTREPID_NEWSHOUND: (3, 3, 2, Keyword.NONE),
    forest.MICHELLE: (6, 1, 1, Keyword.WARD),
    forest.HIEN: (9, 4, 4, Keyword.NONE),
    # tokens and summoned cards
    forest.FAIRY: (1, 1, 1, Keyword.RUSH),
    forest.DEEPWOOD_BOUNTY: (0, 0, 0, Keyword.NONE),
    forest.EVE: (3, 3, 3, Keyword.WARD | Keyword.STORM),
    forest.DEPTHS_OF_THE_ELD_LANCE: (1, 0, 0, Keyword.NONE),
    forest.LYCORIS: (4, 3, 4, Keyword.RUSH | Keyword.BANE),
}

OFFICIAL_TYPES = {
    neutral.WORLD_OF_GAMES: CardType.COUNTDOWN_AMULET,
    forest.GRACE_OF_THE_SWARMPETAL: CardType.SPELL,
    forest.CRIMSON_INCENSE: CardType.SPELL,
    forest.FLIGHT_OF_THE_SWARMPETAL: CardType.SPELL,
    forest.VERDANT_RING_KINDRED: CardType.SPELL,
    forest.DEEPWOOD_BOUNTY: CardType.SPELL,
    forest.DEPTHS_OF_THE_ELD_LANCE: CardType.SPELL,
}

# Leader-area cards: (countdown) from the official data.
OFFICIAL_CRESTS = {
    forest.THESTAE_CREST: 3,
    forest.YUEL_CREST: 4,
    forest.GREAT_HART_CREST: 3,
    forest.SATHANID_FAITH: None,
}


def test_stats_and_keywords():
    for defn, (cost, atk, life, keywords) in OFFICIAL_STATS.items():
        assert (defn.cost, defn.atk, defn.life, defn.keywords) == (cost, atk, life, keywords), defn.name
        assert defn.type == OFFICIAL_TYPES.get(defn, CardType.FOLLOWER), defn.name
    assert neutral.WORLD_OF_GAMES.countdown == 5
    assert forest.FAIRY.is_token and forest.EVE.is_token and forest.DEEPWOOD_BOUNTY.is_token
    for crest, countdown in OFFICIAL_CRESTS.items():
        assert crest.countdown == countdown, crest.name
    # Keyword-only cards: the Fairy and Eve tokens play correctly on the field.
    state = fresh()
    set_pp(state, 0, 4)
    enemy = put(state, 1, demo.FOOTMAN)
    fairy = give(state, 0, forest.FAIRY)
    eve = give(state, 0, forest.EVE)
    play(state, fairy)
    play(state, eve)
    assert can_attack(state, fairy, enemy.uid) and not can_attack(state, fairy, leader_uid(1))
    assert can_attack(state, eve, leader_uid(1))
