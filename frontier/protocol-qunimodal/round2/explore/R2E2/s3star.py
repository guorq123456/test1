# Test S3*: mu* = max(mu - r, max Bad(a)); E* = floor((sigma+1-2r-2mu*)/r).
# Claims: E* even; J(a) in {[0,E*], [0,E*]\{E*-1}, [0,E*-2]}.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter
def estar(r, a, ds=None, tt=None):
    if ds is None: ds = DS(r, a)
    if tt is None: tt = tau(r, a)
    bad = bad_set(r, a, ds, tt)
    sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
    ms = mu - r
    if bad: ms = max(ms, max(bad))
    return (sigma + 1 - 2 * r - 2 * ms) // r, ms, bad
def classify(J, E):
    full = list(range(E + 1)) if E >= 0 else []
    if J == full: return 'full'
    if E >= 2 and J == [x for x in full if x != E - 1]: return 'gap'
    if E >= 2 and J == list(range(E - 1)): return 'minus2'
    return 'OTHER'
if __name__ == '__main__':
    mode = sys.argv[1]
    C = Counter(); ex = []
    def test(r, a):
        J = Jset(r, a); E, ms, bad = estar(r, a)
        c = classify(J, max(E, 0) if E >= 0 else 0)
        C[('Eeven', E % 2 == 0, c)] += 1
        if (E % 2 or c == 'OTHER') and len(ex) < 15: ex.append((r, a, J, E, ms, bad))
    if mode == 'eq':
        for r in range(4, 13):
            for t in range(1, r):
                for k in range(1, 61):
                    test(r, [t] * k)
    else:
        r, kmax, amax = map(int, sys.argv[2:5])
        vals = [x for x in range(1, amax + 1) if x % r]
        for k in range(1, kmax + 1):
            for a in itertools.combinations_with_replacement(vals, k):
                test(r, list(a))
    print(sys.argv[1:], sorted(C.items(), key=str))
    for e in ex: print("  ", e)
