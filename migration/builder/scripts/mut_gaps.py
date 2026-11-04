"""The reviewer's 17 surviving mutants, by line: each must now fail a test (no bytecode)."""
import subprocess, sys
D, F, S = "svsim/cards/dragon.py", "svsim/cards/forest.py", "svsim/cards/sword.py"
M = [  # (file, line, old, new)
 (D, 545, "_clues_in_hand(ctx), 1)", "_clues_in_hand(ctx), 2)"),
 (D, 599, "others, 1)", "others, 2)"),
 (D, 583, "ENEMY_FOLLOWER, 2)", "ENEMY_FOLLOWER, 3)"),
 (D, 635, "(4, 2)", "(5, 2)"),
 (D, 635, "(4, 2)", "(4, 3)"),
 (D, 661, "8, ctx.source", "9, ctx.source"),
 (D, 672, "x > 0", "x > 1"),
 (F, 350, "WOLF_PACK_LACKEY, 2)", "WOLF_PACK_LACKEY, 3)"),
 (F, 410, "5, ctx.source", "6, ctx.source"),
 (F, 426, "2, 0, exclude", "2, 1, exclude"),
 (S, 554, "max(0, atk)", "max(1, atk)"),
]
# Bird's-Eye View: swap modes 0/1 and 2/3 in the cast body
BEV = [("if 0 in ctx.modes:\n            E.summon(ctx.state, ctx.controller, INQUIRING_MISCHIEF)\n        if 1 in ctx.modes:",
        "if 1 in ctx.modes:\n            E.summon(ctx.state, ctx.controller, INQUIRING_MISCHIEF)\n        if 0 in ctx.modes:"),
       ("        if 2 in ctx.modes:\n            for _ in range(3):\n                E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)\n        if 3 in ctx.modes:",
        "        if 3 in ctx.modes:\n            for _ in range(3):\n                E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)\n        if 2 in ctx.modes:")]
TESTS = ["tests/test_set10_dragon.py", "tests/test_set10_forest.py", "tests/test_set10_sword.py"]
def run():
    return subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *TESTS],
                          capture_output=True).returncode != 0
caught = total = 0
for path, line, old, new in M:
    src = open(path).read(); lines = src.split("\n")
    assert lines[line - 1].count(old) == 1, (path, line, lines[line - 1])
    lines[line - 1] = lines[line - 1].replace(old, new)
    try:
        open(path, "w").write("\n".join(lines)); c = run()
    finally:
        open(path, "w").write(src)
    total += 1; caught += c; print("CAUGHT" if c else "MISSED", path, line, old, "->", new)
for old, new in BEV:
    src = open(D).read(); assert src.count(old) == 1
    try:
        open(D, "w").write(src.replace(old, new)); c = run()
    finally:
        open(D, "w").write(src)
    total += 1; caught += c; print("CAUGHT" if c else "MISSED", "bird's-eye view mode swap")
print(f"{caught}/{total}")
