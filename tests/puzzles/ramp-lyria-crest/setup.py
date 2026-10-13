"""Operations puzzle k = 329 (the analysis line's candidates_all.md, puzzle 5; Salem's batch 1 game 1791305347029,
action 57): original Ramp mirror, Salem at 9, the enemy at 18 with a super-evolved Normagdala (Ward) and Burnite's
crest. Salem's line: Lyria with Enhance (a 7-cost follower drawn, 7 play points back), Sagatsumatsu discarding
Dragonsign, Spilling Red discarding the other Lyria onto Normagdala, Sagatsumatsu to the face: a Lyria left on the
field and a fuller hand. The bot plays Sagatsumatsu discarding Normagdala, Sloth (2 more to the face) and the same
Spilling Red. The installed evaluation prefers the bot's end (0.690 vs 0.651); G_end prefers Salem's (1.000 vs
0.854): an evaluation puzzle (analysis/puzzles3)."""
from svsim.cards import dragon, neutral
from svsim.core import effects as E

from helpers import mirror_position


def build(seed: int = 0):
    """Our turn (player 0, second): turn 16, own turn 8, 10/10 play points, 9 defense, no evolution points; hand
    Normagdala, Sloth of the Crestpetal, Sagatsumatsu, Lyria, Fate of the World, Lyria, Dragonsign, Sloth. The enemy
    at 18, 1/10 play points, with a super-evolved Normagdala 8/9 (Ward) and Crest: Burnite; two cards in hand."""
    hand = [dragon.NORMAGDALA, dragon.SLOTH_OF_THE_CRESTPETAL, dragon.SAGATSUMATSU, neutral.LYRIA,
            neutral.FATE_OF_THE_WORLD, neutral.LYRIA, dragon.DRAGONSIGN, dragon.SLOTH_OF_THE_CRESTPETAL]
    st = mirror_position(seed, "ramp", 16, 1, (8, 8), (9, 18), ((10, 10), (1, 10)), ((0, 0), (0, 0)), hand, [],
                         [(dragon.NORMAGDALA, 8, 9, 2, True)], 2, (22, 22), (14, 17))
    E.add_to_leader_area(st, 1, dragon.BURNITE_CREST)
    return st
