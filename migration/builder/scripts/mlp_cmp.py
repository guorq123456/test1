import pickle, sys, numpy as np
from pathlib import Path
from svsim.learn.model import LinearValue
from svsim.learn.netdata import ENDED, ACT
from svsim.learn import mlp
rows, inst_dir, inst_name, new_dir, new_name = sys.argv[1:6]
games = pickle.loads(Path(rows).read_bytes())
inst = {m: LinearValue.load(Path(inst_dir) / f"{inst_name}-{m}.json") for m in ("ended", "act")}
new = {m: LinearValue.load(Path(new_dir) / f"{new_name}-{m}.json") for m in ("ended", "act")}
def z(model, X):
    Xs = (X - np.array(model.mean)) / np.array(model.std)
    out = Xs @ np.array(model.coef)
    if model.hidden:
        out = out + np.tanh(Xs @ np.array(model.hidden["W1"]) + np.array(model.hidden["b1"])) @ np.array(model.hidden["w2"])
    return out
for ph, m in ((ENDED, "ended"), (ACT, "act")):
    va = [r for gid, rs in games if mlp.held_out(gid) for r in rs if r[1] == ph and r[3] != 0.5]
    X = np.array([r[2] for r in va]); y = np.array([r[3] for r in va]); w = np.array([r[5] for r in va])
    for name, mod in (("installed", inst[m]), ("mlp", new[m])):
        zz = z(mod, X); print(m, name, "held-out loss %.4f acc %.4f" % (mlp._logloss(zz, y, w), mlp._accuracy(zz, y)))
    if ph == ENDED:
        for name, mods in (("installed", inst), ("mlp", new)):
            d = z(mods["act"], X) - z(mods["ended"], X); print("ACT-ENDED", name, "mean %.3f sd %.3f" % (d.mean(), d.std()))
