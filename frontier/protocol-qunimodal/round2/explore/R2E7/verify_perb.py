# Verify the per-b theorem: k>=2, r | no a_i, b>=2, L=min a >= Delta/2 + r + 1 where
# Delta = D+1-r(b+1)  ==>  (P unimodal <=> R(Delta)).  Also reports instances just outside.
# Usage: python3 verify_perb.py SEED NTRIALS
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
seed = int(sys.argv[1]); NT = int(sys.argv[2])
rng = random.Random(seed)
inside = bad_in = 0; outside = bad_out = 0
for trial in range(NT):
    r = rng.randint(2, 30)
    k = rng.randint(2, 12)
    a = []
    while len(a) < k:
        x = rng.randint(1, rng.choice([2*r, 4*r, 100]))
        if x <= 100 and x % r: a.append(x)
    a.sort()
    D = sum(x-1 for x in a); L = a[0]
    res = [x % r for x in a]; tau = tau_vec(r, res)
    # choose b values: all b with 2<=b<= F+ (S-k+1)//r + 4
    F = sum(x//r for x in a)
    bmax = F + (sum(res)-k+1)//r + 4
    bs = list(range(2, bmax+1))
    gt = gt_profile(r, a, bs)
    w = wcoef(k, r, D + 4*r + 10)
    for b, g in zip(bs, gt):
        Delta = D + 1 - r*(b+1)
        p = R(r, k, tau, Delta, w)
        if 2*L >= Delta + 2*r + 2:
            inside += 1
            if p != g: bad_in += 1; print('BAD-in', r, a, b, g, p)
        else:
            outside += 1
            if p != g: bad_out += 1
print(f'seed={seed} inside={inside} bad_inside={bad_in} outside={outside} mismatch_outside={bad_out}')
