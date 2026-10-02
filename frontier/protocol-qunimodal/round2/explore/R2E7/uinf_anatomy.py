# Anatomy of U_inf: for each residue multiset decompose why e* < T6-F and where the hole comes from.
# For e>=2: classify failure of R(Delta_e) as NEG (some negative m in window with tau_m>0),
# POS (some 0<=m<=Delta with... m>Delta: w_m < tau_m), MID (some m in (Delta/2,Delta]: w_m - w_{Delta-m} < tau_m).
import sys, itertools
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
def mu_of(r, tau):
    m = r - 1
    while m > 0 and tau[m] <= 0: m -= 1
    return m
def why(r, k, tau, Delta, w):
    lo = Delta//2 + 1; reasons = set()
    W = lambda n: w[n] if n >= 0 else 0
    for m in range(lo, lo + r):
        if W(m) - W(Delta - m) < tau[m % r]:
            reasons.add('NEG' if m < 0 else ('POS' if m > Delta else 'MID'))
    return reasons
C = Counter(); ex = {}
for r in RLIST:
    for k in KLIST:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); tau = tau_vec(r, res); ui = Uinf(r, res); S = sum(res)
            w = wcoef(k, r, S + 3*r)
            es = max(ui); t6 = 1 + (S - k + 1 - 2*mu_of(r, tau))//r
            # reason for e*+1 failing, and for the hole
            key1 = ('e*=T6' if es == t6 else 'e*<T6', tuple(sorted(why(r, k, tau, S-k+1-r*(es+2), w))), 'Delta(e*+1)>=0' if S-k+1-r*(es+2) >= 0 else 'Delta(e*+1)<0')
            C[key1] += 1; ex.setdefault(key1, (r, res))
            if es >= 3 and (es-1) not in ui:
                key2 = ('hole', tuple(sorted(why(r, k, tau, S-k+1-r*es, w))), 'Delta>=0' if S-k+1-r*es >= 0 else 'Delta<0')
                C[key2] += 1; ex.setdefault(key2, (r, res))
for kk, v in sorted(C.items(), key=lambda t: -t[1]): print(v, kk, 'e.g.', ex[kk])
