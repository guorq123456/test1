# For each residue multiset: T = T6-F; beta1 = R(Delta_T), beta2 = R(Delta_{T-1}).
# Record, for failures, the failing m relative to mu (offset m-mu), whether POS (m>Delta) or MID,
# and whether m < r (so w_m is a single binomial).  Usage: python3 bits_anatomy.py RLIST KLIST
import sys, itertools
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
def mu_of(tau):
    m = len(tau) - 1
    while m > 0 and tau[m] <= 0: m -= 1
    return m
C = Counter(); ex = {}
for r in RLIST:
    for k in KLIST:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); tau = tau_vec(r, res); mu = mu_of(tau); S = sum(res); K0 = S - k + 1
            T = 1 + (K0 - 2*mu)//r
            w = wcoef(k, r, K0 + 4*r)
            W = lambda n: w[n] if n >= 0 else 0
            for lab, e in (('T', T), ('T-1', T-1)):
                if e < 2: continue
                Dl = K0 - r*(e+1); lo = Dl//2 + 1
                fails = []
                for m in range(lo, lo + r):
                    if W(m) - W(Dl - m) < tau[m % r]:
                        fails.append(('POS' if m > Dl else ('NEG' if m < 0 else 'MID'), m - mu, m < r))
                key = (lab, 'fail' if fails else 'ok', tuple(sorted(set((f[0], f[1]) for f in fails))))
                C[key] += 1; ex.setdefault(key, (r, tuple(res)))
for kk, v in sorted(C.items(), key=lambda t: (t[0][0], -t[1])): print(v, kk, 'e.g.', ex[kk])
