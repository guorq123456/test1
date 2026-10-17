"""cand-kc-ramp-t's examples (the architecture thread 2026-10-13 23:58Z): the ramp-t mirror's step-1 data (step1.py on
bank 69900000, this folder's README) read as cand-kc's examples were (analysis/lethal-clock/kc_extract.py, itself
analysis/step1-candidate/s1_extract.py), with two differences:
- only the step-1 source (the card-value teacher re-run exists for the original Ramp mirror only);
- the features are the installed ramp-t mirror model's (version 2 + "hand" + "hpphase") plus "kclock".
Every determinization's pair of turn ends (a plan's, the bot's) for T and G_end, each end rebuilt with
teacher_ends.turn_end(end_of_turn=True) and read for its mover. Determinizations where both lines' actions are the
same are not kept; one where either end is a finished game is left out and counted. Calibration rows: the ENDED turn
ends (decided games) of the self-play set. Condition: the opponent's deck list is known (order and hand not).
usage: krt_extract.py DATA_DIR LIB_DIR OUT.npz     (LIB_DIR: the analysis line's card-value / turn-level scripts)"""
import gzip, json, os, sys, time
from collections import defaultdict
from multiprocessing import Pool
import numpy as np
D, LIB, OUT = sys.argv[1:4]
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
sys.path.insert(0, os.path.join(LIB, "card-value"))
EXTRAS = ("hand", "hpphase", "kclock")
ST = {}


def init():
    import teacher_ends as TE
    ST["step1"] = TE.Starts(f"{D}/selfplay.jsonl")


def job(item):
    """(n, rows) -> {(plan, det): (features or None if the game is over, actions)}"""
    import teacher_ends as TE
    from svsim.learn.contrast import features_of
    n, rows = item
    out = {}
    for tag, r in rows:
        st = TE.turn_end(r, ST["step1"], end_of_turn=True)
        det = (tag, r["s"], r["j"])
        out[(r["r"], det)] = (None if st.over else np.asarray(features_of(st, r["seat"], 2, EXTRAS), np.float32),
                              json.dumps(r["actions"], sort_keys=True))
    return n, out


def items():
    by = defaultdict(list)
    for tag, path in (("T", f"{D}/teacher_ends.jsonl.gz"), ("G", f"{D}/gend_ends.jsonl.gz")):
        with gzip.open(path, "rt") as fh:
            for l in fh:
                r = json.loads(l)
                by[r["n"]].append((tag, r))
    for n in sorted(by):
        yield n, by[n]


def calib(line):
    from svsim.learn.contrast import features_of
    from svsim.learn.netdata import ENDED, rows
    rec = json.loads(line)
    return [(rec["g"], np.asarray(features_of(st, me, 2, EXTRAS), np.float32), res)
            for ph, me, st, res in rows(rec) if ph == ENDED and res != 0.5]


if __name__ == "__main__":
    t = time.time()
    workers = int(os.environ.get("WORKERS", "3"))
    X, ia, ib, key, det = [], [], [], [], []
    keys, kidx = [], {}
    count = defaultdict(int)
    with Pool(workers, initializer=init) as p:
        for n, out in p.imap(job, items(), chunksize=4):
            plans = sorted({pl for pl, _ in out if pl != "bot"})
            base = {}
            for pl in plans:
                for (q, d), (fx, acts) in out.items():
                    if q != pl:
                        continue
                    if ("bot", d) not in out:
                        count["no_line_end"] += 1; continue
                    fb, ab = out[("bot", d)]
                    if acts == ab:
                        count["same_actions"] += 1; continue
                    if fx is None or fb is None:
                        count["over"] += 1; continue
                    if d not in base:
                        base[d] = len(X); X.append(fb)
                    X.append(fx)
                    kk = ("step1", n, pl)
                    if kk not in kidx:
                        kidx[kk] = len(keys); keys.append(kk)
                    ia.append(len(X) - 1); ib.append(base[d]); key.append(kidx[kk]); det.append(d[0])
                    count["pairs"] += 1
    lines = [l for l in open(f"{D}/selfplay.jsonl") if l.strip()]
    with Pool(workers) as p:
        cal = [r for part in p.map(calib, lines, chunksize=8) for r in part]
    np.savez(OUT, X=np.stack(X), ia=np.array(ia), ib=np.array(ib), key=np.array(key), det=np.array(det),
             keys=np.array([json.dumps(k) for k in keys]),
             Cg=np.array([c[0] for c in cal]), Cx=np.stack([c[1] for c in cal]), Cy=np.array([c[2] for c in cal], float))
    print(json.dumps({"counts": dict(count), "ends": len(X), "keys": len(keys), "calibration_rows": len(cal),
                      "seconds": round(time.time() - t)}), flush=True)
