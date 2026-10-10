"""The lethal-clock candidate's examples (the architecture thread 2026-10-10 10:38Z): step 1's examples exactly as
analysis/step1-candidate/s1_extract.py builds them (same pairs, same order, same calibration rows), each turn end
read as version-2 features plus the "kclock" set (learn.features). kc_fit.py checks that the version-2 columns equal
s1_data.npz's. Condition: the opponent's deck list is known (order and hand not).
usage: kc_extract.py STEP1_DIR OLD_DIR OUT.npz"""
import gzip, json, sys, time
from collections import defaultdict
from multiprocessing import Pool
import numpy as np
S1, OLD, OUT = sys.argv[1:4]
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2])); sys.path.insert(0, f"{S1}/ana")
EXTRAS = ("kclock",)
ST = {}

def init():
    import teacher_ends as TE
    ST["step1"] = TE.Starts(f"{S1}/selfplay.jsonl")
    ST["old"] = TE.Starts(f"{OLD}/selfplay.jsonl")

def job(item):
    """(source, n, rows) -> {(plan, det): (features or None if the game is over, actions)}"""
    import teacher_ends as TE
    from svsim.learn.contrast import features_of
    src, n, rows = item
    out = {}
    for tag, r in rows:
        st = TE.turn_end(r, ST[src], end_of_turn=True)
        det = (tag, r["s"], r["j"])
        out[(r["r"], det)] = (None if st.over else np.asarray(features_of(st, r["seat"], 2, EXTRAS), np.float32),
                              json.dumps(r["actions"], sort_keys=True))
    return src, n, out

def items():
    by = defaultdict(list)
    for tag, path in (("T", f"{S1}/teacher_ends.jsonl.gz"), ("G", f"{S1}/gend_ends.jsonl.gz")):
        with gzip.open(path, "rt") as fh:
            for l in fh:
                r = json.loads(l); by[r["n"]].append((tag, r))
    for n in sorted(by):
        yield "step1", n, by[n]
    del by
    cur, rows = None, []
    with gzip.open(f"{OLD}/teacher_ends.jsonl.gz", "rt") as fh:
        for l in fh:
            r = json.loads(l)
            if r["n"] != cur and rows:
                yield "old", cur, rows; rows = []
            cur = r["n"]; rows.append(("T", r))
    if rows:
        yield "old", cur, rows

def calib(arg):
    src, line = arg
    from svsim.learn.contrast import features_of
    from svsim.learn.netdata import ENDED, rows
    rec = json.loads(line)
    return [(src, rec["g"], np.asarray(features_of(st, me, 2, EXTRAS), np.float32), res)
            for ph, me, st, res in rows(rec) if ph == ENDED and res != 0.5]

if __name__ == "__main__":
    t = time.time()
    X, ia, ib, key, det = [], [], [], [], []
    keys, kidx = [], {}
    count = defaultdict(int)
    with Pool(4, initializer=init) as p:
        for src, n, out in p.imap(job, items(), chunksize=4):
            line = "bot" if src == "step1" else "line"
            plans = sorted({pl for pl, _ in out if pl != line})
            base = {}
            for pl in plans:
                for (q, d), (fx, acts) in out.items():
                    if q != pl:
                        continue
                    if (line, d) not in out:
                        count[f"{src}_no_line_end"] += 1; continue
                    fb, ab = out[(line, d)]
                    if acts == ab:
                        count[f"{src}_same_actions"] += 1; continue
                    if fx is None or fb is None:
                        count[f"{src}_over"] += 1; continue
                    if d not in base:
                        base[d] = len(X); X.append(fb)
                    X.append(fx)
                    kk = (src, n, pl)
                    if kk not in kidx:
                        kidx[kk] = len(keys); keys.append(kk)
                    ia.append(len(X) - 1); ib.append(base[d]); key.append(kidx[kk]); det.append(d[0])
                    count[f"{src}_pairs"] += 1
    lines = [("step1", l) for l in open(f"{S1}/selfplay.jsonl") if l.strip()] + \
            [("old", l) for l in open(f"{OLD}/selfplay.jsonl") if l.strip()]
    with Pool(4) as p:
        cal = [r for part in p.map(calib, lines, chunksize=8) for r in part]
    np.savez(OUT, X=np.stack(X), ia=np.array(ia), ib=np.array(ib), key=np.array(key), det=np.array(det),
             keys=np.array([json.dumps(k) for k in keys]),
             Csrc=np.array([c[0] for c in cal]), Cg=np.array([c[1] for c in cal]),
             Cx=np.stack([c[2] for c in cal]), Cy=np.array([c[3] for c in cal], float))
    print(json.dumps({"counts": dict(count), "ends": len(X), "keys": len(keys), "calibration_rows": len(cal),
                      "seconds": round(time.time() - t)}), flush=True)
