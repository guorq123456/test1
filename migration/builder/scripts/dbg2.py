import sys, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from rhino_lethal import position
from svsim.search.combo import plan, realize, verify
from svsim.core.engine import apply
from svsim.core.enums import Keyword
from svsim.ui.text import card_name, describe
for seed in map(int, sys.argv[1:]):
    s = position(seed)
    me, opp = s.players[0], s.players[1]
    print("seed", seed, "hp", opp.leader_hp, "pp", me.pp, "combo", me.combo, "ep/sep", me.ep, me.sep, "turns", me.turns_taken,
          "\n hand", [(card_name(c.defn), c.cost) for c in me.hand],
          "\n field", [(card_name(c.defn), c.atk, c.life) for c in me.field],
          "\n enemy", [(card_name(f.defn), f.atk, f.life, "W" if f.keywords & Keyword.WARD else "") for f in opp.followers])
    t = time.perf_counter(); p = plan(s); print(" plan", p.damage, "nodes", p.nodes, round(time.perf_counter() - t, 2), "s")
    for st in p.steps: print("   ", st)
    line = realize(s, p.steps)
    print(" realized", None if line is None else len(line))
    if line:
        c = s.clone()
        for a in line:
            print("    ", describe(c, a)); apply(c, a)
        print("  hp after", c.players[1].leader_hp, "verify", verify(s, line))
