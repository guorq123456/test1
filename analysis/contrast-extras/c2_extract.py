"""Every teacher pair's turn ends (end-of-turn resolved; pairs with a game over left out) as linear features
(version 2 + clock) and the network's set inputs; the line's end shared within (position, seed, determinization).
Calibration: the self-play turn ends. Saved as c2_data.npz."""
import json, sys, time
from multiprocessing import Pool
import numpy as np
D = sys.argv[1]
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, f"{D}/ana")
STARTS = None
KEYS = ("x", "fid", "fnum", "hid", "hst", "hfit", "ctx")

def init():
    global STARTS
    import teacher_ends as TE
    STARTS = TE.Starts(f"{D}/selfplay.jsonl")

def enc(state, me):
    from svsim.learn.contrast import features_of
    from svsim.learn.contrast_net import encode
    return encode(state, me, features_of(state, me, 2, ("clock",)))

def end(row):
    import teacher_ends as TE
    from svsim.search.evaluate import after_end_of_turn
    st = TE.turn_end(row, STARTS, False)
    if st.over:
        return None
    st = after_end_of_turn(st)
    return None if st.over else st

def job(item):
    (n, s), d = item
    ends, pairs, line_idx, over = [], [], {}, 0
    for r, rs in sorted(d.items()):
        if r == "line":
            continue
        for x, b in zip(rs, d["line"]):
            if x["actions"] == b["actions"]:
                continue
            j = x["j"]
            if j not in line_idx:
                eb = end(b)
                line_idx[j] = None if eb is None else len(ends)
                if eb is not None:
                    ends.append(enc(eb, b["seat"]))
            ea = end(x)
            if ea is None or line_idx[j] is None:
                over += 1
                continue
            ends.append(enc(ea, x["seat"]))
            pairs.append((len(ends) - 1, line_idx[j], x["value"] - b["value"], x["g"], r.split(":")[0]))
    return ends, pairs, over

def calib_job(line):
    from svsim.learn.netdata import ENDED, rows
    rec = json.loads(line)
    return [(rec["g"], enc(st, me), res) for ph, me, st, res in rows(rec) if ph == ENDED and res != 0.5]

if __name__ == "__main__":
    import teacher_ends as TE
    t = time.time()
    E = {k: [] for k in KEYS}; ia, ib, dT, g, kind = [], [], [], [], []; over = 0; base = 0
    with Pool(4, initializer=init) as p:
        for ends, pairs, o in p.imap(job, TE.groups(f"{D}/teacher_ends.jsonl.gz"), chunksize=8):
            for e in ends:
                for k in KEYS: E[k].append(e[k])
            for a, b, d_, g_, k_ in pairs:
                ia.append(base + a); ib.append(base + b); dT.append(d_); g.append(g_); kind.append(k_)
            base += len(ends); over += o
    lines = [l for l in open(f"{D}/selfplay.jsonl") if l.strip()]
    with Pool(4) as p:
        cal = [r for part in p.map(calib_job, lines, chunksize=8) for r in part]
    out = {f"E_{k}": np.stack(E[k]) for k in KEYS}
    out.update({f"C_{k}": np.stack([c[1][k] for c in cal]) for k in KEYS})
    out.update(ia=np.array(ia), ib=np.array(ib), dT=np.array(dT), g=np.array(g), kind=np.array(kind),
               Cg=np.array([c[0] for c in cal]), Cy=np.array([c[2] for c in cal], float))
    np.savez(f"{D}/c2_data.npz", **out)
    print(f"{len(dT)} pairs over {base} turn ends, {over} left out (game over), {len(cal)} calibration rows, "
          f"{round(time.time() - t)} s", flush=True)
