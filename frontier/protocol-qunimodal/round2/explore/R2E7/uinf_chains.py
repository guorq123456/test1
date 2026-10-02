# U_inf as two chains: odd chain {1,3,..,eo}, even chain {2,4,..,ee} (ee=0 if 2 not in U_inf).
# Checks (a) chain structure (proved: R(Delta)=>R(Delta+2r)); (b) eo in {T,T-2}, ee in {eo-1,eo-3}
# with T=T6-F=1+floor((S-k+1-2mu)/r); (c) joint histogram of (T-eo, eo-ee).
# Usage: python3 uinf_chains.py RLIST KLIST
import sys, itertools
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
def mu_of(tau):
    m = len(tau) - 1
    while m > 0 and tau[m] <= 0: m -= 1
    return m
H = Counter(); chainbad = 0; n = 0; byr = Counter()
for r in RLIST:
    for k in KLIST:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); ui = Uinf(r, res); tau = tau_vec(r, res); n += 1
            T = 1 + (sum(res) - k + 1 - 2*mu_of(tau))//r
            odd = sorted(e for e in ui if e % 2); even = sorted(e for e in ui if e % 2 == 0)
            eo = max(odd); ee = max(even) if even else 0
            if odd != list(range(1, eo+1, 2)) or even != list(range(2, ee+1, 2)): chainbad += 1
            H[(T - eo, eo - ee)] += 1; byr[(r, T-eo, eo-ee)] += 1
print(f'r={RLIST} k={KLIST} multisets={n} chain-structure violations={chainbad}')
print('  joint histogram (T-eo, eo-ee):', dict(sorted(H.items())))
