import subprocess, sys
p='svsim/cards/forest.py'
orig=open(p).read()
M=[
 ("helper base cost", "return sum(c.defn.cost == 1 for c in ctx.me.field if c is not exclude)", "return sum(c.cost == 1 for c in ctx.me.field if c is not exclude)"),
 ("crest", "    def on_turn_start(self, ctx):\n        _summon(ctx, INQUIRING_MISCHIEF)", "    def on_turn_start(self, ctx):\n        pass"),
 ("dogsitter fanfare", "    def fanfare(self, ctx):\n        _summon(ctx, DIVINE_EVIDENCE)\n\n    def on_evolve(self, ctx):\n        if _one_cost_allies(ctx) >= 2:\n            E.heal_leader", "    def fanfare(self, ctx):\n        pass\n\n    def on_evolve(self, ctx):\n        if _one_cost_allies(ctx) >= 2:\n            E.heal_leader"),
 ("dogsitter cond", "        if _one_cost_allies(ctx) >= 2:\n            E.heal_leader(ctx.state, ctx.controller, 2)", "        if _one_cost_allies(ctx) >= 1:\n            E.heal_leader(ctx.state, ctx.controller, 2)"),
 ("lackey evolve", "    def on_evolve(self, ctx):\n        _summon(ctx, WOLF_PACK_LACKEY, 2)", "    def on_evolve(self, ctx):\n        _summon(ctx, WOLF_PACK_LACKEY, 1)"),
 ("reincarnation enhance", "3 if ctx.enhanced else 1", "1"),
 ("reincarnation evolve", "        for fairy in _summon(ctx, FAIRY, 3 if ctx.enhanced else 1):\n            _evolve(ctx, fairy)", "        for fairy in _summon(ctx, FAIRY, 3 if ctx.enhanced else 1):\n            pass"),
 ("mischief other", "        if _one_cost_allies(ctx, exclude=ctx.source) >= 2:", "        if _one_cost_allies(ctx) >= 2:"),
 ("garden elf", "        _add(ctx, DEEPWOOD_BOUNTY)\n        _add(ctx, FAIRY)", "        _add(ctx, DEEPWOOD_BOUNTY)"),
 ("testimony crest", "        _gain_crest(ctx, UNTAMED_TESTIMONY_CREST)", "        pass"),
 ("sleuth evolve cond", "        if _one_cost_allies(ctx) >= 2:\n            _summon(ctx, INQUIRING_MISCHIEF)", "        if _one_cost_allies(ctx) >= 1:\n            _summon(ctx, INQUIRING_MISCHIEF)"),
 ("interrogation dmg", "E.damage(ctx.state, _random_enemy_follower(ctx), 5, ctx.source)\n        for mischief", "E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)\n        for mischief"),
 ("interrogation storm", "            if _one_cost_allies(ctx) >= 2:\n                E.give_keywords(mischief, Keyword.STORM)", "            if True:\n                E.give_keywords(mischief, Keyword.STORM)"),
 ("nosche fanfare", "        _summon(ctx, SLEUTHS_BEST_FRIEND)\n        _summon(ctx, INQUIRING_MISCHIEF)", "        _summon(ctx, SLEUTHS_BEST_FRIEND)"),
 ("nosche exclude", "        _buff_all_allies(ctx, 2, 0, exclude=ctx.source)", "        _buff_all_allies(ctx, 2, 0)"),
 ("hyphae craft", "c.defn.is_follower and c.defn.craft == Craft.FOREST and c in p.hand", "c.defn.is_follower and c in p.hand"),
 ("hyphae super", "    def on_super_evolve(self, ctx):\n        self._sow(ctx)", "    def on_super_evolve(self, ctx):\n        pass"),
 ("hyphae full field", "                        and len(p.field) < FIELD_LIMIT):\n                    p.hand.remove(c)\n                    E.enter_field", "                        ):\n                    p.hand.remove(c)\n                    E.enter_field"),
]
caught=0
for name,a,b in M:
    assert orig.count(a)==1,(name,orig.count(a))
    open(p,'w').write(orig.replace(a,b))
    r=subprocess.run([sys.executable,"-m","pytest","-q","-x","-p","no:cacheprovider","tests/test_set10_forest.py"],capture_output=True,text=True)
    ok=r.returncode!=0; caught+=ok
    print(("CAUGHT " if ok else "MISSED ")+name)
open(p,'w').write(orig)
print(f"{caught}/{len(M)}")
