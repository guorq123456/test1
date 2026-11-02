"""Pins for docs/rulings.md section C: one minimal test per reading that had none. Each pins the CURRENT reading
(no behaviour change); if a ruling changes, the test fails and the register gets a new entry."""
from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Evolve
from svsim.core.engine import apply, legal_actions

from helpers import put, start


def _evolves(state):
    return [a for a in legal_actions(state) if isinstance(a, Evolve)]


def _own_turn(state, player, turn):
    while not (state.active == player and state.players[player].turns_taken == turn):
        apply(state, EndTurn())


def test_r02_recovered_evolution_points_are_capped_at_two():
    state = start(first=0)
    p = state.players[0]
    assert (p.ep, p.sep) == (2, 2)
    E.recover_ep(state, 0)
    E.recover_sep(state, 0, 3)
    assert (p.ep, p.sep) == (2, 2)
    p.ep, p.sep = 0, 1
    E.recover_ep(state, 0, 5)
    E.recover_sep(state, 0, 5)
    assert (p.ep, p.sep) == (2, 2)


def test_r02_a_recovered_point_cannot_be_spent_before_the_unlock_turn():
    state = start(first=0)
    _own_turn(state, 0, 4)                          # going first: evolution unlocks on own turn 5
    p = state.players[0]
    put(state, 0, demo.FOOTMAN)
    p.ep, p.sep = 0, 0
    E.recover_ep(state, 0)
    E.recover_sep(state, 0)
    assert (p.ep, p.sep) == (1, 1) and not _evolves(state)
    _own_turn(state, 0, 5)
    assert _evolves(state) and not any(a.super_ for a in _evolves(state))   # super evolution still waits for 7


def test_r09_nocturne_summons_a_skeleton_when_a_clue_amulet_is_banished_by_a_merge():
    from svsim.cards import abyss, neutral
    from svsim.core.actions import PlayCard
    from svsim.core.state import BANISHED
    from helpers import give, set_pp
    state = start()
    put(state, 0, abyss.NOCTURNE)
    set_pp(state, 0, 10)
    first = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(first.uid))
    skeletons = lambda: [c for c in state.players[0].field if c.defn.card_id == abyss.SKELETON.card_id]  # noqa: E731
    assert skeletons() == []
    apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))   # the merge banishes the first amulet
    assert first.fate == BANISHED and E.clues(state, 0) == 2
    skeleton, = skeletons()
    assert (skeleton.atk, skeleton.life) == (3, 5)


def test_r08_a_clue_amulet_merged_in_this_turn_can_engage_again_this_turn():
    from svsim.cards import neutral
    from svsim.core.actions import Engage, PlayCard
    from svsim.core.state import BANISHED, IN_PLAY
    from helpers import give, set_pp
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, 10)
    for _ in range(2):                                     # two plays: one amulet with 2 clues
        apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))
    engaged = E.clue_amulet(state, 0)
    apply(state, Engage(engaged.uid))
    assert engaged.fate == IN_PLAY and E.clues(state, 0) == 1      # it stays with 1 clue
    assert not any(isinstance(a, Engage) for a in legal_actions(state))   # once per amulet per turn
    third = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(third.uid))                      # merges: the engaged amulet is banished
    assert engaged.fate == BANISHED and E.clue_amulet(state, 0).uid == third.uid and E.clues(state, 0) == 2
    assert Engage(third.uid) in legal_actions(state)       # the merged-in amulet engages again this turn


def test_r07_a_spell_enters_the_graveyard_after_it_resolves():
    from svsim.core.actions import PlayCard
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, register
    from helpers import give, set_pp
    seen = []
    probe = CardDef(7591, "Test Shadow Probe", Craft.NEUTRAL, CardType.SPELL, 1)

    @register(probe.card_id)
    class ShadowProbe(CardScript):                       # reads the shadow count while it resolves
        def cast(self, ctx):
            seen.append(ctx.me.shadows)

    state = start()
    p = state.players[0]
    p.shadows = 3
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, probe).uid))
    assert seen == [3] and p.shadows == 4                  # not yet counted during resolution, counted after


def test_r01_the_default_turn_limit_is_60_and_ending_the_last_turn_is_a_draw():
    from svsim.core.enums import DRAW
    state = start(first=0)
    assert state.max_turns == 60
    state.players[0].leader_hp = state.players[1].leader_hp = 20
    while state.turn < 60:
        apply(state, EndTurn())
    assert state.turn == 60 and state.winner is None       # the 60th turn is still played
    apply(state, EndTurn())
    assert state.winner == DRAW                            # a draw, not both players losing


def test_r04_a_non_super_evolved_follower_loses_barrier_to_zero_damage():
    from svsim.core.enums import Keyword
    state = start(first=0)
    plain = put(state, 0, demo.FOOTMAN)
    E.give_keywords(plain, Keyword.BARRIER)
    life = plain.life
    E.damage(state, [plain], 0, None)
    assert not plain.has(Keyword.BARRIER) and plain.life == life


def test_r05_a_random_effect_can_hit_an_ambush_follower():
    from svsim.cards import neutral
    from svsim.core.actions import PlayCard
    from svsim.core.enums import Keyword
    from helpers import give, set_pp
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, 10)
    hidden = put(state, 1, demo.SHIELDBEARER)              # 1/3, so 2 damage leaves it at 1
    E.give_keywords(hidden, Keyword.AMBUSH)
    jailor = give(state, 0, neutral.JAILOR_OF_ANTIQUITY)
    assert [a.targets for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == jailor.uid] == [()]
    apply(state, PlayCard(jailor.uid))                     # nothing selectable: the 6 damage hits nothing
    assert hidden.life == 1                                # the random 2 damage still lands on the Ambush follower


def test_r12_a_second_crest_of_the_same_name_does_not_reset_the_countdown():
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    crest = CardDef(7592, "Test Countdown Crest", Craft.NEUTRAL, CardType.CREST, 0, countdown=3)
    state = start()
    first = E.add_to_leader_area(state, 0, crest)
    first.countdown = 1                                    # two turns have ticked it down
    assert E.add_to_leader_area(state, 0, crest) is None   # the second one fizzles
    assert state.players[0].leader_area == [first] and first.countdown == 1


def test_r14_halving_an_odd_max_defense_rounds_up():
    from svsim.cards import portal as PORTAL
    from helpers import give, set_pp
    from test_cards_portal import EVIDENCE, fuse, play
    state = start()
    foe = state.players[1]
    foe.leader_max_hp = foe.leader_hp = 19
    lineage = give(state, 0, PORTAL.LINEAGE)
    fuse(state, lineage, give(state, 0, EVIDENCE))
    set_pp(state, 0, 9)
    play(state, lineage)
    assert foe.leader_max_hp == 10 and foe.leader_hp == 10  # 19 / 2 rounded up
