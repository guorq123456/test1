"""ms per decision, the candidate against level-strong (the same search; only the turn-end weights differ): every
decision of a turn played from each of the first N step-1 turn starts, both specs on the same start and seed,
alternating which goes first. usage: ms.py STEP1_DIR [N]"""
import json, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2])); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.core.engine import apply, legal_actions
from svsim.tools.arena import make_agent
SPECS = {"level-strong": "level-strong", "cand-th": "mcts:200+plan+learned+phased=cand-th-ramp-ramp"}
d, N = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60
games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
starts = list(SD._lines(f"{d}/starts.jsonl"))[:N]
ms = {k: [] for k in SPECS}
for i, r in enumerate(starts):
    order = list(SPECS) if i % 2 == 0 else list(SPECS)[::-1]
    for name in order:
        s = SD._state_at(games[r["game"]], r["at"])
        me, agent = s.active, make_agent(SPECS[name], 1000 + i)
        while not s.over and s.active == me:
            legal = legal_actions(s)
            t = time.perf_counter()
            a = agent.act(s, legal)
            ms[name].append((time.perf_counter() - t) * 1000)
            apply(s, a)
out = {k: {"decisions": len(v), "mean": round(statistics.mean(v), 1), "median": round(statistics.median(v), 1)}
       for k, v in ms.items()}
out["ratio_mean"] = round(out["cand-th"]["mean"] / out["level-strong"]["mean"], 3)
print(json.dumps(out))
