# For random instances (parts >= 2, r | no a_i) record, for every b>=2 where gt != R(Delta),
# the quantity 2L - Delta (L = min part). Proven: no failure when 2L - Delta >= 2r+2.
# Also checks the necessity half: failures with R false & gt true (proven impossible when 2L-Delta >= 1).
# Usage: python3 margin_scan.py SEED NTRIALS
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
seed, NT = map(int, sys.argv[1:3]); rng = random.Random(seed)
fails = []; nb = 0; nec_viol = 0
for t in range(NT):
    r = rng.randint(3, 30); k = rng.randint(3, 14)
    a = []
    while len(a) < k:
        x = rng.randint(2, rng.choice([r, 2*r, 3*r, 100]))
        if x <= 100 and x % r: a.append(x)
    a.sort(); L = a[0]; D = sum(x-1 for x in a); F = sum(x//r for x in a)
    res = [x % r for x in a]; tau = tau_vec(r, res)
    bs = list(range(2, F + (sum(res)-k+1)//r + 4))
    gt = gt_profile(r, a, bs); w = wcoef(k, r, D + 4*r + 10)
    for b, g in zip(bs, gt):
        Delta = D + 1 - r*(b+1); p = R(r, k, tau, Delta, w); nb += 1
        if p != g:
            fails.append((2*L - Delta, r, a, b, g, p))
            if g and not p: nec_viol += 1
fails.sort(key=lambda f: -f[0]/f[1])
print(f'seed={seed} b-values={nb} failures={len(fails)} necessity-violations(R false, unimodal)={nec_viol}')
for f in fails[:6]: print('  2L-Delta=%d r=%d (ratio %.2f) a=%s b=%d gt=%s R=%s' % (f[0], f[1], f[0]/f[1], f[2], f[3], f[4], f[5]))
