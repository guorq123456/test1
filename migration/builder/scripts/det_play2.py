import sys, json, random
sys.path.insert(0, "/home/user/test1")
from svsim.ui.session import Session
from svsim.ui import session as S
def fp(st):
    return json.dumps(([[c.uid for c in p.deck][-5:] for p in st.players], [[(c.uid, c.cost) for c in p.hand] for p in st.players],
            [[(c.uid, c.defn.card_id, c.atk, c.life) for c in p.field] for p in st.players], [p.leader_hp for p in st.players], [p.pp for p in st.players]))
trace = []
orig = Session._apply
def traced(self, action, who):
    trace.append((str(action), fp(self.state)))
    return orig(self, action, who)
Session._apply = traced
s = Session(); rng = random.Random(1)
v = s.start("rhino", "ramp", "strong", 195489856, "you")
steps = 0
while not v["over"] and steps < 400:
    steps += 1
    if v["active"] == 1: v = s.ai_step(); continue
    if v.get("mulligan"): v = s.mulligan([]); continue
    moves = [a for a in v["actions"] if a["type"] != "EndTurn"]
    end = next(a for a in v["actions"] if a["type"] == "EndTurn")
    v = s.act((rng.choice(moves) if moves and rng.random() < 0.7 else end)["i"])
    if s.state.turn > 8: break
json.dump(s.record, open("det_record.json", "w")); json.dump(trace, open("t_orig.json", "w"))
print("原局", len(trace), "步")
