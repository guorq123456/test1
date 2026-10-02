# Targeted search for failures of the B4 description just below L0.
# For random residue multisets, for L in [max(1,L0-DEPTH), L0-1], test configs:
#   (A) all parts minimal (least >= L with given residue);  (B) one part minimal = L-ish, others minimal >= L0+r;
#   (C) random parts in [L, 100].
# Records largest failing L relative to L0.  Usage: python3 sharp_search.py SEED NRES DEPTH
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
seed, NRES, DEPTH = map(int, sys.argv[1:4]); rng = random.Random(seed)
def least(s, L, r):
    x = s
    while x < L: x += r
    return x
gaps = {}; nfail_tot = 0; ntest = 0
for it in range(NRES):
    r = rng.randint(3, 30); k = rng.randint(3, 16)
    res = sorted(rng.randint(1, r-1) for _ in range(k))
    L0v = L0(r, res)
    if L0v < 3: continue
    ui = Uinf(r, res); emax = max(ui)
    best = None
    for L in range(min(L0v-1, 100), max(0, L0v-1-DEPTH), -1):
        cfgs = []
        cfgs.append(sorted(least(s, L, r) for s in res))
        for j in range(k):
            cfg = [least(s, L0v + r, r) for s in res]; cfg[j] = least(res[j], L, r); cfgs.append(sorted(cfg))
        for _ in range(6):
            cfgs.append(sorted(least(s, rng.randint(L, 100), r) for s in res))
        fail = False
        for a in cfgs:
            if min(a) < L or max(a) > 100: continue
            F = sum(x//r for x in a); bs = list(range(2, F + emax + 3))
            gt = gt_profile(r, a, bs); ntest += 1
            pred = [(b <= F+1) or ((b-F) in ui) for b in bs]
            if gt != pred:
                fail = True; nfail_tot += 1
                print('FAIL at L0-1:', r, a, 'L0', L0v, 'Uinf', sorted(ui), 'U-F', [b-F for b,g in zip(bs,gt) if g and b > F+1])
                break
        if fail: best = L; break
    g = None if best is None else L0v - best
    gaps[g] = gaps.get(g, 0) + 1
print(f'seed={seed} configs tested={ntest} gap histogram (L0 - largest failing L; None = no failure within depth {DEPTH}):', dict(sorted(gaps.items(), key=lambda t: (t[0] is None, t[0] or 0))))
