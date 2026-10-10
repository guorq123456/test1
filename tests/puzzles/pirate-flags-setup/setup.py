"""The Pirate puzzle with its original card: Ruthless Eld Sword in place of the Depths of the Eld Sword (the
architecture thread 2026-10-10 02:16Z). No lethal this turn: a set-up turn, which line is better is open."""
from svsim.cards import decks, sword
from svsim.core import effects as E
from svsim.core.actions import Mulligan
from svsim.core.engine import apply, new_game

from helpers import give, put, set_pp


def build(seed: int = 0):
    """Our turn (player 0): turn 15, own turn 8, 8/8 play points, 12 defense, one evolution and one
    super-evolution point; three Dread Pirate's Flags at countdowns 2, 5, 5. Hand: Roughwater First Mate, Yidmetra,
    Flashstep Quickblader, Gilded Blade (cost 0), Ruthless Eld Sword, Beltezore. The enemy at 10 with a super-evolved Golden
    Knight 9/9 and a Steelclad Knight 2/2; five cards from their deck in hand (unknown to us)."""
    st = new_game(list(decks.build(decks.PIRATE_T)), list(decks.build(decks.PIRATE_T)), seed=seed, first=0)
    apply(st, Mulligan(()))
    apply(st, Mulligan(()))
    me, op = st.players
    for p in st.players:
        p.hand.clear()
        p.field.clear()
    st.turn = 15
    me.turns_taken, op.turns_taken = 8, 7
    set_pp(st, 0, 8)
    me.leader_hp, op.leader_hp = 12, 10
    me.ep = me.sep = op.ep = op.sep = 1
    for cd in (2, 5, 5):
        put(st, 0, sword.DREAD_PIRATES_FLAG).countdown = cd
    gk = put(st, 1, sword.GOLDEN_KNIGHT)
    E.evolve(st, gk, super_=True, notify=False)
    put(st, 1, sword.STEELCLAD_KNIGHT)
    for d in (sword.ROUGHWATER_FIRST_MATE, sword.YIDMETRA, sword.FLASHSTEP_QUICKBLADER):
        give(st, 0, d)
    E.set_cost(give(st, 0, sword.GILDED_BLADE), 0)
    give(st, 0, sword.RUTHLESS_ELD_SWORD)
    give(st, 0, sword.BELTEZORE)
    for _ in range(5):
        op.hand.append(op.deck.pop())
    return st
