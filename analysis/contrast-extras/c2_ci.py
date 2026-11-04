"""The comparison read with its noise: linear (the chosen version, clock columns held out), linear+clock and the
network (6 epochs, fixed in advance; seeds 0, 1, 2) on the held-out teacher pairs (game % 11 == 0), each against the
linear version with a 95% interval from resampling held-out games (2000 draws); then the cost per evaluation,
measured interleaved after a warm-up (5 rounds, median)."""
import json, random, sys, time
import numpy as np
D = sys.argv[1]
sys.path.insert(0, "/home/user/test1")
from svsim.learn.contrast import feature_names, fit_contrast
from svsim.learn.contrast_net import ContrastNet
from svsim.learn.features import signs
from svsim.learn.phased import STOCK
MU, L2 = 0.03, 1e-4
z = np.load(f"{D}/c2_data.npz")
E = {k[2:]: z[k] for k in z.files if k.startswith("E_")}
C = {k[2:]: z[k] for k in z.files if k.startswith("C_")}
ia, ib, dT, g, kind, Cg, Cy = z["ia"], z["ib"], z["dT"], z["g"], z["kind"], z["Cg"], z["Cy"]
names = feature_names(2, ("clock",)); bias = names.index("bias")
stock = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
noclock = stock.copy(); noclock[-5:] = 0.0
sg = list(signs(False, 2)) + [0] * 5
tr, va = np.where(g % 11 != 0)[0], np.where(g % 11 == 0)[0]
ctr, cva = np.where(Cg % 11 != 0)[0], np.where(Cg % 11 == 0)[0]
s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
X = E["x"].astype(np.float32)
preds = {}
def linear(keep, tag):
    lin, _ = fit_contrast(X[ia[tr]] * keep, X[ib[tr]] * keep, dT[tr], None, C["x"][ctr].astype(np.float32) * keep,
                          Cy[ctr], mu=MU, l2=L2, iters=3000, signs=sg, bias=bias, keep=keep)
    f = lambda Xs: lin.forward(lin.standardize(np.asarray(Xs, float) * keep).astype(np.float32))
    preds[tag] = (f(X[ia[va]]), f(X[ib[va]]), f(C["x"][cva]))
    return lin
linear(noclock, "linear")
lin = linear(stock, "linear+clock")
vocab = sorted({int(c) for c in np.unique(np.concatenate([E["fid"].ravel(), E["hid"].ravel(), C["fid"].ravel(), C["hid"].ravel()])) if c})
lut = {c: i + 1 for i, c in enumerate(vocab)}
def prep(D_, mean, std):
    out = dict(D_)
    for a, b in (("fid", "fi"), ("hid", "hi")):
        u, inv = np.unique(D_[a], return_inverse=True)
        out[b] = np.array([lut.get(int(c), 0) if c else 0 for c in u])[inv].reshape(D_[a].shape)
    out["xs"] = ((D_["x"].astype(float) * stock - mean) / std).astype(np.float32)
    return out
EP, CP = prep(E, lin.mean, lin.std), prep(C, lin.mean, lin.std)
take = lambda D_, idx: {k: v[idx] for k, v in D_.items()}
A_tr, B_tr, A_va, B_va = take(EP, ia[tr]), take(EP, ib[tr]), take(EP, ia[va]), take(EP, ib[va])
C_tr, C_va = take(CP, ctr), take(CP, cva)
nets = {}
for seed in (0, 1, 2):
    net = ContrastNet(vocab, lin.mean, lin.std, bias, seed=seed); net.w = lin.w.copy(); net.index = lut
    net.fit(A_tr, B_tr, dT[tr], None, C_tr, Cy[ctr], mu=MU, l2=L2, epochs=6, batch=2048, lr=3e-3, seed=seed,
            keep=stock, signs=sg)
    preds[f"network s{seed}"] = (net.forward(A_va), net.forward(B_va), net.forward(C_va)); nets[seed] = net
dv, gv, kv, gc, yc = dT[va], g[va], kind[va], Cg[cva], Cy[cva]
nz = dv != 0
def per_pair(tag):
    fa, fb, fc = preds[tag]; d = s(fa) - s(fb)
    return (d - dv) ** 2, (np.sign(d) == np.sign(dv)).astype(float), np.logaddexp(0, fc) - yc * fc
ids = sorted(set(gv.tolist())); byp = {k: np.where(gv == k)[0] for k in ids}; byc = {k: np.where(gc == k)[0] for k in ids}
rng = random.Random(1)
draws = [[k for k in (ids[rng.randrange(len(ids))] for _ in ids)] for _ in range(2000)]
base = per_pair("linear")
def summary(tag):
    m, sgn, c = per_pair(tag)
    out = {"model": tag, "mse": round(float(m.mean()), 6), "sign": round(float(sgn[nz].mean()), 4),
           "calib": round(float(c.mean()), 4),
           "by_kind": {k: round(float(sgn[nz & (kv == k)].mean()), 4) for k in ("keep", "noevo", "save")}}
    if tag != "linear":
        diffs = {"mse": [], "sign": [], "calib": []}
        for dr in draws:
            p = np.concatenate([byp[k] for k in dr]); q = np.concatenate([byc[k] for k in dr if k in byc])
            pn = p[nz[p]]
            diffs["mse"].append(float(m[p].mean() - base[0][p].mean()))
            diffs["sign"].append(float(sgn[pn].mean() - base[1][pn].mean()))
            diffs["calib"].append(float(c[q].mean() - base[2][q].mean()))
        out["vs_linear_95"] = {k: [round(sorted(v)[50], 6 if k == "mse" else 4), round(sorted(v)[1949], 6 if k == "mse" else 4)]
                               for k, v in diffs.items()}
    return out
for tag in preds:
    print(json.dumps(summary(tag)), flush=True)
fa = np.mean([preds[f"network s{k}"][0] for k in (0, 1, 2)], axis=0); fb = np.mean([preds[f"network s{k}"][1] for k in (0, 1, 2)], axis=0)
fc = np.mean([preds[f"network s{k}"][2] for k in (0, 1, 2)], axis=0)
preds["network mean of 3"] = (fa, fb, fc); print(json.dumps(summary("network mean of 3")), flush=True)
print(json.dumps({"held_out": {"pairs": int(len(va)), "nonzero": int(nz.sum()), "games": len(ids), "calibration_rows": int(len(cva))}}), flush=True)
# cost per evaluation: interleaved, after a warm-up, median of 5 rounds
sys.path.insert(0, "/home/user/test1/tests")
from test_handvalue import _positions
from svsim.learn.contrast import features_of
from svsim.search.evaluate import after_end_of_turn
pos, _ = _positions(n_games=3)
ends = [(after_end_of_turn(st), p) for st, p in pos if not after_end_of_turn(st).over]
lins = [features_of(e, p, 2, ("clock",)) for e, p in ends]
net = nets[0]
for (e, p), x in zip(ends, lins): features_of(e, p, 2, ()); net.logit(e, p, x)
rounds = {"linear_features": [], "with_clock": [], "network_on_top": []}
for _ in range(5):
    t = time.perf_counter()
    for e, p in ends: features_of(e, p, 2, ())
    rounds["linear_features"].append((time.perf_counter() - t) / len(ends))
    t = time.perf_counter()
    for e, p in ends: features_of(e, p, 2, ("clock",))
    rounds["with_clock"].append((time.perf_counter() - t) / len(ends))
    t = time.perf_counter()
    for (e, p), x in zip(ends, lins): net.logit(e, p, x)
    rounds["network_on_top"].append((time.perf_counter() - t) / len(ends))
print(json.dumps({"cost_us": {k: round(float(np.median(v)) * 1e6, 1) for k, v in rounds.items()}, "ends": len(ends)}), flush=True)
