"""Forestcraft cards of set 10 (Deicide in Nacreheim) and Crest: Untamed Testimony."""
from svsim.cards import demo, forest
from svsim.cards.neutral import DIVINE_EVIDENCE
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, resolve_queue
from svsim.core.enums import Keyword
from svsim.core.state import DESTROYED, FIELD_LIMIT

from helpers import count, give, put, set_pp, start, unlock_evolution


def fresh(first: int = 0, deck=None, deck1=None):
    """A started game with an empty hand for player 0."""
    state = start(first=first, deck=deck, deck1=deck1)
    state.players[0].hand.clear()
    return state


def play(state, card, targets=(), modes=()):
    apply(state, PlayCard(card.uid, tuple(targets), tuple(modes)))


def end_round(state):
    apply(state, EndTurn())
    apply(state, EndTurn())


def test_one_cost_allies_count_followers_and_amulets_by_base_cost():
    state = fresh()
    footman = put(state, 0, demo.FOOTMAN)                # a 1-cost follower
    E.add_cost(footman, 1)                               # its base cost is what counts
    evidence = put(state, 0, DIVINE_EVIDENCE)            # a 1-cost amulet
    put(state, 0, demo.SHIELDBEARER)                     # 2-cost: not counted
    put(state, 1, demo.FOOTMAN)                          # enemy: not counted
    mischief = give(state, 0, forest.INQUIRING_MISCHIEF)
    set_pp(state, 0, 1)
    play(state, mischief)
    assert (mischief.atk, mischief.life) == (3, 2) and evidence in state.players[0].field


# --- 1 to 3 PP -------------------------------------------------------------------------------

def test_inquiring_mischief_needs_two_other_one_cost_allies():
    state = fresh()
    first = give(state, 0, forest.INQUIRING_MISCHIEF)
    set_pp(state, 0, 1)
    play(state, first)
    assert (first.atk, first.life) == (1, 1) and first.has(Keyword.RUSH)
    second = give(state, 0, forest.INQUIRING_MISCHIEF)  # one other 1-cost ally: not enough
    set_pp(state, 0, 1)
    play(state, second)
    assert (second.atk, second.life) == (1, 1)
    third = give(state, 0, forest.INQUIRING_MISCHIEF)   # two others: +2/+1
    set_pp(state, 0, 1)
    play(state, third)
    assert (third.atk, third.life) == (3, 2) and (first.atk, second.atk) == (1, 1)


def test_inquiring_mischief_summoned_also_checks():
    state = fresh()
    put(state, 0, demo.FOOTMAN)
    put(state, 0, demo.FOOTMAN)
    summoned = E.summon(state, 0, forest.INQUIRING_MISCHIEF)
    resolve_queue(state)
    assert (summoned.atk, summoned.life) == (3, 2)


def test_debonair_dogsitter_summons_evidence_and_evolve_heals_with_two_one_costs():
    state = fresh()
    p = state.players[0]
    p.leader_hp = 10
    dog = give(state, 0, forest.DEBONAIR_DOGSITTER)
    set_pp(state, 0, 2)
    play(state, dog)
    assert count(p.field, DIVINE_EVIDENCE) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(dog.uid))                         # only the Evidence: no heal
    assert p.leader_hp == 10
    state2 = fresh()
    p2 = state2.players[0]
    p2.leader_hp = 10
    put(state2, 0, demo.FOOTMAN)
    dog2 = give(state2, 0, forest.DEBONAIR_DOGSITTER)
    set_pp(state2, 0, 2)
    play(state2, dog2)
    unlock_evolution(state2, 0)
    apply(state2, Evolve(dog2.uid))                       # Footman + Evidence
    assert p2.leader_hp == 12


def test_garden_elf_adds_bounty_and_fairy_at_end_of_turn():
    state = fresh()
    p = state.players[0]
    put(state, 0, forest.GARDEN_ELF)
    apply(state, EndTurn())
    assert [c.defn for c in p.hand] == [forest.DEEPWOOD_BOUNTY, forest.FAIRY]
    apply(state, EndTurn())                               # not on the opponent's turn end
    assert count(p.hand, forest.FAIRY) == 1


def test_untamed_testimony_crest_summons_a_mischief_on_each_of_the_next_two_turns():
    state = fresh()
    p = state.players[0]
    testimony = give(state, 0, forest.UNTAMED_TESTIMONY)
    set_pp(state, 0, 2)
    play(state, testimony)
    assert count(p.field, DIVINE_EVIDENCE) == 1
    crest = E.leader_area_card(state, 0, forest.UNTAMED_TESTIMONY_CREST)
    assert crest is not None and crest.countdown == 2
    end_round(state)
    assert count(p.field, forest.INQUIRING_MISCHIEF) == 1 and crest.countdown == 1
    end_round(state)
    # Needs the parent's engine change (a countdown card's on_turn_start still fires on the turn its
    # count reaches 0, as Salem confirmed for Slaus); fails on an engine without it (1 Mischief).
    assert crest.fate == DESTROYED and count(p.field, forest.INQUIRING_MISCHIEF) == 2


def test_natural_reincarnation_summons_and_evolves_fairies():
    state = fresh()
    p = state.players[0]
    spell = give(state, 0, forest.NATURAL_REINCARNATION)
    set_pp(state, 0, 3)
    play(state, spell)
    fairies = [f for f in p.field if f.defn == forest.FAIRY]
    assert len(fairies) == 1 and fairies[0].evolved
    enhanced = give(state, 0, forest.NATURAL_REINCARNATION)
    set_pp(state, 0, 6)
    ep = p.ep
    play(state, enhanced)
    fairies = [f for f in p.field if f.defn == forest.FAIRY]
    assert len(fairies) == 4 and all(f.evolved for f in fairies) and p.ep == ep


def test_nosches_interrogation_damages_and_gives_storm_with_two_one_costs():
    state = fresh()
    p = state.players[0]
    enemy = put(state, 1, demo.GIANT)
    spell = give(state, 0, forest.NOSCHES_INTERROGATION)
    set_pp(state, 0, 3)
    play(state, spell)
    assert enemy.life == 0 or enemy not in state.players[1].field
    mischief = [c for c in p.hand if c.defn == forest.INQUIRING_MISCHIEF]
    assert len(mischief) == 1 and not mischief[0].has(Keyword.STORM)
    put(state, 0, demo.FOOTMAN)
    put(state, 0, DIVINE_EVIDENCE)
    again = give(state, 0, forest.NOSCHES_INTERROGATION)
    set_pp(state, 0, 3)
    play(state, again)                                    # no enemy follower: the rest still happens
    stormy = [c for c in p.hand if c.defn == forest.INQUIRING_MISCHIEF and c.has(Keyword.STORM)]
    assert len(stormy) == 1
    set_pp(state, 0, 1)
    play(state, stormy[0])
    assert stormy[0] in p.field and stormy[0].has(Keyword.STORM)


# --- 4 PP and up -----------------------------------------------------------------------------

def test_sleuths_best_friend_evidence_storm_and_evolve_mischief():
    state = fresh()
    p = state.players[0]
    dog = give(state, 0, forest.SLEUTHS_BEST_FRIEND)
    set_pp(state, 0, 4)
    play(state, dog)
    assert dog.has(Keyword.STORM) and count(p.field, DIVINE_EVIDENCE) == 1
    unlock_evolution(state, 0)
    apply(state, Evolve(dog.uid))                         # only one 1-cost ally
    assert count(p.field, forest.INQUIRING_MISCHIEF) == 0
    state2 = fresh()
    p2 = state2.players[0]
    put(state2, 0, demo.FOOTMAN)
    dog2 = give(state2, 0, forest.SLEUTHS_BEST_FRIEND)
    set_pp(state2, 0, 4)
    play(state2, dog2)
    unlock_evolution(state2, 0)
    apply(state2, Evolve(dog2.uid))
    assert count(p2.field, forest.INQUIRING_MISCHIEF) == 1


def test_nosche_summons_without_fanfares_and_super_evolve_buffs_others():
    state = fresh()
    p = state.players[0]
    other = put(state, 0, demo.SHIELDBEARER)
    nosche = give(state, 0, forest.NOSCHE)
    set_pp(state, 0, 6)
    play(state, nosche)
    assert count(p.field, forest.SLEUTHS_BEST_FRIEND) == 1
    assert count(p.field, forest.INQUIRING_MISCHIEF) == 1
    assert count(p.field, DIVINE_EVIDENCE) == 0           # a summoned Sleuth's Fanfare doesn't fire
    atk = {f.uid: f.atk for f in p.followers}
    unlock_evolution(state, 0)
    apply(state, Evolve(nosche.uid))                      # plain evolution: no buff
    assert all(f.atk == atk[f.uid] for f in p.followers if f is not nosche)
    state2 = fresh()
    p2 = state2.players[0]
    other = put(state2, 0, demo.SHIELDBEARER)
    nosche2 = give(state2, 0, forest.NOSCHE)
    set_pp(state2, 0, 6)
    play(state2, nosche2)
    unlock_evolution(state2, 0)
    apply(state2, Evolve(nosche2.uid, True))
    assert other.atk == 3 and nosche2.atk == 5 + 3       # super-evolved Nosche: +3/+3 only
    assert [f.atk for f in p2.followers if f.defn == forest.INQUIRING_MISCHIEF] == [3]


def test_wolf_pack_lackey_summons_two_and_evolve_two_more():
    state = fresh()
    p = state.players[0]
    lackey = give(state, 0, forest.WOLF_PACK_LACKEY)
    set_pp(state, 0, 7)
    play(state, lackey)
    assert count(p.field, forest.WOLF_PACK_LACKEY) == 3 and lackey.has(Keyword.RUSH)
    unlock_evolution(state, 0)
    apply(state, Evolve(lackey.uid))
    assert count(p.field, forest.WOLF_PACK_LACKEY) == 5


def _hyphae_state(top):
    state = fresh()
    p = state.players[0]
    p.deck = [state.new_instance(demo.FOOTMAN, 0) for _ in range(10)]
    p.deck += [state.new_instance(d, 0) for d in reversed(top)]       # the last card is drawn first
    return state, p


def test_heartening_hyphae_summons_only_forest_followers_drawn():
    state, p = _hyphae_state([forest.SLEUTHS_BEST_FRIEND, forest.NATURAL_REINCARNATION])
    hyphae = give(state, 0, forest.HEARTENING_HYPHAE)
    set_pp(state, 0, 8)
    play(state, hyphae)
    assert count(p.field, forest.SLEUTHS_BEST_FRIEND) == 1     # summoned: its Fanfare doesn't fire
    assert count(p.field, DIVINE_EVIDENCE) == 0
    assert [c.defn for c in p.hand] == [forest.NATURAL_REINCARNATION]
    state, p = _hyphae_state([demo.GIANT, forest.GARDEN_ELF])     # a Neutral follower stays in hand
    hyphae = give(state, 0, forest.HEARTENING_HYPHAE)
    set_pp(state, 0, 8)
    play(state, hyphae)
    assert [c.defn for c in p.hand] == [demo.GIANT] and count(p.field, forest.GARDEN_ELF) == 1


def test_heartening_hyphae_super_evolve_replicates_and_full_field_keeps_it_in_hand():
    state, p = _hyphae_state([forest.GARDEN_ELF, forest.GARDEN_ELF, forest.GARDEN_ELF,
                              forest.WOLF_PACK_LACKEY])
    hyphae = give(state, 0, forest.HEARTENING_HYPHAE)
    set_pp(state, 0, 8)
    play(state, hyphae)
    assert count(p.field, forest.GARDEN_ELF) == 2
    while len(p.field) < FIELD_LIMIT:
        put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(hyphae.uid, True))
    assert count(p.field, forest.GARDEN_ELF) == 2                     # field full: both stay in hand
    assert count(p.hand, forest.GARDEN_ELF) == 1 and count(p.hand, forest.WOLF_PACK_LACKEY) == 1


# --- gaps found by the analysis line's review (2026-10-28) ---------------------------------

def test_wolf_pack_lackey_evolve_summons_exactly_two():
    state = fresh()
    p = state.players[0]
    lackey = put(state, 0, forest.WOLF_PACK_LACKEY)        # on the field without its Fanfare
    unlock_evolution(state, 0)
    apply(state, Evolve(lackey.uid))
    assert count(p.field, forest.WOLF_PACK_LACKEY) == 3       # room for more: exactly 2 came


def test_nosches_interrogation_deals_exactly_five():
    state = fresh()
    big = put(state, 1, demo.GIANT)
    big.life = big.max_life = 20
    spell = give(state, 0, forest.NOSCHES_INTERROGATION)
    set_pp(state, 0, 3)
    play(state, spell)
    assert big.life == 15


def test_nosche_super_evolve_gives_attack_only():
    state = fresh()
    other = put(state, 0, demo.SHIELDBEARER)               # 1/3
    nosche = put(state, 0, forest.NOSCHE)
    unlock_evolution(state, 0)
    apply(state, Evolve(nosche.uid, True))
    assert (other.atk, other.life, other.max_life) == (3, 3, 3)
