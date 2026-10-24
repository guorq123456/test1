import json, sys, time
import numpy as np
D = sys.argv[1]
sys.path.insert(0, "/home/user/test1")
from svsim.learn.contrast import feature_names, fit_contrast
from svsim.learn.contrast_net import ContrastNet
from svsim.learn.features import signs
from svsim.learn.phased import STOCK
from svsim.learn.fit import standardize
MU, L2 = 0.03, 1e-4
z = np.load(f"{D}/c2_data.npz")
E = {k[2:]: z[k] for k in z.files if k.startswith("E_")}
C = {k[2:]: z[k] for k in z.files if k.startswith("C_")}
ia, ib, dT, g, kind, Cg, Cy = z["ia"], z["ib"], z["dT"], z["g"], z["kind"], z["Cg"], z["Cy"]
names = feature_names(2, ("clock",)); bias = names.index("bias")
keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
sg = list(signs(False, 2)) + [0] * 5
tr, va = np.where(g % 11 != 0)[0], np.where(g % 11 == 0)[0]
ctr, cva = np.where(Cg % 11 != 0)[0], np.where(Cg % 11 == 0)[0]
s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
def read(fa, fb, fc, idx, cidx):
    d = s(fa) - s(fb); t = dT[idx]; nz = t != 0
    zc = fc
    return {"mse": round(float(np.mean((d - t) ** 2)), 6), "sign": round(float(np.mean(np.sign(d[nz]) == np.sign(t[nz]))), 4),
            "calib": round(float(np.mean(np.logaddexp(0, zc) - Cy[cidx] * zc)), 4)}
def by_kind(fa, fb):
    out = {}
    for k in ("keep", "noevo", "save"):
        m = kind[va] == k; d = s(fa[m]) - s(fb[m]); t = dT[va][m]; nz = t != 0
        out[k] = round(float(np.mean(np.sign(d[nz]) == np.sign(t[nz]))), 4)
    return out
# 1. linear + clock (the chosen settings)
X = E["x"].astype(np.float32)
t0 = time.time()
lin, rep = fit_contrast(X[ia[tr]], X[ib[tr]], dT[tr], None, C["x"][ctr].astype(np.float32), Cy[ctr], mu=MU, l2=L2,
                        iters=3000, signs=sg, bias=bias, keep=keep)
EL = lambda Xs: lin.forward(lin.standardize(np.asarray(Xs, float) * keep).astype(np.float32))
r_lin = read(EL(X[ia[va]]), EL(X[ib[va]]), EL(C["x"][cva]), va, cva)
print(json.dumps({"model": "linear+clock", **r_lin, "by_kind": by_kind(EL(X[ia[va]]), EL(X[ib[va]])),
                  "clock_coefs": {n: round(float(lin.w[names.index(n)]), 4) for n in names[-5:]},
                  "intercept": round(float(lin.w[bias]), 4), "seconds": round(time.time() - t0)}), flush=True)
# 2. the network on top (linear part from the linear+clock fit, network part from zero)
vocab = sorted({int(c) for c in np.unique(np.concatenate([E["fid"].ravel(), E["hid"].ravel(), C["fid"].ravel(), C["hid"].ravel()])) if c})
net = ContrastNet(vocab, lin.mean, lin.std, bias, embed=8, field=16, hand=16, hidden=32, seed=0)
net.w = lin.w.copy()
lut = {c: i + 1 for i, c in enumerate(vocab)}
def prep(D_):
    out = dict(D_)
    for a, b in (("fid", "fi"), ("hid", "hi")):
        u, inv = np.unique(D_[a], return_inverse=True)
        out[b] = np.array([lut.get(int(c), 0) if c else 0 for c in u])[inv].reshape(D_[a].shape)
    out["xs"] = ((D_["x"].astype(float) * keep - net.mean) / net.std).astype(np.float32)
    return out
EP, CP = prep(E), prep(C)
take = lambda D_, idx: {k: v[idx] for k, v in D_.items()}
A_tr, B_tr = take(EP, ia[tr]), take(EP, ib[tr]); A_va, B_va = take(EP, ia[va]), take(EP, ib[va])
C_tr, C_va = take(CP, ctr), take(CP, cva)
def report(m):
    fa, fb, fc = m.forward(A_va), m.forward(B_va), m.forward(C_va)
    print(json.dumps({"model": "network", "epoch": report.k, **read(fa, fb, fc, va, cva), "by_kind": by_kind(fa, fb)}), flush=True)
    report.k += 1
report.k = 1
t0 = time.time()
net.fit(A_tr, B_tr, dT[tr], None, C_tr, Cy[ctr], mu=MU, l2=L2, epochs=6, batch=2048, lr=3e-3, seed=0, keep=keep,
        signs=sg, report=report)
print(json.dumps({"model": "network", "parameters": net.parameters(), "seconds": round(time.time() - t0)}), flush=True)
# 3. cost per evaluation
sys.path.insert(0, "/home/user/test1/tests")
from test_handvalue import _positions
from svsim.learn.contrast import features_of
from svsim.search.evaluate import after_end_of_turn
pos, _ = _positions(n_games=3)
ends = [(after_end_of_turn(st), p) for st, p in pos if not after_end_of_turn(st).over]
t = time.perf_counter()
for e, p in ends * 3: features_of(e, p, 2, ())
t_base = (time.perf_counter() - t) / (3 * len(ends))
t = time.perf_counter()
for e, p in ends * 3: features_of(e, p, 2, ("clock",))
t_clock = (time.perf_counter() - t) / (3 * len(ends))
lins = [features_of(e, p, 2, ("clock",)) for e, p in ends]
net.index = lut
t = time.perf_counter()
for (e, p), x in zip(ends * 3, lins * 3): net.logit(e, p, x)
t_net = (time.perf_counter() - t) / (3 * len(ends))
print(json.dumps({"cost_us": {"linear_features": round(t_base * 1e6, 1), "with_clock": round(t_clock * 1e6, 1),
                              "network_on_top": round(t_net * 1e6, 1)}}), flush=True)
