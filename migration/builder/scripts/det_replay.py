import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
from svsim.core.engine import legal_actions
rec = json.load(open("det_record.json"))
bad = next((i for i, (st, a) in enumerate(records.steps(rec)) if a not in legal_actions(st)), None)
print("新进程重放：", "全部合法" if bad is None else f"第 {bad} 步不合法")
