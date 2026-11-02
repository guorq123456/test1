import sys
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from rhino_lethal import position
from svsim.search import combo as C
from svsim.core.engine import apply, legal_actions
from svsim.ui.text import card_name, describe
seed = int(sys.argv[1])
s = position(seed)
p = C.plan(s)
# step-by-step realize with diagnostics
for k in range(1, len(p.steps) + 1):
    line = C.realize(s, p.steps[:k])
    if line is None:
        print("fails at step", k, p.steps[k - 1])
        prev = C.realize(s, p.steps[:k - 1]); c = s.clone()
        for a in prev: apply(c, a)
        me = c.players[0]
        print("  hand", [(card_name(x.defn), x.cost, x.uid) for x in me.hand])
        print("  field", [(card_name(x.defn), x.atk, x.life, x.attacks_made, x.uid) for x in me.field])
        print("  enemy", [(card_name(x.defn), x.atk, x.life, x.uid) for x in c.players[1].followers])
        print("  legal", [describe(c, a) for a in legal_actions(c)][:40])
        break
else:
    c = s.clone()
    for a, st in zip(line, p.steps):
        apply(c, a)
        me = c.players[0]
        print(f"{describe(c, a) if False else st[0]:8} combo {me.combo} pp {me.pp} opp hp {c.players[1].leader_hp} | field",
              [(card_name(x.defn), x.atk, x.life) for x in me.field], "| enemy", [(x.atk, x.life) for x in c.players[1].followers])
