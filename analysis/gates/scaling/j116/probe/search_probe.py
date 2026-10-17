"""Inside real searches (gate agents and deals), check the v2 net's search-path logit at every call two ways:
cached (as played) vs the same call with the per-card / per-zone caches emptied, and vs the batch forward pass on
tokens.encode(state, player, inputs). Prints the largest differences. Run with PYTHONPATH = the 342cc14 checkout."""
import sys
import numpy as np
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.tools import gate
from svsim.cards import decks
from svsim.ui.session import DECKS

net_path, n, seed0, games = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
net = SN.load_cached(net_path)
orig = SN.SetNet.logit
stats = {"calls": 0, "d_cache": 0.0, "d_batch": 0.0, "skipped": 0}

def wrapped(self, state, player):
    v = orig(self, state, player)
    if self is not net:
        return v
    stats["calls"] += 1
    keep = (self._pool, self._zone_sums)
    self._pool, self._zone_sums = {}, {}
    v2 = orig(self, state, player)
    self._pool, self._zone_sums = keep
    stats["d_cache"] = max(stats["d_cache"], abs(v - v2))
    if stats["calls"] % 7 == 0:                      # the batch path is slower; check every 7th call
        cids, tok, glob = T.encode(state, player, self.inputs)
        idx = self._index()
        if all(int(c) in idx for c in cids):
            cards = np.array([idx[int(c)] for c in cids])
            seg = tok[:, SN._ZONE].astype(np.int64)
            z = self.forward(cards, SN.dynamic(tok, self.inputs), tok[:, SN._COUNT].astype(np.float32), seg,
                             (np.asarray(glob) / SN.global_scale(self.inputs))[None, :])
            stats["d_batch"] = max(stats["d_batch"], abs(v - float(np.asarray(z).reshape(-1)[0])))
        else:
            stats["skipped"] += 1
    return v

SN.SetNet.logit = wrapped
deck = decks.build(DECKS["ramp-t"][1])
a = f"mcts:{n}+{P}+setnet={net_path}+neteot"
b = f"mcts:100+{P}+setnet=analysis/scaling/models/net-gen4-59000.npz+neteot"
for k in range(games):
    seed, seat = seed0 + k // 2, k % 2
    pts, _ = gate._game(deck, deck, seat, gate._agent(a, 2 * seed + seat, None), gate._agent(b, 2 * seed + 1 - seat, None),
                        seed, "probe", ["ramp-t", "ramp-t"])
    print(f"game {k}: seed {seed} seat {seat} A {pts}  {stats}", flush=True)
print("final", stats)
