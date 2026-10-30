"""Unlimited cards for the Rhinoceroach Forest deck (破魔虫精灵), with the official Q&A."""
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, demo, forest, unlimited as U
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard, UseBonusPP
from svsim.core.engine import apply, new_game
from svsim.core.state import DESTROYED, leader_uid

from helpers import count, give, put, set_pp, start, unlock_evolution
from test_fuzz import check_invariants


def fresh(pp: int = 10):
    """Player 0 to act on turn 1, empty hands, `pp` play points."""
    state = start(first=0)
    for p in state.players:
        p.hand.clear()
    set_pp(state, 0, pp)
    return state


def play(state, defn, targets=(), modes=()):
    inst = give(state, 0, defn)
    apply(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))
    return inst


def test_deck_is_legal_in_unlimited_and_fully_scripted():
    deck = decks.build(decks.RHINO_FOREST)
    assert decks.validate(deck, unlimited=True) == []
    assert decks.validate(deck) != []                       # not a Rotation deck
    assert decks.unimplemented(deck) == []
    assert sorted(c.card_id for c in decks.from_hash(decks.to_hash(deck, battle_format=2))) == \
        sorted(c.card_id for c in deck)


def test_rhinoceroach_gains_attack_per_combo_and_loops_with_bug_alert():
    state = fresh()
    opp = state.players[1]
    play(state, U.FAIRY_CONVOCATION)                        # combo 1, two Fairies in hand
    fairy = next(c for c in state.players[0].hand if c.defn == U.FAIRY)
    apply(state, PlayCard(fairy.uid))                       # combo 2
    rhino = play(state, U.KILLER_RHINOCEROACH)              # combo 3: 3/2 Storm
    assert (rhino.atk, rhino.life) == (3, 2)
    apply(state, Attack(rhino.uid, leader_uid(1)))
    play(state, forest.BUG_ALERT, targets=[rhino.uid])      # combo 4, back to hand as a fresh card
    again = next(c for c in state.players[0].hand if c.defn == U.KILLER_RHINOCEROACH)
    assert again.atk == 0
    apply(state, PlayCard(again.uid))                       # combo 5: 5/2
    apply(state, Attack(again.uid, leader_uid(1)))
    assert opp.leader_hp == 20 - 3 - 5 and state.players[0].pp == 1


def test_baby_carbuncle_returns_a_card_and_super_evolve_recovers_three():
    state = fresh(pp=10)
    rhino = put(state, 0, U.KILLER_RHINOCEROACH)
    carbuncle = play(state, U.BABY_CARBUNCLE, targets=[rhino.uid])
    assert rhino not in state.players[0].field
    assert count(state.players[0].hand, U.KILLER_RHINOCEROACH) == 1
    # Official Q&A: 9 max PP, bonus PP used, a 3-cost card played (7 left): recovers 3.
    p = state.players[0]
    p.max_pp, p.pp, p.bonus_ready = 9, 9, True
    apply(state, UseBonusPP())
    p.pp -= 3                                               # the 3-cost card
    assert p.pp == 7
    unlock_evolution(state, 0)
    apply(state, Evolve(carbuncle.uid, True))
    assert p.pp == 10


def test_lambent_cairn_fairy_bounty_and_engage():
    state = fresh()
    play(state, U.LAMBENT_CAIRN)
    assert [c.defn for c in state.players[0].hand] == [U.FAIRY]
    state.players[0].combo = 2
    cairn = play(state, U.LAMBENT_CAIRN)                    # combo 3: Fairy and Deepwood Bounty
    assert count(state.players[0].hand, U.DEEPWOOD_BOUNTY) == 1
    apply(state, Engage(cairn.uid))                         # Q&A: no follower needed, just destroyed
    assert cairn.fate == DESTROYED
    other = next(c for c in state.players[0].field if c.defn == U.LAMBENT_CAIRN)
    footman = put(state, 0, demo.FOOTMAN)
    apply(state, Engage(other.uid, (footman.uid,)))
    assert (footman.atk, footman.life) == (2, 3) and other.fate == DESTROYED


def test_glade_draws_and_evolve_splits_hand_size_damage():
    state = fresh()
    glade = play(state, U.GLADE)
    assert len(state.players[0].hand) == 2
    # Official Q&A: X = 7 against 3, 3 and 2 defense (oldest first) deals 3, 3 and 1.
    targets = [put(state, 1, demo.GIANT) for _ in range(3)]
    for t, life in zip(targets, (3, 3, 2)):
        t.life = t.max_life = life
    for _ in range(5):
        give(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(glade.uid))
    assert [t.fate for t in targets[:2]] == [DESTROYED, DESTROYED] and targets[2].life == 1


def test_bayle_gets_cheaper_whenever_an_allied_follower_leaves():
    state = fresh()
    bayle = give(state, 0, U.BAYLE)
    a, b, c = (put(state, 0, demo.FOOTMAN) for _ in range(3))
    E.destroy(state, a)
    E.return_to_hand(state, b)
    E.banish(state, c)
    from svsim.core.engine import resolve_queue
    resolve_queue(state)
    assert bayle.cost == 5
    apply(state, EndTurn())                                 # Q&A: also on the opponent's turn
    fairy = put(state, 0, U.FAIRY)
    E.destroy(state, fairy)
    resolve_queue(state)
    assert bayle.cost == 4
    enemy = put(state, 1, demo.GIANT)
    E.destroy(state, enemy)                                 # enemy followers don't count
    resolve_queue(state)
    assert bayle.cost == 4


def test_bayle_fanfare_deals_four():
    state = fresh()
    enemy = put(state, 1, demo.GIANT)
    play(state, U.BAYLE, targets=[enemy.uid])
    assert enemy.life == 1


def test_godwood_staff_combo_draw_and_engage():
    state = fresh()
    staff = play(state, U.GODWOOD_STAFF)
    apply(state, Engage(staff.uid))                         # Q&A: nothing to select, just destroyed
    assert staff.fate == DESTROYED
    staff = play(state, U.GODWOOD_STAFF)
    rhino = put(state, 0, U.KILLER_RHINOCEROACH)
    apply(state, Engage(staff.uid, (rhino.uid,)))
    assert staff.fate == DESTROYED and count(state.players[0].hand, U.KILLER_RHINOCEROACH) == 1
    state = fresh()
    play(state, U.GODWOOD_STAFF)
    state.players[0].combo = 3
    hand = len(state.players[0].hand)
    apply(state, EndTurn())
    assert len(state.players[0].hand) == hand + 1          # drew at the end of the turn


def test_gardens_allure_draws_two_after_a_fuse():
    state = fresh()
    play(state, U.GARDENS_ALLURE)
    assert len(state.players[0].hand) == 1
    state = fresh()
    allure = give(state, 0, U.GARDENS_ALLURE)
    fodder = give(state, 0, forest.BUG_ALERT)
    apply(state, Fuse(allure.uid, (fodder.uid,)))
    apply(state, PlayCard(allure.uid))
    assert len(state.players[0].hand) == 2


def test_eradicating_arrow_shrinks_random_enemies_combo_times():
    state = fresh()
    walls = [put(state, 1, demo.SHIELDBEARER) for _ in range(2)]   # 1/3 each
    state.players[0].combo = 3
    play(state, U.ERADICATING_ARROW)                        # combo 4: four times -0/-1
    assert sum(3 - w.life if w.fate != DESTROYED else 3 for w in walls) == 4


def test_fairy_convocation_adds_two_fairies():
    state = fresh()
    play(state, U.FAIRY_CONVOCATION)
    assert count(state.players[0].hand, U.FAIRY) == 2


def test_random_games_with_the_deck_hold_invariants():
    rhino = decks.build(decks.RHINO_FOREST)
    others = [decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON), rhino]
    for g in range(60):
        state = new_game(rhino, others[g % 3], seed=700 + g)
        agents = [RandomAgent(2 * g, 0.15), RandomAgent(2 * g + 1, 0.15)]
        assert play_game(state, agents, on_action=check_invariants) in (0, 1, -1)
