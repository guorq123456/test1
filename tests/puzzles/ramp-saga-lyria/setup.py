"""Operations puzzle k = 455 (the analysis line's candidates_all.md, puzzle 4; Salem's batch 2 game 1791317476826,
action 59): original Ramp mirror, Salem at 11, the enemy at 9 with Lyria (Barrier) and an evolved Sagatsumatsu 7/6.
Salem's line: Roar of Prominence, Spilling Red discarding Depths (1 to the face) onto Lyria, Dragonsign, Sloth: the
enemy at 6, their board empty, an evolution point kept. The bot plays Kimika, Sagatsumatsu and trades. The installed
evaluation prefers the bot's end (0.32-0.38 vs 0.272); G_end prefers Salem's (0.583 vs 0.125): an evaluation
puzzle (analysis/puzzles3)."""
from svsim.cards import dragon, neutral

from helpers import mirror_position


def build(seed: int = 0):
    """Our turn (player 0, second): turn 18, own turn 9, 10/10 play points, 11 defense, one evolution point; hand Roar
    of Prominence, Zooey, Spilling Red, Depths of the Eld Blades, Spilling Red, Spilling Red, Kimika, Dragonsign,
    Sloth of the Crestpetal. The enemy at 9 with Lyria 1/1 (Barrier) and an evolved Sagatsumatsu 7/6 (Storm, Bane,
    Aura); four cards in hand."""
    theirs = [(neutral.LYRIA, 1, 1, 0, True), (dragon.SAGATSUMATSU, 7, 6, 1, True)]
    hand = [dragon.ROAR_OF_PROMINENCE, dragon.ZOOEY, dragon.SPILLING_RED, dragon.DEPTHS_OF_THE_ELD_BLADES,
            dragon.SPILLING_RED, dragon.SPILLING_RED, dragon.KIMIKA, dragon.DRAGONSIGN, dragon.SLOTH_OF_THE_CRESTPETAL]
    return mirror_position(seed, "ramp", 18, 1, (9, 9), (11, 9), ((10, 10), (0, 10)), ((1, 0), (1, 2)), hand, [],
                           theirs, 4, (23, 25), (18, 14))
