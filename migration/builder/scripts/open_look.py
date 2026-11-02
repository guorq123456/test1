import sys, pickle
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from rhino_lethal import position
from svsim.ui.text import card_name
from svsim.core.enums import Keyword
res = pickle.load(open("rhino_combo.pkl", "rb"))
for r in res:
    if r[2] == "search" and not r[1]:
        s = position(r[0])
        me, opp = s.players[0], s.players[1]
        print(r[0], "ceiling", r[3], "hp", r[4], "pp", me.pp,
              "hand", [card_name(c.defn) for c in me.hand],
              "| field", [card_name(c.defn) for c in me.field],
              "| enemy", [(card_name(f.defn), f.atk, f.life, "W" if f.keywords & Keyword.WARD else "") for f in opp.followers])
