"""+abs's pre-gate reading (the architecture thread 2026-10-10 09:01Z): how often its root choice differs from the
installed search's, by the position's absolute win probability. At each of the first N step-1 turn starts (6f11111;
the turn's first decision), level-strong and level-strong+abs choose with the same seed; the start's absolute win
probability is the installed evaluation's sigma(score / 8) with the player to move (the ACT model). Buckets:
< 0.15, 0.15-0.85, > 0.85. Condition: the opponent's deck list is known (order and hand not).
usage: abs_read.py STEP1_DIR [N] [WORKERS]"""
import json, math, sys
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
D = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 600
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
sys.path.insert(0, f"{D}/ana")
G = {}


def init():
    import student_data as SD
    G["games"] = {r["g"]: r for r in SD._lines(f"{D}/selfplay.jsonl")}


def job(item):
    import student_data as SD
    from svsim.core.engine import legal_actions
    from svsim.search.evaluate import evaluate
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    i, r = item
    s = SD._state_at(G["games"][r["game"]], r["at"])
    legal = legal_actions(s)
    if len(legal) < 2:
        return None
    me, where = s.active, _locator(s, s.active)
    out = {"i": i}
    for name, spec in (("installed", "level-strong"), ("abs", "level-strong+abs")):
        agent = make_agent(spec, 7000 + i)
        out[name] = repr(action_key(s, agent.act(s.clone(), legal), where))
    w = _search(make_agent("level-strong", 0)).weights
    out["p"] = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, evaluate(s, me, w, True) / 8.0))))
    return out


if __name__ == "__main__":
    import student_data as SD
    starts = list(SD._lines(f"{D}/starts.jsonl"))[:N]
    with Pool(WORKERS, initializer=init) as pool:
        rows = [r for r in pool.map(job, list(enumerate(starts)), chunksize=4) if r]
    out = {}
    for name, lo, hi in (("< 0.15", 0, 0.15), ("0.15-0.85", 0.15, 0.85), ("> 0.85", 0.85, 1.01)):
        sel = [r for r in rows if lo <= r["p"] < hi]
        diff = sum(r["installed"] != r["abs"] for r in sel)
        out[name] = {"decisions": len(sel), "different": diff, "share": round(diff / len(sel), 4) if sel else None}
    out["all"] = {"decisions": len(rows), "different": sum(r["installed"] != r["abs"] for r in rows),
                  "share": round(sum(r["installed"] != r["abs"] for r in rows) / len(rows), 4)}
    print(json.dumps(out, indent=1))
