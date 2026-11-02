import hashlib, json, sys
sys.path.insert(0, "."); sys.path.insert(0, f"{sys.argv[1]}/ana")
import student_data as SD
from svsim.core.engine import legal_actions
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search
S = sys.argv[1]
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = [r for r in SD._lines(f"{S}/starts.jsonl")][:120]
out = []
for i, r in enumerate(starts):
    s = SD._state_at(games[r["game"]], r["at"])
    if len(legal_actions(s)) < 2: continue
    agent = make_agent("mcts:200+plan+learned+phased", i)
    a = agent.act(s.clone(), legal_actions(s)); root = _search(agent).last_root
    out.append([repr(a), None if root is None else sorted([repr(k), c.visits, repr(c.value)] for k, c in root.children.items())])
print(len(out), hashlib.sha256(json.dumps(out).encode()).hexdigest())
