"""Features of every teacher pair's two turn ends (end_of_turn=True), by (position, seed) group in parallel."""
import json, sys, time
from multiprocessing import Pool
import numpy as np
D = sys.argv[1]
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, f"{D}/ana")
STARTS = None

def init():
    global STARTS
    import teacher_ends as TE
    STARTS = TE.Starts(f"{D}/selfplay.jsonl")

def end(row):
    """The turn end with end-of-turn abilities resolved, or None if the game ended during the turn."""
    import teacher_ends as TE
    from svsim.search.evaluate import after_end_of_turn
    st = TE.turn_end(row, STARTS, False)
    if st.over:
        return None
    st = after_end_of_turn(st)
    return None if st.over else st

def job(item):
    from svsim.learn.contrast import features_of
    (n, s), d = item
    out, cache, over = [], {}, 0
    line = d["line"]
    for r, rs in sorted(d.items()):
        if r == "line":
            continue
        for x, b in zip(rs, line):
            if x["actions"] == b["actions"]:
                continue
            j = x["j"]
            if j not in cache:
                eb = end(b)
                cache[j] = None if eb is None else features_of(eb, b["seat"])
            ea = end(x)
            if ea is None or cache[j] is None:
                over += 1
                continue
            out.append((n, x["g"], s, j, r, features_of(ea, x["seat"]), cache[j], x["value"] - b["value"]))
    return out, over

if __name__ == "__main__":
    import teacher_ends as TE
    t = time.time()
    with Pool(4, initializer=init) as p:
        res, over = [], 0
        for part, o in p.imap(job, TE.groups(f"{D}/teacher_ends.jsonl.gz"), chunksize=8):
            res += part
            over += o
    rs = sorted({r[4] for r in res})
    np.savez_compressed(f"{D}/c1_pairs.npz", n=np.array([r[0] for r in res]), g=np.array([r[1] for r in res]),
                        s=np.array([r[2] for r in res]), j=np.array([r[3] for r in res]),
                        kind=np.array([r[4].split(":")[0] for r in res]),
                        XA=np.array([r[5] for r in res], dtype=np.float32), XB=np.array([r[6] for r in res], dtype=np.float32),
                        dT=np.array([r[7] for r in res]))
    print(len(res), "pairs,", over, "left out (the game ended during a turn),", round(time.time() - t), "s", flush=True)
