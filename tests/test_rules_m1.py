"""Rules added for the starter decks: hand targets and discard, play reactions,
countdown advance, leader area, timed leader effects, Accelerate, multiple
attacks, evolve modes, and action de-duplication."""
from svsim.cards import demo, dragon, sword
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import CardType, Craft
from svsim.core.state import DESTROYED, leader_uid

from helpers import give, plays, put, set_pp, start, unlock_evolution


def test_faith_starts_in_leader_area():
    state = start(deck=[sword.YIDMETRA] + [demo.FOOTMAN] * 39, deck1=[demo.FOOTMAN] * 40)
    assert [c.defn for c in state.players[0].leader_area] == [sword.ELD_SWORD_FAITH]
    assert state.players[1].leader_area == []


def test_hand_targets_count_identical_cards_once():
    state = start()                                  # hand: 5 Footmen
    set_pp(state, 0, 2)
    kimika = give(state, 0, dragon.KIMIKA)
    give(state, 0, dragon.VORLALAI)
    give(state, 0, dragon.VORLALAI)
    give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    assert len(plays(state, kimika.uid)) == 3        # Footman, Vorlalai, or Depths


def test_discarded_card_ability_resolves_after_the_fanfare():
    state = start()
    p = state.players[0]
    p.hand.clear()
    p.leader_hp = 10
    set_pp(state, 0, 2)
    kimika = give(state, 0, dragon.KIMIKA)
    vorlalai = give(state, 0, dragon.VORLALAI)
    apply(state, PlayCard(kimika.uid, (vorlalai.uid,)))
    assert [c.defn for c in p.field] == [dragon.KIMIKA, dragon.VORLALAI]
    assert p.shadows == 1 and len(p.hand) == 1 and p.leader_hp == 11


def test_spell_needs_every_target():
    """Official Q&A (Spilling Red): both a hand card and an enemy follower are needed."""
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 1)
    red = give(state, 0, dragon.SPILLING_RED)
    enemy = put(state, 1, demo.FOOTMAN)
    assert plays(state, red.uid) == []
    footman = give(state, 0, demo.FOOTMAN)
    assert plays(state, red.uid) == [PlayCard(red.uid, (footman.uid, enemy.uid))]
    state.players[1].field.clear()
    assert plays(state, red.uid) == []


def test_reactions_are_queued_when_the_card_is_played():
    """Confirmed by a player: a flag summoned by L'Age d'Or isn't advanced by it."""
    state = start()
    old = put(state, 0, sword.DREAD_PIRATES_FLAG)
    set_pp(state, 0, 4)
    card = give(state, 0, sword.LAGE_DOR)
    apply(state, PlayCard(card.uid))
    new = state.players[0].field[-1]
    assert (old.countdown, new.countdown) == (6, 7)


def test_advanced_countdown_destroys_and_last_words_fire():
    state = start()
    flag = put(state, 0, sword.DREAD_PIRATES_FLAG)
    flag.countdown = 1
    set_pp(state, 0, 0)
    gold = give(state, 0, sword.GLITTERING_GOLD)
    apply(state, PlayCard(gold.uid, modes=(0,)))
    assert flag.fate == DESTROYED and state.players[1].leader_hp == 18


def test_leader_area_holds_one_of_each_and_at_most_five():
    state = start()
    assert E.add_to_leader_area(state, 0, sword.UNKEI_CREST)
    assert E.add_to_leader_area(state, 0, sword.UNKEI_CREST) is None
    for i in range(4):
        crest = CardDef(900 + i, f"Crest {i}", Craft.NEUTRAL, CardType.CREST, 0)
        assert E.add_to_leader_area(state, 0, crest)
    assert E.add_to_leader_area(state, 0, dragon.BURNITE_CREST) is None


def test_leader_damage_cap_lasts_through_the_opponents_turn():
    state = start(first=0)
    E.give_leader_damage_cap(state, 0, 0, until_turn=state.turn + 1)
    E.damage(state, [leader_uid(0)], 5)
    apply(state, EndTurn())                          # opponent's turn: still capped
    E.damage(state, [leader_uid(0)], 5)
    assert state.players[0].leader_hp == 20
    apply(state, EndTurn())                          # expired at the end of that turn
    E.damage(state, [leader_uid(0)], 5)
    assert state.players[0].leader_hp == 15


def test_accelerate_only_when_the_normal_cost_is_unaffordable():
    state = start()
    p = state.players[0]
    p.hand.clear()
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    set_pp(state, 0, 2)
    assert plays(state, lumiore.uid) == []
    set_pp(state, 0, 5)
    assert plays(state, lumiore.uid) == [PlayCard(lumiore.uid)]   # Accelerate (3)
    apply(state, PlayCard(lumiore.uid))
    assert (p.max_pp, p.pp, p.field, p.shadows) == (6, 2, [], 1)
    again = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    set_pp(state, 0, 8)
    apply(state, PlayCard(again.uid))                # normal play: a follower on the field
    assert p.field == [again]


def test_attacks_per_turn():
    state = start()
    beltezore = put(state, 0, sword.BELTEZORE)
    for _ in range(3):
        apply(state, Attack(beltezore.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 14
    assert not any(isinstance(a, Attack) for a in legal_actions(state))


def test_evolve_chooses_modes_again():
    """Official Q&A (Norman): replicating a Mode Fanfare lets you choose again."""
    state = start()
    unlock_evolution(state, 0)
    normagdala = put(state, 0, dragon.NORMAGDALA)
    enemy = put(state, 1, demo.SHIELDBEARER)         # 1/3
    choices = {(a.super_, a.modes) for a in legal_actions(state) if isinstance(a, Evolve)}
    assert choices == {(False, (0,)), (False, (1,)), (True, (0,)), (True, (1,))}
    apply(state, Evolve(normagdala.uid, modes=(1,)))
    assert enemy.fate == DESTROYED                   # -0/-4


def test_identical_cards_in_hand_give_one_set_of_actions():
    state = start()
    p = state.players[0]
    p.hand.clear()
    golds = [give(state, 0, sword.GLITTERING_GOLD) for _ in range(3)]
    gold_plays = [a for a in legal_actions(state) if isinstance(a, PlayCard)]
    assert len(gold_plays) == 2 and {a.uid for a in gold_plays} == {golds[0].uid}
