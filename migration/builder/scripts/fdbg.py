import sys
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from rhino_lethal import position
from svsim.search.combo import plan
from svsim.search.formula import estimate
from svsim.core.enums import Keyword
from svsim.ui.text import card_name
for seed in map(int, sys.argv[1:]):
    s = position(seed); me, opp = s.players[0], s.players[1]
    print("== seed", seed, "hp", opp.leader_hp, "pp", me.pp, "ep/sep", me.ep, me.sep,
          "\n hand", [(card_name(c.defn), c.cost) for c in me.hand], "\n field", [(card_name(c.defn), c.atk, c.life) for c in me.field],
          "\n enemy", [(card_name(f.defn), f.atk, f.life, "W" if f.keywords & Keyword.WARD else "", "B" if f.keywords & Keyword.BARRIER else "") for f in opp.followers])
    print(estimate(s).text(opp.leader_hp))
    for st in plan(s).steps: print("   ", st[:2], st[2:] if st[0] != "play" else st[3:])
