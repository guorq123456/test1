"""Operations puzzle 1 (the analysis line's d9f691e, puzzles.md, k = 320; Salem's batch 1 game 1791305215412, action
39): original Ramp mirror, Salem at 9 facing a super-evolved Erntz. Salem's line: Kimika discarding Vorlalai (it
comes back) and drawing Sagatsumatsu, super-evolve Vorlalai (three Depths), Sagatsumatsu discarding a Depths (two
Spilling Red), Spilling Red discarding a Depths onto Erntz, Sagatsumatsu to the face. It rests on Kimika's draw
(Sagatsumatsu: 3 of the 27 cards left); the bot played Erntz and ended."""
from svsim.cards import dragon
from svsim.core.enums import Keyword

from helpers import mirror_position


def build(seed: int = 0):
    """Our turn (player 0, first): turn 13, own turn 7, 10/10 play points, 9 defense, two evolution and two
    super-evolution points; hand Burnite, Roar of Prominence, Erntz, Vorlalai, Burnite, Lumiore & Argente, Kimika.
    The enemy at 20 with a super-evolved Erntz 11/11 (Intimidate); three cards in hand (unknown to us)."""
    erntz = (dragon.ERNTZ, 11, 11, 2, True, Keyword.INTIMIDATE)
    hand = [dragon.BURNITE, dragon.ROAR_OF_PROMINENCE, dragon.ERNTZ, dragon.VORLALAI, dragon.BURNITE,
            dragon.LUMIORE_AND_ARGENTE, dragon.KIMIKA]
    return mirror_position(seed, "ramp", 13, 0, (7, 6), (9, 20), ((10, 10), (0, 9)), ((2, 2), (0, 1)), hand, [],
                           [erntz], 3, (27, 30), (8, 7))
