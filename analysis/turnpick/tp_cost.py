"""The turn pick's cost against level-strong: on the first N training starts of step 1 (starts.jsonl order, split
train), each agent plays the mover's whole turn from the start on the real position (seed 7, one process, one
thread); per turn the milliseconds, the decisions, and the search decisions (more than one legal action); for the
pick also its own time (plans and their scores) and what it chose.
usage: tp_cost.py STEP1_DIR N SPEC [SPEC ...]"""
import json, statistics, sys, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, f"{sys.argv[1]}/ana")
import student_data as SD
from svsim.core.engine import apply, legal_actions
from svsim.tools.arena import make_agent
S, N, specs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = [r for r in SD._lines(f"{S}/starts.jsonl") if r["split"] == "train"][:N]
rows = {sp: [] for sp in specs}
for st in starts:
    for sp in specs:
        s = SD._state_at(games[st["game"]], st["at"]); me = s.active
        agent = make_agent(sp, 7)
        t = time.perf_counter(); k = srch = 0
        while not s.over and s.active == me:
            legal = legal_actions(s)
            srch += len(legal) > 1
            a = agent.act(s, legal); apply(s, a); k += 1
        ms = (time.perf_counter() - t) * 1000
        inner = agent.base
        r = {"k": st["k"], "spec": sp, "ms": round(ms), "decisions": k, "search_decisions": srch,
             "pick_ms": round(getattr(inner, "seconds", 0.0) * 1000),
             "chosen": (getattr(inner, "last_pick", None) or {}).get("chosen"),
             "plans": len((getattr(inner, "last_pick", None) or {}).get("plans", []))}
        rows[sp].append(r); print(json.dumps(r), flush=True)
for sp, rs in rows.items():
    ms = [r["ms"] for r in rs]; sd = sum(r["search_decisions"] for r in rs)
    print(json.dumps({"spec": sp, "turns": len(rs), "ms_per_turn_mean": round(statistics.mean(ms)),
                      "ms_per_turn_median": round(statistics.median(ms)),
                      "ms_per_search_decision": round(sum(ms) / max(sd, 1)),
                      "search_decisions_per_turn": round(sd / len(rs), 2),
                      "pick_ms_per_turn": round(statistics.mean(r["pick_ms"] for r in rs)),
                      "switched": sum(1 for r in rs if r["chosen"] not in (None, "bot")),
                      "chosen": {c: sum(1 for r in rs if r["chosen"] == c) for c in {r["chosen"] for r in rs}}}), flush=True)
