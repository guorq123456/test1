import json, math, sys
from multiprocessing import Pool
sys.path.insert(0, "/home/user/test1"); D = sys.argv[1]; sys.path.insert(0, f"{D}/ana")
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
    s = SD._state_at(G["games"][r["game"]], r["at"]); legal = legal_actions(s)
    if len(legal) < 2: return None
    me, where = s.active, _locator(s, s.active); out = {}
    for name, spec, center, norm in (("inst", "level-strong", True, False), ("abs_only", "level-strong", False, False),
                                     ("norm_only", "level-strong", True, True)):
        a = make_agent(spec, 7000 + i); srch = _search(a); srch.centered, srch.normalize = center, norm
        out[name] = repr(action_key(s, a.act(s.clone(), legal), where))
    w = _search(make_agent("level-strong", 0)).weights
    out["p"] = 1 / (1 + math.exp(-max(-60, min(60, evaluate(s, me, w, True) / 8))))
    return out
if __name__ == "__main__":
    import student_data as SD
    starts = list(SD._lines(f"{D}/starts.jsonl"))[:600]
    with Pool(4, initializer=init) as pool:
        rows = [r for r in pool.map(job, list(enumerate(starts)), chunksize=4) if r]
    for name, lo, hi in (("< 0.15", 0, 0.15), ("mid", 0.15, 0.85), ("> 0.85", 0.85, 1.01), ("all", 0, 1.01)):
        sel = [r for r in rows if lo <= r["p"] < hi]
        print(name, len(sel), "center off only:", round(sum(r["inst"] != r["abs_only"] for r in sel) / len(sel), 3),
              "normalize only:", round(sum(r["inst"] != r["norm_only"] for r in sel) / len(sel), 3))
