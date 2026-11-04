import subprocess, sys
P = "svsim/cards/neutral.py"
orig = open(P).read()
M = [
 ("exias no evidence", "    def fanfare(self, ctx):\n        E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)\n\n\n@register(DYNAMES", "    def fanfare(self, ctx):\n        pass\n\n\n@register(DYNAMES"),
 ("dynames evolve no replicate", "    def on_evolve(self, ctx):\n        self._testify(ctx)\n\n    def _testify", "    def on_evolve(self, ctx):\n        pass\n\n    def _testify"),
 ("scene summons own side", "E.summon(ctx.state, 1 - ctx.controller, DIVINE_EVIDENCE)", "E.summon(ctx.state, ctx.controller, DIVINE_EVIDENCE)"),
 ("scene destroys", "            E.banish(ctx.state, target)\n        # Unconditional", "            E.destroy(ctx.state, target)\n        # Unconditional"),
 ("scene summon conditional", "        for target in _random_enemy_follower(ctx):\n            E.banish(ctx.state, target)\n        # Unconditional: the Chinese text makes the summon its own sentence.\n        E.summon", "        for target in _random_enemy_follower(ctx):\n            E.banish(ctx.state, target)\n            E.summon"),
 ("kyrios one evidence", "        for _ in range(2):\n            E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)", "        for _ in range(1):\n            E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)"),
 ("kyrios 1 damage", "E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)\n        for _ in range(2)", "E.damage(ctx.state, list(ctx.opponent.followers), 1, ctx.source)\n        for _ in range(2)"),
 ("rezeal 10 damage", "E.damage(ctx.state, ctx.chosen(), 9, ctx.source)\n\n    def on_super_evolve", "E.damage(ctx.state, ctx.chosen(), 10, ctx.source)\n\n    def on_super_evolve"),
 ("rezeal crest on evolve", "    def on_super_evolve(self, ctx):\n        E.add_to_leader_area(ctx.state, ctx.controller, REZEAL_CREST)", "    def on_evolve(self, ctx):\n        E.add_to_leader_area(ctx.state, ctx.controller, REZEAL_CREST)"),
 ("crest no cant-attack", "        E.grant(played, CANT_ATTACK, common.end_of_turn(ctx))", "        pass"),
 ("crest cant-attack permanent", "        E.grant(played, CANT_ATTACK, common.end_of_turn(ctx))", "        E.grant(played, CANT_ATTACK)"),
 ("crest no last words", "        E.grant(played, SUMMON_COPY_ON_DEATH)\n", ""),
]
caught = 0
try:
  pass
finally:
  pass
for name, a, b in M:
    assert orig.count(a) == 1, name
for name, a, b in M:
    open(P, "w").write(orig.replace(a, b))
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_set10_neutral.py", "tests/test_clue.py"], capture_output=True)
    ok = r.returncode != 0
    caught += ok
    print(("CAUGHT " if ok else "MISSED ") + name)
open(P, "w").write(orig)
print(f"{caught}/{len(M)}")
