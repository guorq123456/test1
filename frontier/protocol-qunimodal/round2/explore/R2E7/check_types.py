# Exhaustive residue-level check: rule_types.shape(r,res) == rule_B4.Uinf(r,res) for all multisets.
# Also counts errors of simpler candidate shapes.  Usage: python3 check_types.py RLIST KLIST
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from rule_B4 import Uinf, _tau
from rule_types import shape
RL = list(map(int, sys.argv[1].split(','))); KL = list(map(int, sys.argv[2].split(',')))
n = bad = badT = 0
for r in RL:
    for k in KL:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); U = Uinf(r, res); n += 1
            if shape(r, res) != U: bad += 1; print('shape mismatch', r, res, sorted(U), sorted(shape(r,res)))
            tau = _tau(r, res); mu = max([t for t in range(r) if tau[t] > 0], default=0)
            T = 1 + (sum(res)-k+1-2*mu)//r
            if U != set(range(1, T+1)): badT += 1
print(f'r={RL} k={KL} multisets={n} three-type-rule mismatches={bad}  "U_inf=[1,T6-F]" mismatches={badT}')
