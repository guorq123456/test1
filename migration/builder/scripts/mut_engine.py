import subprocess, sys
M = [
 ("svsim/core/effects.py", "        emit(state, \"on_card_banished\", other=inst)\n", ""),
 ("svsim/core/effects.py", "    if amulet is None or counters(amulet).get(\"clues\", 0) < n:\n        return False\n    consume_clue", "    if amulet is None or counters(amulet).get(\"clues\", 0) <= n:\n        return False\n    consume_clue"),
 ("svsim/core/engine.py", "    E.emit(state, \"on_ally_fuse\", player=p.index, other=card, cards=tuple(fodder))\n", ""),
 ("svsim/core/engine.py", "    E.emit(state, \"on_ally_fuse\", player=p.index, other=card, cards=tuple(fodder))\n", "    E.emit(state, \"on_ally_fuse\", other=card, cards=tuple(fodder))\n"),
 ("svsim/core/engine.py", "    p.amulet_engaged_turn = state.turn\n", ""),
 ("svsim/core/engine.py", "                E.enqueue(state, \"on_turn_start\", card, p.index, zone=None)\n", ""),
 ("svsim/core/state.py", "        clone.amulet_engaged_turn = self.amulet_engaged_turn\n", ""),
]
caught = 0
for p, a, b in M:
    orig = open(p).read(); assert orig.count(a) == 1, a
for p, a, b in M:
    orig = open(p).read()
    try:
        open(p, "w").write(orig.replace(a, b))
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_set10_engine.py", "tests/test_cards_portal.py"], capture_output=True)
    finally:
        open(p, "w").write(orig)
    caught += r.returncode != 0
    print("CAUGHT" if r.returncode else "MISSED", p, a.strip()[:60])
print(f"{caught}/{len(M)}")
