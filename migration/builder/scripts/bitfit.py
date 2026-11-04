import sys, hashlib, gzip, json
import numpy as np
root = sys.argv[1]
sys.path.insert(0, root)
from svsim.learn import midrows as MR, setnet as SN, scaledata
from pathlib import Path
d = Path(sys.argv[2])
end, mid = [d / "tok-85830000.npz"], [d / "mid-85830000.npz"]
train, valid = MR.phase_split(end, mid, d / "cards.npz", every=20, mid_rate=0.3, seed=0)
net = SN.SetNet(train.static.shape[1], seed=0, flag=True)
net.set_cards(train.card_ids, train.static, np.bincount(train.cards, minlength=len(train.card_ids)) + 1)
sub = train.subset(np.arange(train.n) < 20000)
net.fit(sub, valid.subset(np.arange(valid.n) < 3000), epochs=2, batch=256, log=lambda s: None, ftz=True)
h = hashlib.sha256()
for k in net.PARAMS:
    h.update(getattr(net, k).tobytes())
print(root, h.hexdigest(), net.info["history"][-1])
