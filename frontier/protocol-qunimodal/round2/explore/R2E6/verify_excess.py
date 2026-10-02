"""Cross-check excess.Inst.unimodal against the ground-truth gt_big.profile on random in-box instances."""
import random, sys
sys.path.insert(0, '/tmp/claude-0/qu/tools')
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from gt_big import profile
from excess import Inst

random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
ntests = 0; nbad = 0
for trial in range(400):
    r = random.randint(4, 12)
    k = random.randint(1, 12)
    a = sorted(random.randint(1, 40) for _ in range(k))
    if any(x % r == 0 for x in a):
        continue
    I = Inst(r, a)
    T6 = I.T6()
    bs = list(range(1, T6 + 4))
    gt = profile(r, a, bs)
    mine = [I.unimodal(b) for b in bs]
    ntests += len(bs)
    if gt != mine:
        nbad += 1
        print("MISMATCH", r, a, gt, mine)
    # T6 check: nothing unimodal above T6
    assert not any(gt[b - 1] for b in bs if b > T6), (r, a)
print("instances-b pairs tested", ntests, "mismatching instances", nbad)
