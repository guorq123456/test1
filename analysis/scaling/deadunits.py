"""How much of a scaling-test net is in use: dead units, inputs that never vary, weights that are 0 (the architecture
thread 2026-10-16 04:37Z; a description only, nothing in the test changes). Condition: the opponent's deck list is
known (order and hand not).

    python analysis/scaling/deadunits.py --tokens TOKDIR [--nets net-10000 net-gen2-20000 net-100000]

For each net (models/<name>.npz):
1. units per layer whose output is never positive (0 for ReLU) at every holdout turn end (the 5 tok-702000xx files): phi's two layers over every
   token of those positions, rho's two layers over the positions;
2. inputs that are 0 throughout the net's own training data (its info "shards", the validation part included):
   - phi's: the standardized static row of every card a token there has, and the token's dynamic values;
   - rho's: the pooled zone sums (7 zones x phi's width) and the scaled globals;
3. per weight array: how many are exactly 0, subnormal (below 2.2e-308) and normal.
Writes data/deadunits.json and prints it.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import json      # noqa: E402
import sys       # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from svsim.learn.setnet import NZ, Data, SetNet, _TINY, _act, _segsum  # noqa: E402


class Seen:
    """Per dimension, over batches: ever nonzero (inputs) or ever positive (a unit's output: with leaky ReLU a unit
    whose output is never positive is dead in the same sense, its input always on the flat side)."""

    def __init__(self, width: int, positive: bool = False):
        self.any = np.zeros(width, dtype=bool)
        self.positive = positive

    def add(self, x: np.ndarray) -> None:
        if len(x):
            self.any |= np.any(x > 0 if self.positive else x != 0, axis=0)


def _layers(net: SetNet, batch, static):
    """(phi input, H1, H2, rho input, Z1, Z2) of one batch."""
    cards, dyn, count, seg, glob = batch
    B = glob.shape[0]
    S = net._S()
    x_phi = np.concatenate([S[cards], dyn], axis=1)
    A1 = (S @ net.W1s)[cards] + dyn @ net.W1d + net.b1
    H1 = _act(A1, net.slope)
    H2 = _act(H1 @ net.W2 + net.b2, net.slope)
    P = _segsum(H2, count, seg, B * NZ).reshape(B, -1)
    U = np.concatenate([P, glob], axis=1)
    Z1 = _act(U @ net.V1 + net.c1, net.slope)
    Z2 = _act(Z1 @ net.V2 + net.c2, net.slope)
    return x_phi, H1, H2, U, Z1, Z2


def _pass(net: SetNet, data: Data, step: int = 2048):
    widths = [net.static.shape[1] + net.W1d.shape[0], net.phi[0], net.phi[1], net.V1.shape[0], net.rho[0],
              net.rho[1]]
    seen = [Seen(w, positive=i in (1, 2, 4, 5)) for i, w in enumerate(widths)]
    for s in range(0, data.n, step):
        for sn, arr in zip(seen, _layers(net, data.batch(np.arange(s, min(s + step, data.n))), None)):
            sn.add(arr)
    return [int((~sn.any).sum()) for sn in seen], [sn.any for sn in seen]


def _align(net: SetNet, data: Data) -> Data:
    import train as T
    return T._align(net, data)


def describe(name: str, tok: Path) -> dict:
    import train as T
    net = SetNet.load(HERE / f"models/{name}.npz")
    hold = _align(net, Data([tok / f"tok-{s}.npz" for s in T.HOLDOUT], tok / "cards.npz"))
    dead_hold, _ = _pass(net, hold)
    del hold
    shards = net.info.get("shards") or T.shards(net.info["size"])
    train = _align(net, Data([tok / f"tok-{s}.npz" for s in shards], tok / "cards.npz"))
    zero_train, any_train = _pass(net, train)
    n_train = int(train.n)
    del train
    weights = {}
    for k in SetNet.PARAMS:
        a = getattr(net, k)
        zero = int((a == 0).sum())
        sub = int(((a != 0) & (np.abs(a) < _TINY)).sum())
        weights[k] = {"size": int(a.size), "zero": zero, "subnormal": sub, "normal": int(a.size) - zero - sub}
    h1, h2 = net.phi
    r1, r2 = net.rho
    n_static, n_dyn = net.static.shape[1], net.W1d.shape[0]
    pooled_zero = int((~any_train[3][:NZ * h2]).sum())
    globals_zero = int((~any_train[3][NZ * h2:]).sum())
    return {
        "net": name, "slope": net.slope, "holdout_turn_ends": 93787, "training_turn_ends": n_train,
        "dead_on_holdout": {"phi_layer1": f"{dead_hold[1]} of {h1}", "phi_layer2": f"{dead_hold[2]} of {h2}",
                            "rho_layer1": f"{dead_hold[4]} of {r1}", "rho_layer2": f"{dead_hold[5]} of {r2}"},
        "dead_on_training": {"phi_layer1": f"{zero_train[1]} of {h1}", "phi_layer2": f"{zero_train[2]} of {h2}",
                             "rho_layer1": f"{zero_train[4]} of {r1}", "rho_layer2": f"{zero_train[5]} of {r2}"},
        "inputs_always_0_in_training": {
            "phi_static": f"{int((~any_train[0][:n_static]).sum())} of {n_static}",
            "phi_dynamic": f"{int((~any_train[0][n_static:]).sum())} of {n_dyn}",
            "rho_pooled": f"{pooled_zero} of {NZ * h2}", "rho_globals": f"{globals_zero} of {any_train[3].size - NZ * h2}"},
        "weights": weights,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--nets", nargs="+", default=["net-10000", "net-gen2-20000", "net-100000"])
    args = ap.parse_args()
    out = [describe(n, Path(args.tokens)) for n in args.nets]
    (HERE / "data/deadunits.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
