# For residue vectors rho, enumerate lifts s (a = rho + r s, s_i in [0,Smax]) and record J(s), compared with J_inf.
# Reports: S2 failures, cases where J(s) is not of the form J_inf ∩ [0,c], distribution of shapes.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import Jinf
r, kmax, Smax = map(int, sys.argv[1:4])
tot = 0; s2bad = 0; notprefix = 0; examples = []
for k in range(1, kmax + 1):
    for rho in itertools.combinations_with_replacement(range(1, r), k):
        rho = list(rho)
        Ji = Jinf(r, rho)
        for s in itertools.product(range(Smax + 1), repeat=k):
            a = [rho[i] + r * s[i] for i in range(k)]
            if max(a) > 100: continue
            J = Jset(r, a)
            tot += 1
            if not S2_shape(J): s2bad += 1; print("S2FAIL", r, a, J)
            if not set(J) <= set(Ji): print("NOT SUBSET of Jinf", r, a, J, Ji)
            # prefix of Jinf?
            pref = [x for x in Ji if x <= max(J)]
            if J != pref:
                notprefix += 1
                if len(examples) < 15: examples.append((rho, s, J, Ji))
print(f"r={r} kmax={kmax} Smax={Smax}: instances {tot}, S2 fails {s2bad}, J not a prefix of Jinf {notprefix}")
for e in examples: print("  ", e)
