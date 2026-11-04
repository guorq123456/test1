import subprocess, sys
P = "svsim/cards/dragon.py"
orig = open(P).read()
M = [
 ("for _ in range(3 if ctx.enhanced else 1):", "for _ in range(2 if ctx.enhanced else 1):"),
 ("E.buff(ctx.state, ctx.source, 5, 5)", "E.buff(ctx.state, ctx.source, 5, 4)"),
 ("        E.heal_leader(ctx.state, ctx.controller, 1)\n        if E.overflow(ctx.state, ctx.controller):", "        E.heal_leader(ctx.state, ctx.controller, 1)\n        if True:"),
 ("        for _ in range(2):\n            E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)", "        for _ in range(1):\n            E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)"),
 ("others = [f for f in ctx.me.followers if f is not ctx.source and not f.evolved]", "others = [f for f in ctx.me.followers if not f.evolved]"),
 ("lambda c: c.defn.cost >= 5)", "lambda c: c.defn.cost >= 1)"),
 ("        if _discard_random_clue(ctx):\n            E.draw_matching", "        _discard_random_clue(ctx)\n        if True:\n            E.draw_matching"),
 ("        if _discard_random_clue(ctx):\n            E.gain_max_pp", "        _discard_random_clue(ctx)\n        if True:\n            E.gain_max_pp"),
 ("ctx.me.followers[:2]", "ctx.me.followers[:3]"),
 ("if c.defn.cost <= 4]", "if c.defn.cost < 4]"),
 ("        for _ in range(x):\n            E.damage(ctx.state, _random_enemy_follower(ctx), 8", "        for _ in range(x + 1):\n            E.damage(ctx.state, _random_enemy_follower(ctx), 8"),
 ("x = enemy.leader_max_hp - enemy.leader_hp", "x = enemy.leader_max_hp - enemy.leader_hp - 1"),
 ("Keyword.STORM | Keyword.WARD)", "Keyword.STORM)"),
 ("    def last_words(self, ctx):\n        E.add_to_hand(ctx.state, ctx.controller, DIVINE_EVIDENCE)", "    def last_words(self, ctx):\n        pass"),
 ("    def on_evolve(self, ctx):\n        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)\n\n\n@register(BIRDS", "    def on_evolve(self, ctx):\n        E.damage(ctx.state, ctx.chosen(), 2, ctx.source)\n\n\n@register(BIRDS"),
 ("            E.summon(ctx.state, ctx.controller, INQUIRING_MISCHIEF)", "            pass"),
 ("            E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)\n\n\n@register(LEIZAUT", "            pass\n\n\n@register(LEIZAUT"),
 ("        E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)\n        # The draw", "        # The draw"),
]
caught = 0
try:
    for i, (a, b) in enumerate(M):
        assert orig.count(a) == 1, (i, a)
        open(P, "w").write(orig.replace(a, b))
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/test_set10_dragon.py"], capture_output=True)
        ok = r.returncode != 0
        caught += ok
        print(i, "caught" if ok else "SURVIVED", a[:60].replace("\n", " "))
finally:
    open(P, "w").write(orig)
print(f"{caught}/{len(M)} caught")
