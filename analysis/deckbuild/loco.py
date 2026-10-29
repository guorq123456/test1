"""Leave-one-class-out within the old pool: train on deals between 6 classes' decks, score deals that involve the
7th class (its class cards never seen). Chooses the deck model's size and regularization without new-pool labels."""
import sys, json
import numpy as np
from svsim.learn import deckmodel as D

recs = D.load_records([sys.argv[1]])
craft = lambda code: code.split(".")[1]
configs = [(32, 32, 1e-4), (8, 8, 1e-3), (8, 8, 1e-2), (4, 4, 1e-2), (16, 16, 3e-3)]
out = {}
for h, h2, l2 in configs:
    losses, base = [], []
    for c in "1234567":
        test = [r for r in recs if craft(r[0]) == c or craft(r[1]) == c]
        train = [r for r in recs if craft(r[0]) != c and craft(r[1]) != c]
        m, _ = D.fit(train, h, h2, epochs=15, l2=l2, log=lambda s: None)
        e = D.evaluate(m, test)
        losses.append(e["log_loss"]); base.append(e["log_loss_mean"])
    out[f"h{h}/{h2} l2 {l2}"] = (round(float(np.mean(losses)), 4), round(float(np.mean(base)), 4))
    print(f"h{h}/{h2} l2 {l2}: unseen-class log loss {np.mean(losses):.4f} vs constant {np.mean(base):.4f}", flush=True)
