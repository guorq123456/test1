import sys
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from rhino_lethal import position
from svsim.search.combo import plan, realize
from svsim.core.engine import apply
from svsim.ui.text import card_name, describe
from svsim.search.lethal import hidden_info
for seed in map(int, sys.argv[1:]):
    s = position(seed)
    p = plan(s)
    print("seed", seed, "plan", p.damage, "hp", s.players[1].leader_hp)
    for st in p.steps: print("  ", st)
    line = realize(s, p.steps)
    print("  realized:", None if line is None else len(line))
    if line:
        c = s.clone()
        for a in line:
            b = hidden_info(c)
            print("    ", describe(c, a), "LUCK" if False else "")
            apply(c, a)
            if hidden_info(c) != b: print("      (hidden info changed)")
        print("   result hp", c.players[1].leader_hp, "winner", c.winner)
