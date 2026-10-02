"""Numerical sanity check of the proved statements on the fit set (exact ground truth U):
 Thm1/Cor1: if k>=3 and a_min >= 2 n_lo + 2r then max(0,E_lo) <= E <= E_hi;
            if moreover a_min >= S1 + 2 - r then [1, 1+F+E_lo] subset of U;
            and U has no element >= F + 2 + E_hi.
 Thm2: explicit window from (r,k,S1,L): E_minus <= E <= E_plus under a_min >= 2 n_plus + 2r.
"""
import sys, json
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import sandwich_b4, explicit_window
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
c = dict(h1=0, ok1=0, h2=0, ok2=0, h3=0, ok3=0)
for R in rows:
    r, a, F, U = R['r'], R['a'], R['F'], R['U']
    s = [x % r for x in a]; k = len(a); S1 = sum(x - 1 for x in s)
    E = max(U) - 1 - F
    (nlo, nhi, Elo, Ehi), M = sandwich_b4(r, s)
    amin = min(a)
    if amin >= 2 * nlo + 2 * r:
        c['h1'] += 1
        c['ok1'] += (Elo <= E <= Ehi) and all(b <= F + 1 + Ehi for b in U)
        if amin >= S1 + 2 - r:
            c['h2'] += 1
            c['ok2'] += all(b in U for b in range(1, F + 2 + Elo))
    Em, Ep, npl, nmi = explicit_window(r, s)
    if amin >= 2 * npl + 2 * r:
        c['h3'] += 1
        c['ok3'] += Em <= E <= Ep
print(c)
