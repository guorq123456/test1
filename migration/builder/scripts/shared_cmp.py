import pickle, sys, numpy as np
from pathlib import Path
from svsim.cards.decks import NAMED
from svsim.learn import deckdesc, mlp
from svsim.learn.model import LinearValue
from svsim.learn.netdata import ACT, ENDED
rows, me, op, shared_dir = sys.argv[1:5]
games = pickle.loads(Path(rows).read_bytes())
desc = np.array(deckdesc.describe(NAMED[me]) + deckdesc.describe(NAMED[op]))
pair = f"{me}-{op}"
models = {"installed": "svsim/learn/phased_models", "E2": sys.argv[5] if len(sys.argv) > 5 else None, "shared": shared_dir}
def z(model, X):
    if model.deck_desc:
        X = np.hstack([X, np.tile(desc, (len(X), 1))])
    Xs = (X - np.array(model.mean)) / np.array(model.std)
    out = Xs @ np.array(model.coef)
    if model.hidden:
        out = out + np.tanh(Xs @ np.array(model.hidden["W1"]) + np.array(model.hidden["b1"])) @ np.array(model.hidden["w2"])
    return out
for ph, m in ((ENDED, "ended"), (ACT, "act")):
    va = [r for gid, rs in games if mlp.held_out(gid) for r in rs if r[1] == ph and r[3] != 0.5]
    X = np.array([r[2] for r in va], np.float64); y = np.array([r[3] for r in va]); w = np.array([r[5] for r in va])
    for name, d in models.items():
        if not d or not (Path(d) / f"{pair}-{m}.json").exists():
            continue
        mod = LinearValue.load(Path(d) / f"{pair}-{m}.json")
        zz = z(mod, X)
        print(m, len(va), name, "loss %.4f acc %.4f" % (mlp._logloss(zz, y, w), mlp._accuracy(zz, y)))
