"""Operations puzzle 2 (the analysis line's d9f691e, puzzles.md, k = 518; Salem's batch 2 game 1791387160337, action
56): original Ramp mirror, Salem at 3 facing a super-evolved Normagdala (Ward) and three small followers.
Salem's line: Erntz, the Bonus Play Point, Spilling Red discarding Vorlalai (it comes back) onto Normagdala, evolve
Vorlalai into Lyria; Erntz's turn end clears the rest and heals 8 (11)."""
from svsim.cards import dragon, neutral

from helpers import mirror_position


def build(seed: int = 0):
    """Our turn (player 0, second): turn 16, own turn 8, 10/10 play points, 3 defense, one evolution point, the Bonus
    Play Point; hand Roar of Prominence, Dragonsign, Sloth of the Crestpetal, Spilling Red, Vorlalai, Erntz, Lyria,
    Sagatsumatsu, Kimika. The enemy at 11: Lyria 1/1 Barrier, Normagdala 8/9 Ward super-evolved, Kimika 2/1, Vorlalai
    0/2 Bane; four cards in hand (unknown to us)."""
    theirs = [(neutral.LYRIA, 1, 1, 0, True), (dragon.NORMAGDALA, 8, 9, 2, True), (dragon.KIMIKA, 2, 1, 0, True),
              (dragon.VORLALAI, 0, 2, 0, True)]
    hand = [dragon.ROAR_OF_PROMINENCE, dragon.DRAGONSIGN, dragon.SLOTH_OF_THE_CRESTPETAL, dragon.SPILLING_RED,
            dragon.VORLALAI, dragon.ERNTZ, neutral.LYRIA, dragon.SAGATSUMATSU, dragon.KIMIKA]
    return mirror_position(seed, "ramp", 16, 1, (8, 8), (3, 11), ((10, 10), (0, 10)), ((1, 0), (1, 0)), hand, [],
                           theirs, 4, (25, 21), (16, 15), bonus=True)
