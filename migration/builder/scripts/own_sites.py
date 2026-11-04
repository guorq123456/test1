import collections, sys, traceback
sys.path.insert(0, "."); sys.path.insert(0, f"{sys.argv[1]}/ana")
import student_data as SD
from svsim.core import state as ST
from svsim.core.engine import legal_actions
from svsim.tools.arena import make_agent
sites = collections.Counter()
orig = ST.PlayerState._own_deck
def spy(self):
    f = traceback.extract_stack(limit=4)[-3]
    sites[f"{f.filename.split('svsim/')[-1]}:{f.lineno} {f.name}"] += 1
    orig(self)
ST.PlayerState._own_deck = spy
S = sys.argv[1]
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = list(SD._lines(f"{S}/starts.jsonl"))[:40]
for i, r in enumerate(starts):
    s = SD._state_at(games[r["game"]], r["at"])
    if len(legal_actions(s)) > 1:
        make_agent("mcts:200+plan+learned+phased", i).act(s.clone(), legal_actions(s))
for k, v in sites.most_common(25): print(v, k)
