# Sharpness of L0(r,res)=ceil((S-k+3-r)/2): for every residue multiset (r in RLIST, k in KLIST),
# search configurations with min a >= L (each a_i in {base_i, base_i+r}, base_i = least part >= L
# with residue s_i) for L = L0-1 down to 1, and record the largest L at which the description
# U = [1,F+1] u (F+Uinf) fails.  Output: per (r,k) the counts of multisets with Lfail = L0-1, < L0-1, none.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
for r in RLIST:
    for k in KLIST:
        stats = {}; worst = []
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); L0v = L0(r, res); ui = Uinf(r, res); emax = max(ui)
            lfail = None
            for L in range(L0v-1, 0, -1):
                base = []
                for s in res:
                    x = s
                    while x < L: x += r
                    base.append(x)
                found = False
                for bits in itertools.product([0,1], repeat=k):
                    a = sorted(x + r*t for x, t in zip(base, bits))
                    if max(a) > 100: continue
                    F = sum(x//r for x in a)
                    bs = list(range(1, F + emax + 3))
                    gt = gt_profile(r, a, bs)
                    pred = [(b <= F+1) or ((b-F) in ui) for b in bs]
                    if gt != pred: found = True; break
                if found: lfail = L; break
            gap = None if lfail is None else L0v - lfail
            stats[gap] = stats.get(gap, 0) + 1
            if gap == 1: worst.append(tuple(res))
        print(f'r={r} k={k} gap(L0 - largest failing L) histogram: {dict(sorted(stats.items(), key=lambda t: (t[0] is None, t[0] or 0)))}  sharp examples: {worst[:4]}', flush=True)
