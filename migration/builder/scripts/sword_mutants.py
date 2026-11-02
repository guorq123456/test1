"""Mutation checks for the set-10 Sword scripts: each mutant must make tests/test_set10_sword.py fail."""
import subprocess

PATH = "svsim/cards/sword.py"
MUTANTS = [
    ("clue filter", "        if E.is_clue(ctx.other):\n            _swap_stats", "        if True:\n            _swap_stats"),
    ("no +1/+0", "            E.buff(ctx.state, ctx.source, 1, 0)\n", "            E.buff(ctx.state, ctx.source, 0, 0)\n"),
    ("max_life kept", "    inst.atk, inst.life, inst.max_life = max(0, atk), life, life", "    inst.atk, inst.life = max(0, atk), life"),
    ("not in hand", "    listen_in_hand = True\n\n    def on_engage", "    listen_in_hand = False\n\n    def on_engage"),
    ("newsie enhance always", "        if ctx.enhanced and _on_field(ctx, ctx.source):\n            E.summon_copy", "        if _on_field(ctx, ctx.source):\n            E.summon_copy"),
    ("newsie no last words", "    def last_words(self, ctx):\n        E.summon(ctx.state, ctx.controller, DIVINE_EVIDENCE)", "    def last_words(self, ctx):\n        pass"),
    ("lady not once", 'E.once_per_turn(ctx, "bejeweled")', "True"),
    ("lady no leader", "list(ctx.opponent.followers) + [common.enemy_leader(ctx)], 2,", "list(ctx.opponent.followers), 2,"),
    ("lady no necklace", "        _add(ctx, GILDED_NECKLACE)\n\n    def on_play", "        pass\n\n    def on_play"),
    ("onward no barrier", "            E.give_keywords(knight, Keyword.BARRIER)", "            pass"),
    ("onward not evolved", "            E.evolve(ctx.state, knight)\n", "            pass\n"),
    ("architect X=1", "        _hit_selected(ctx, ctx.source.atk)", "        _hit_selected(ctx, 1)"),
    ("architect no evidence", "        _hit_selected(ctx, ctx.source.atk)\n        E.summon(ctx.state, ctx.controller, DIVINE_EVIDENCE)", "        _hit_selected(ctx, ctx.source.atk)"),
    ("architect evolve none", "    def on_evolve(self, ctx):\n        E.summon(ctx.state, ctx.controller, GUILELESS_NEWSIE)", "    def on_evolve(self, ctx):\n        pass"),
    ("errant no condition", "        if _allied_amulet(ctx):", "        if True:"),
    ("errant on plain evolve", "    def on_super_evolve(self, ctx):\n        self._banish(ctx)", "    def on_evolve(self, ctx):\n        self._banish(ctx)"),
    ("forensics 5", "10 if _engaged_clue(ctx) else 5", "5"),
    ("placid stats swapped", "            _set_stats(newsie, atk, life)", "            _set_stats(newsie, life, atk)"),
    ("placid bane self", "        for f in [f for f in ctx.me.followers if f is not ctx.source]:\n            E.give_keywords(f, Keyword.BANE)", "        for f in list(ctx.me.followers):\n            E.give_keywords(f, Keyword.BANE)"),
    ("cross-exam no condition", "        if _engaged_clue(ctx):\n            E.summon(ctx.state, ctx.controller, GUILELESS_NEWSIE)", "        if True:\n            E.summon(ctx.state, ctx.controller, GUILELESS_NEWSIE)"),
    ("no life branches", "        if me.atk < me.life:", "        if me.atk > me.life:"),
    ("no life no copy", "        copy = E.summon_copy(ctx.state, ctx.controller, me) if _on_field(ctx, me) else None", "        copy = None"),
    ("almaelys no gold", "    def fanfare(self, ctx):\n        _add(ctx, GLITTERING_GOLD)\n\n    def on_evolve(self, ctx):\n        E.add_to_leader_area", "    def fanfare(self, ctx):\n        pass\n\n    def on_evolve(self, ctx):\n        E.add_to_leader_area"),
    ("almaelys delay 1", "            E.advance_countdown(ctx.state, crest, -2)\n\n\n@register(ALMAELYS_CREST", "            E.advance_countdown(ctx.state, crest, -1)\n\n\n@register(ALMAELYS_CREST"),
    ("crest stops at 2", "(GILDED_BLADE, GILDED_GOBLET)[step % 2]", "(GILDED_BLADE, GILDED_GOBLET)[min(step, 1)]"),
    ("crest full cost", "        if token is not None:\n            E.set_cost(token, 0)", "        pass"),
]

original = open(PATH).read()
caught = 0
try:
    for name, old, new in MUTANTS:
        assert original.count(old) == 1, name
        open(PATH, "w").write(original.replace(old, new))
        r = subprocess.run(["python3", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                            "tests/test_set10_sword.py"], capture_output=True, text=True)
        killed = r.returncode != 0
        caught += killed
        print(("caught " if killed else "SURVIVED ") + name)
finally:
    open(PATH, "w").write(original)
print(f"{caught} of {len(MUTANTS)} mutants caught")
