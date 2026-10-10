"""Step 1 on the teacher pairs, fit only. Stage 1: grid over mu x L2 x start on a quarter of the training games
(g % 11 != 0 and g % 4 == 0), read on all held-out games (g % 11 == 0). Stage 2: the chosen setting on all
training games (3000 and 6000 iterations: convergence), against the installed model. Stage 3: game bootstrap (30,
warm-started from stage 2, 400 iterations). Every stage prints as it ends."""
import itertools, json, os, random, sys
from collections import Counter
from multiprocessing import Pool
import numpy as np
D = sys.argv[1]
sys.path.insert(0, "/home/user/test1")
P = C = None

def calib_job(line):
    from svsim.learn.contrast import features_of
    from svsim.learn.netdata import ENDED, rows
    rec = json.loads(line)
    return [(rec["g"], features_of(st, me), res) for ph, me, st, res in rows(rec) if ph == ENDED and res != 0.5]

def load():
    global P, C
    z = np.load(f"{D}/c1_pairs.npz"); P = {k: z[k] for k in z.files}
    c = np.load(f"{D}/c1_calib.npz"); C = {"g": c["g"], "X": c["X"].astype(np.float32), "y": c["y"]}

def setup():
    from pathlib import Path
    from svsim.learn.contrast import feature_names
    from svsim.learn.features import signs
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import STOCK
    names = feature_names(2, ())
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    inst = LinearValue.load(Path("/home/user/test1/svsim/learn/phased_models/ramp-ramp-ended.json"))
    return names, keep, list(signs(False, 2)), names.index("bias"), inst

def fit(ip, ic, mu, l2, start, iters, init=None):
    from svsim.learn.contrast import fit_contrast
    names, keep, sg, bias, inst = setup()
    if init is None and start == "installed":
        init = (inst.coef, inst.mean, inst.std)
    return fit_contrast(P["XA"][ip], P["XB"][ip], P["dT"][ip], None, C["X"][ic], C["y"][ic], mu=mu, l2=l2,
                        iters=iters, signs=sg, bias=bias, keep=keep, init=init)

def read(E, ip, ic):
    s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
    d = s(E(P["XA"][ip])) - s(E(P["XB"][ip])); t = P["dT"][ip]; nz = t != 0
    zc = E(C["X"][ic]); yc = C["y"][ic]
    return {"mse": round(float(np.mean((d - t) ** 2)), 6), "sign": round(float(np.mean(np.sign(d[nz]) == np.sign(t[nz]))), 4),
            "calib": round(float(np.mean(np.logaddexp(0, zc) - yc * zc)), 4)}

def model_E(m, keep):
    return lambda X: m.forward(m.standardize(np.asarray(X, float) * keep).astype(np.float32))

def grid_job(cfg):
    mu, l2, start = cfg
    names, keep, sg, bias, inst = setup()
    tr = np.where((P["g"] % 11 != 0) & (P["g"] % 4 == 0))[0]
    ctr = np.where((C["g"] % 11 != 0) & (C["g"] % 4 == 0))[0]
    va, cva = np.where(P["g"] % 11 == 0)[0], np.where(C["g"] % 11 == 0)[0]
    m, rep = fit(tr, ctr, mu, l2, start, 2000)
    return dict(mu=mu, l2=l2, start=start, intercept=round(float(m.w[bias]), 4), **read(model_E(m, keep), va, cva))

def boot_job(args):
    seed, w0, mean0, std0, mu, l2 = args
    rng = random.Random(seed)
    games = sorted(set(P["g"][P["g"] % 11 != 0].tolist()))
    cnt = Counter(games[rng.randrange(len(games))] for _ in games)
    byp, byc = {}, {}
    for i, g in enumerate(P["g"]): byp.setdefault(int(g), []).append(i)
    for i, g in enumerate(C["g"]): byc.setdefault(int(g), []).append(i)
    ip = np.concatenate([np.repeat(byp[g], k) for g, k in cnt.items() if g in byp])
    ic = np.concatenate([np.repeat(byc[g], k) for g, k in cnt.items() if g in byc])
    m, _ = fit(ip, ic, mu, l2, "zero", 400, init=(w0, mean0, std0))
    return (m.w / m.std).tolist()

if __name__ == "__main__":
    if not os.path.exists(f"{D}/c1_calib.npz"):
        lines = [l for l in open(f"{D}/selfplay.jsonl") if l.strip()]
        with Pool(4) as p:
            cal = [r for part in p.map(calib_job, lines, chunksize=8) for r in part]
        np.savez_compressed(f"{D}/c1_calib.npz", g=np.array([c[0] for c in cal]), X=np.array([c[1] for c in cal]),
                            y=np.array([c[2] for c in cal], float))
    load()
    names, keep, sg, bias, inst = setup()
    va, cva = np.where(P["g"] % 11 == 0)[0], np.where(C["g"] % 11 == 0)[0]
    E_inst = lambda X: ((np.asarray(X, float) - np.array(inst.mean)) / np.array(inst.std)) @ np.array(inst.coef)
    base = read(E_inst, va, cva)
    print(json.dumps({"stage": "installed", "val": base, "pairs": int(len(P["dT"])), "val_pairs": int(len(va)),
                      "calib_rows": int(len(C["y"]))}), flush=True)
    grid = list(itertools.product((0.03, 0.1, 0.3, 1.0), (1e-4, 1e-3, 1e-2), ("zero", "installed")))
    with Pool(4) as p:
        res = []
        for r in p.imap_unordered(grid_job, grid):
            res.append(r); print(json.dumps(dict(stage="grid", **r)), flush=True)
    ok = [r for r in res if r["calib"] <= base["calib"] + 0.005]          # calibration no worse than installed + 0.005
    best = min(ok or res, key=lambda r: r["mse"])
    print(json.dumps({"stage": "chosen", **best, "rule": "least held-out contrast MSE among settings whose held-out "
                      "calibration log loss is within +0.005 of the installed model's"}), flush=True)
    tr, ctr = np.where(P["g"] % 11 != 0)[0], np.where(C["g"] % 11 != 0)[0]
    with Pool(2) as p:
        (m3, r3), (m6, r6) = p.starmap(fit, [(tr, ctr, best["mu"], best["l2"], best["start"], 3000),
                                               (tr, ctr, best["mu"], best["l2"], best["start"], 6000)])
    E3, E6 = model_E(m3, keep), model_E(m6, keep)
    print(json.dumps({"stage": "final", "val_3000": read(E3, va, cva), "val_6000": read(E6, va, cva),
                      "train_3000": read(E3, tr, ctr), "train_installed": read(E_inst, tr, ctr),
                      "max_coef_diff_3000_6000": round(float(np.max(np.abs(m3.w - m6.w))), 4),
                      "intercept": round(float(m3.w[bias]), 4), "intercept_installed": round(float(inst.coef[bias]), 4)}), flush=True)
    kinds = {}
    for k in sorted(set(P["kind"].tolist())):
        m_ = va[P["kind"][va] == k]
        kinds[k] = {"n": int(len(m_)), "contrast": read(E3, m_, cva)["sign"], "installed": read(E_inst, m_, cva)["sign"]}
    print(json.dumps({"stage": "by_kind", **kinds}), flush=True)
    inst_conv = np.array(inst.coef) / np.array(inst.std) * m3.std
    flips = [{"feature": names[i], "contrast": round(float(m3.w[i]), 4), "installed": round(float(inst_conv[i]), 4)}
             for i in range(len(names)) if i != bias and keep[i] and m3.w[i] * inst_conv[i] < 0
             and max(abs(m3.w[i]), abs(inst_conv[i])) >= 0.015]
    print(json.dumps({"stage": "flips", "flips": flips}), flush=True)
    from svsim.learn.contrast import to_linear_value
    from pathlib import Path
    to_linear_value(m3, 2, (), {"contrast": True, "mode": "det", "mu": best["mu"], "l2": best["l2"], "start": best["start"],
                                "iters": 3000, "report": r3}).save(Path(f"{D}/c1_ramp-ramp-ended.json"))
    os.environ["OMP_NUM_THREADS"] = "1"
    with Pool(4) as p:
        boots = np.array(p.map(boot_job, [(s, m3.w, m3.mean, m3.std, best["mu"], best["l2"]) for s in range(30)]))
    unit = m3.w / m3.std
    order = sorted([i for i in range(len(names)) if keep[i] and i != bias], key=lambda i: -abs(m3.w[i]))
    rows = []
    for i in order[:12] + [names.index(f["feature"]) for f in flips if names.index(f["feature"]) not in order[:12]]:
        b = boots[:, i]
        rows.append({"feature": names[i], "std_coef": round(float(m3.w[i]), 4), "per_unit": round(float(unit[i]), 4),
                     "lo": round(float(np.percentile(b, 2.5)), 4), "hi": round(float(np.percentile(b, 97.5)), 4),
                     "same_sign": round(float(np.mean(np.sign(b) == np.sign(unit[i]))), 3)})
    print(json.dumps({"stage": "bootstrap", "n": 30, "coefs": rows}), flush=True)
