"""Measurement only (no behaviour change): within one own turn, level-strong's search starts every decision from a
fresh tree (ISMCTS.reuse is off in v2s). Playing whole turns from step 1's turn starts (RC 6f11111, the first 120,
the 116 with more than one legal action), for each searched decision k: the visits its chosen child already held,
as a share of the 200 iterations, which is what keeping the tree (+reuse) would hand to decision k + 1; split by
whether the move revealed nothing (no random numbers, no card from a deck: the case ISMCTS._expect keeps the subtree
for) and whether the turn went on to another searched decision.
usage: reuse_share.py STEP1_DIR"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
S = sys.argv[1]
sys.path.insert(0, f"{S}/ana")
import student_data as SD
from svsim.core.engine import apply, legal_actions
from svsim.search.lethal import hidden_info
from svsim.search.mcts import _locator, action_key
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = list(SD._lines(f"{S}/starts.jsonl"))[:120]
rows, turns = [], 0
for i, r in enumerate(starts):
    s = SD._state_at(games[r["game"]], r["at"])
    if len(legal_actions(s)) < 2:
        continue
    turns += 1
    agent = make_agent("mcts:200+plan+learned+phased", i)
    search = _search(agent)
    me, k, steps = s.active, 0, []
    while not s.over and s.active == me:
        legal = legal_actions(s)
        search.last_root = None
        a = agent.act(s, legal)
        root = search.last_root
        if root is not None:
            key = action_key(s, a, _locator(s, me))
            child = root.children.get(key)
            before = hidden_info(s)
            t = s.clone()
            apply(t, a)
            quiet = hidden_info(t) == before and not t.over and t.active == me
            steps.append({"k": k, "visits": child.visits if child else 0, "quiet": quiet,
                          "end_turn": type(a).__name__ == "EndTurn"})
        k += 1
        apply(s, a)
    for j, st in enumerate(steps):
        st["next_searched"] = j + 1 < len(steps)
        rows.append(st)

def summary(xs):
    v = [x["visits"] / 200 for x in xs]
    if not v:
        return {"n": 0}
    q = statistics.quantiles(v, n=4) if len(v) > 1 else [v[0]] * 3
    return {"n": len(v), "mean": round(statistics.mean(v), 3), "q1": round(q[0], 3), "median": round(q[1], 3),
            "q3": round(q[2], 3)}

useful = [x for x in rows if x["next_searched"] and not x["end_turn"]]
out = {"turns": turns, "searched_decisions": len(rows),
       "searched_per_turn": round(len(rows) / turns, 2),
       "all_searched_steps": summary(rows),
       "followed_by_a_search_this_turn": summary(useful),
       "followed_and_reveals_nothing (reusable)": summary([x for x in useful if x["quiet"]]),
       "followed_but_reveals (a draw or random: not reusable)": summary([x for x in useful if not x["quiet"]]),
       "by_step_k (followed, reusable)": {k: summary([x for x in useful if x["quiet"] and x["k"] == k])
                                           for k in sorted({x["k"] for x in useful})[:8]}}
print(json.dumps(out, indent=1))
