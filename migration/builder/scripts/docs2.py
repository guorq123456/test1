import ast
import sys
from pathlib import Path

NEW = {
    "GildariaCrest": "Countdown (1). On your turn, allied followers entering deal 1 damage to the enemy leader.",
    "OkitaSouji": "Fanfare: evolve if super-evolution is unlocked. Follower Strike: 3 damage (x3 if evolved).",
    "BunnyAndBaron": "Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot.",
    "Mars": "Fanfare: 3 Knights. Entering Officer allies: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight.",
    "MeasuredAttunement": "3 damage to an enemy follower. Rally (10): it can't attack until the opponent's turn ends.",
    "CaesuraAlFine": "6 damage to an enemy follower. Rally (10): X to all enemy followers, X = allied followers.",
    "Gildaria": "Fanfare: Rally (20): crest, evolve. Your turn: entering allies get Rush. Evolves: 2 Steelclads.",
    "Cesar": "Fanfare: 2 Steelclads; other Swordcraft allies +1/+3, Ward. Super-Evolve: destroy an enemy.",
    "NoelIV": "Fanfare: Bane soldier; Enhance (7): +Drain one; (8): +Storm one. Super-Evolve: others +1/+1.",
    "Oluon": "Turn end: unevolved, 7 to all enemy followers; evolved, 3 times 7 to another random target.",
    "KnightlyArdor": "Mode: leftmost Sword ally attacks twice / Sword allies +1/+1, Barrier / 2 PP, 1 EP / heal 6.",
    "Seofon": "Fanfare: Skybound Art: evolve all unevolved allies (itself too); Super: super-evolve them.",
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
bad = False
for start, end, text in sorted(edits, reverse=True):
    line = f'    """{text}"""'
    if len(line) > 105:
        print("LONG", len(line), line)
        bad = True
    lines[start - 1:end] = [line]
if not bad:
    path.write_text("\n".join(lines))
    print("written")
