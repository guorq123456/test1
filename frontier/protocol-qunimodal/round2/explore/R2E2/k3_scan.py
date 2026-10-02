# k<=3: distribution of E* (= B-1-F) and of max J over residue triples (small parts and some lifts), r<=30.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, Fval, Jset
import s3star_rule as S
from collections import Counter
C = Counter(); ex = []
for r in range(4, 31):
    for k in (1, 2, 3):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            for lift in itertools.product(range(0, 3), repeat=k):
                a = sorted(rho[i] + r * lift[i] for i in range(k))
                if max(a) > 100: continue
                B = S.Bvalue(r, a); F = Fval(r, a)
                E = B - 1 - F
                C[('k', k, 'E*', E)] += 1
                if E >= 2 and len(ex) < 10: ex.append((r, a, B, F, Jset(r, a)))
for k_, v in sorted(C.items()): print(k_, v)
for e in ex: print("  ", e)
