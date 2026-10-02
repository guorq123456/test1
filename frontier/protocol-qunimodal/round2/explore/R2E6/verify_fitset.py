"""Re-verify fit-set ground truth with the exact checker gt_big.profile on a random sample."""
import sys, json, random
sys.path.insert(0, '/tmp/claude-0/qu/tools')
from gt_big import profile
rows = [json.loads(l) for f in sys.argv[2:] for l in open(f)]
random.seed(0)
samp = random.sample(rows, int(sys.argv[1]))
bad = 0
for R in samp:
    bs = list(range(1, R['T6'] + 3))
    gt = profile(R['r'], R['a'], bs)
    mine = [b in R['U'] for b in bs]
    if gt != mine: bad += 1; print("BAD", R['r'], R['a'])
print("checked", len(samp), "bad", bad)
