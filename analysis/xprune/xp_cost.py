"""+xprune's cost: ms per decision of the whole agent, level-strong (mcts:200+plan+learned+phased) with and without
+xprune, on step 1's 28 starts (bench.py's) played to the turn's end, alternating, the median of R rounds; and the
same on the bank's two operations puzzles (2 and 3), seeds 1-8. One process. Condition: the opponent's deck list is
known (order and hand not).

    python3 xp_cost.py STEP1_DIR [R] [FLAG]      (FLAG: the +xprune option, default "xprune=3:3:cost")
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
S = sys.argv[1]
R = int(sys.argv[2]) if len(sys.argv) > 2 else 3
FLAG = sys.argv[3] if len(sys.argv) > 3 else "xprune=3:3:cost"
sys.path.insert(0, f"{S}/ana")
import student_data as SD   # noqa: E402
from svsim.core.actions import EndTurn   # noqa: E402
from svsim.core.engine import apply, legal_actions   # noqa: E402
from svsim.tools.arena import make_agent   # noqa: E402
from svsim.tools.puzzles import puzzles   # noqa: E402

BASE = "mcts:200+plan+learned+phased"
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = [r for r in SD._lines(f"{S}/starts.jsonl") if r["split"] == "train"][:30]
states = [SD._state_at(games[r["game"]], r["at"]) for r in starts]
states = [s for s in states if len(legal_actions(s)) > 1]
P = {n: b for n, b, a in puzzles()}
ops = [P[n](seed) for n in ("ramp-erntz-normagdala", "ramp-erntz-spilling") for seed in range(1, 9)]


def turn(spec, positions):
    t = n = 0
    for i, s0 in enumerate(positions):
        s, agent = s0.clone(), make_agent(spec, i)
        me = s.active
        while not s.over and s.active == me:
            legal = legal_actions(s)
            t0 = time.perf_counter()
            a = agent.act(s, legal)
            t += time.perf_counter() - t0
            n += 1
            if isinstance(a, EndTurn):
                break
            apply(s, a)
    return 1000 * t / n, n


out = {}
for label, positions in (("28 starts", states), ("puzzles 2 and 3, seeds 1-8", ops)):
    turn(BASE, positions[:2])                       # warm-up
    rows = {BASE: [], BASE + "+" + FLAG: []}
    for _ in range(R):
        for spec in rows:
            rows[spec].append(turn(spec, positions))
    out[label] = {spec: {"ms_per_decision": round(statistics.median(r[0] for r in v), 1),
                         "decisions": [r[1] for r in v]} for spec, v in rows.items()}
    a, b = (out[label][s]["ms_per_decision"] for s in rows)
    out[label]["ratio"] = round(b / a, 3)
print(json.dumps(out, indent=1))
