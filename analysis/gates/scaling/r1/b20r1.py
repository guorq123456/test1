"""R1 pre-gate check (96c5b24): prior-ramp-r1's batch path (setpolicy encode + SetPolicy.evaluate) against the search's
path (SetPolicy.priors on the replayed state) on the first 20 games of 71600018 and 75400038. Run inside the builder
checkout: python3 b20r1.py REC_DIR DEC_DIR"""
import gzip, json, sys
import numpy as np
from svsim.learn.setpolicy import SetPolicy, Decisions, decisions
rec_dir, dec_dir = sys.argv[1:3]
pol = SetPolicy.load("analysis/scaling/models/prior-ramp-r1.npz")
np.savez(f"{dec_dir}/cards-r1.npz", card_id=pol.card_ids, static=pol.static)
for s in (71600018, 75400038):
    data = Decisions([f"{dec_dir}/dec-{s}.npz"], f"{dec_dir}/cards-r1.npz")
    p = pol.evaluate(data)
    batch = {(int(data.g[d]), int(data.step[d])): p[data.moff[d]:data.moff[d + 1]] for d in range(data.n)}
    mx, n, miss = 0.0, 0, 0
    for line in gzip.open(f"{rec_dir}/rec-{s}.jsonl.gz", "rt"):
        rec = json.loads(line)
        for i, state, legal, reps, group, pi, start in decisions(rec):
            q = np.asarray(pol.priors(state, reps), float)
            b = batch.get((rec["g"], i))
            if b is None or len(b) != len(q):
                miss += 1
                continue
            mx = max(mx, float(np.abs(q - b).max())); n += 1
    print(s, "decisions", n, "unmatched", miss, "batch decisions", data.n, "max |batch - search path|", f"{mx:.2e}")
