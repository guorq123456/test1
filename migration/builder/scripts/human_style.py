"""你的打法：每回合手牌数、出牌数、PP 用量、破魔虫下场（连击、伤害）、打脸伤害。"""
import json, glob, sys
sys.path.insert(0, "/home/user/test1")
from collections import defaultdict
from svsim.tools import records
from svsim.cards import unlimited as U
from svsim.core.actions import PlayCard, Attack, EndTurn, Evolve, Engage, Fuse, Mulligan
from svsim.core.state import leader_uid
from svsim.ui.text import card_name
for f in sorted(glob.glob("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/dbgames2/games/*.json")):
    body = json.load(open(f)); body = body.get("data", body); rec = body["record"]
    if not body.get("finished"): continue
    print(f"\n===== {f.split('/')[-1][:13]}（{'你先手' if rec['first']==0 else 'AI 先手'}）=====")
    turn = None; row = None; rows = []
    for state, a in records.steps(rec):
        me, ai = state.players
        if isinstance(a, Mulligan):
            if state.active == 0:
                print("  起手:", [card_name(c.defn) for c in me.hand], "换掉:", [card_name(me.hand[i].defn) for i in a.indices])
            continue
        if state.active != 0:
            continue
        if state.turn != turn:
            turn = state.turn
            row = {"t": me.turns_taken, "pp": me.max_pp, "hand0": len(me.hand), "plays": [], "rhino": [], "spent": 0,
                   "ai_hp0": ai.leader_hp, "evolve": "", "end_hand": None}
            rows.append(row)
        if isinstance(a, PlayCard):
            c = state.in_hand(0, a.uid)
            row["plays"].append(card_name(c.defn)); row["spent"] += c.cost
            if c.defn == U.KILLER_RHINOCEROACH:
                row["rhino"].append(me.combo + 1)
        elif isinstance(a, Evolve):
            row["evolve"] = ("超进化" if a.super_ else "进化") + card_name(state.on_field(a.uid).defn)
        elif isinstance(a, Fuse):
            row["plays"].append("融合")
        elif isinstance(a, EndTurn):
            row["end_hand"] = len(me.hand); row["ai_hp1"] = ai.leader_hp; row["pp_left"] = me.pp
    for r in rows:
        dealt = r["ai_hp0"] - r.get("ai_hp1", r["ai_hp0"] if r["end_hand"] is None else r["ai_hp0"])
        rh = f" 破魔虫×{len(r['rhino'])}（连击 {'/'.join(map(str, r['rhino']))}）" if r["rhino"] else ""
        print(f"  你第{r['t']:>2}回合 PP{r['pp']:>2} 手牌 {r['hand0']}→{r['end_hand']} 出{len(r['plays'])}张 花{r['spent']}费"
              f" 剩{r.get('pp_left','?')}费 打脸{dealt if r['end_hand'] is not None else '(斩杀)'}{rh} {r['evolve']}")
        if r["plays"]: print("        ", "、".join(r["plays"]))
