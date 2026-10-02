"""Larger cross-check of excess.Inst.unimodal vs gt_big.profile (in-box)."""
import random, sys
sys.path.insert(0, '/tmp/claude-0/qu/tools'); sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from gt_big import profile
from excess import Inst
random.seed(int(sys.argv[1]))
nt=0; nb=0
for trial in range(int(sys.argv[2])):
    r = random.randint(4, 30); k = random.randint(3, 25)
    a = sorted(random.choice([x for x in range(2,101) if x % r]) for _ in range(k))
    if any(x % r == 0 for x in a): continue
    I = Inst(r, a); T6 = I.T6()
    lo = max(1, I.F - 3)
    bs = list(range(lo, T6 + 3))
    gt = profile(r, a, bs); mine = [I.unimodal(b) for b in bs]
    nt += len(bs)
    if gt != mine: nb += 1; print("MISMATCH", r, a)
print("pairs", nt, "mismatch instances", nb)
