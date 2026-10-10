"""Operations puzzle 3 (the analysis line's d9f691e, puzzles.md, k = 445; Salem's batch 2 game 1791317238047, action
49): original Ramp mirror, Salem at 5 facing a super-evolved Erntz (8 to our leader at their turn's end). Salem's
line: Spilling Red discarding Vorlalai (it comes back) onto Erntz, the Bonus Play Point, Erntz (Ward, heals 8: 13)."""
from svsim.cards import dragon
from svsim.core.enums import Keyword

from helpers import mirror_position


def build(seed: int = 0):
    """Our turn (player 0, second): turn 16, own turn 8, 10/10 play points, 5 defense, two super-evolution points,
    the Bonus Play Point; hand Erntz, Lumiore & Argente, Sloth of the Crestpetal, Spilling Red, Vorlalai. The enemy
    at 13 with a super-evolved Erntz 11/11 (Intimidate); five cards in hand (unknown to us)."""
    erntz = (dragon.ERNTZ, 11, 11, 2, True, Keyword.INTIMIDATE)
    hand = [dragon.ERNTZ, dragon.LUMIORE_AND_ARGENTE, dragon.SLOTH_OF_THE_CRESTPETAL, dragon.SPILLING_RED,
            dragon.VORLALAI]
    return mirror_position(seed, "ramp", 16, 1, (8, 8), (5, 13), ((10, 10), (0, 10)), ((0, 2), (1, 0)), hand, [],
                           [erntz], 5, (27, 25), (14, 9), bonus=True)
