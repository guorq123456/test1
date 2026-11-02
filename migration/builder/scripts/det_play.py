"""用 mcts:200+plan 当 AI 打一局（人类一方随机点），存记录，并在同一进程里重放检查。"""
import sys, json, random
sys.path.insert(0, "/home/user/test1")
from svsim.ui.session import Session
from svsim.tools import records
from svsim.core.engine import legal_actions
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
json.dump(s.record, open("det_record.json", "w"))
bad = next((i for i, (st, a) in enumerate(records.steps(s.record)) if a not in legal_actions(st)), None)
print("同进程重放：", "全部合法" if bad is None else f"第 {bad} 步不合法", "共", len(s.record["actions"]), "步")
