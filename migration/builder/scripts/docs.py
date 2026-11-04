import ast
import sys
from pathlib import Path

NEW = {
    "GildariaCrest": "Countdown (1). On your turn, each allied follower that enters deals 1 damage to the enemy leader.",
    "FerociousCommander": "Fanfare: summon 2 Steelclad Knights. Enhance (7): they and this follower get +3/+0 and Rush.",
    "NahtAndVince": "Fanfare: summon a Naht's Henchman, 3 damage to all enemy followers. Super-Evolve: do it again.",
    "Shaili": "Ambush. Evolve: an enemy follower can't attack until the end of your opponent's turn.",
    "Sasha": "Fanfare: summon a Steelclad Knight with Rush. Evolve: summon one with Ward.",
    "Katze": "Once on each of your turns, a spell you play deals 2 to a random enemy. Evolve: add a Gold.",
    "SharedExistence": "A random highest-attack enemy follower gets -10/-10. Enhance (6): also summon 3 Wretches.",
    "OkitaSouji": "Fanfare: evolve if super-evolution is unlocked. Rush. Follower Strike: 3 damage to it (x3 evolved).",
    "SliceOfDomesticity": "Mode: 4 damage to a random enemy follower / heal 2; both if 2+ allied cards on the field.",
    "BunnyAndBaron": "Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add a Desperados' Shot.",
    "Mars": "Fanfare: 3 Knights. Storm, Bane. Entering allied Officers: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight.",
    "BombasticBombardier": "In hand: an allied super-evolution sets its cost to 1. Fanfare: 3 damage to an enemy follower.",
    "MeasuredAttunement": "3 damage to an enemy follower. Rally (10): it can't attack until the end of the opponent's turn.",
    "MetronomicMedic": "Fanfare: draw 2 cards, summon 2 Knights. Evolve: 3 damage to an enemy follower.",
    "KnellclawLieutenant": "Fanfare: summon 3 Knights, then Mode: other allies +1/+0 and Rush, or +0/+1 and Ward.",
    "CaesuraAlFine": "6 damage to an enemy follower. Rally (10): X damage to all enemy followers, X = allied followers.",
    "Gildaria": "Fanfare: Rally (20): crest, evolve. Your turn: other allies entering get Rush. Evolved: 2 Steelclad Knights.",
    "Cesar": "Fanfare: 2 Steelclad Knights; other Swordcraft allies +1/+3, Ward. Ward. Super-Evolve: destroy an enemy.",
    "IdleMaid": "Fanfare: return a card in your hand to the deck, then draw 2 Swordcraft followers.",
    "LoyalGuard": "Enhance (4): +2/+2. Ward. Evolve: 3 damage to an enemy follower.",
    "HeartlessStrategist": "Fanfare: destroy an enemy follower. Enhance (6): also recover 3 PP, add a Fearless Soldier.",
    "RuthlessEldSword": "Mode: draw a card / 3 damage to a random enemy follower. Enhance (3): both.",
    "NoelIV": "Fanfare: Fearless Soldier with Bane, +Drain one at Enhance (7), +Storm one at (8). Super-Evolve: others +1/+1.",
    "AltruisticAristocrat": "Fanfare: discard a card in your hand; heal your leader 3, or 6 if it was a spell.",
    "SmokeShroudedBeauty": "Fanfare: with 2+ spells in hand, +1/+1 and Ward. Evolve: add a Glittering Gold.",
    "ExtravaganceOfTheGoldbloom": "Discard a spell in your hand, then twice: 3 damage to a random enemy follower.",
    "SwiftStaffmaster": "When drawn, costs 3 until the end of the turn. Fanfare: draw a card, heal your leader 3. Rush.",
    "AmphibianGoldmuncher": "Your turn end: with 2+ spells in hand, 5 damage to all enemy followers. Evolve: add 2 Golds.",
    "UnmovingTactician": "Can't attack. Your turn end: summon a Steelclad Knight. Super-Evolve: other allies +3/+3.",
    "Oluon": "Your turn end: unevolved, 7 to all enemy followers; evolved, 3 times 7 to another random target.",
    "KnightlyArdor": "Mode: leftmost Swordcraft ally attacks twice / Swordcraft allies +1/+1, Barrier / 2 PP, 1 EP / heal 6.",
    "Seofon": "Fanfare: Skybound Art: evolve all unevolved allies (itself too). Super Skybound Art: super-evolve.",
}

path = Path(sys.argv[1])
src = path.read_text()
lines = src.split("\n")
tree = ast.parse(src)
edits = []
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name in NEW:
        d = node.body[0]
        edits.append((d.lineno, d.end_lineno, NEW.pop(node.name)))
assert not NEW, NEW
for start, end, text in sorted(edits, reverse=True):
    line = f'    """{text}"""'
    if len(line) > 112:
        print("LONG", len(line), line)
    lines[start - 1:end] = [line]
path.write_text("\n".join(lines))
