# Residue-level check: rule_chains.Uinf == rule_B4.Uinf; S2 shape for U_inf (e_odd > e_even >= e_odd-3);
# histogram of T-e_odd by k.  Usage: python3 check_chains.py SEED N
import sys, random
from collections import Counter, defaultdict
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
import rule_B4, rule_chains
rng = random.Random(int(sys.argv[1])); bad = s2 = n = 0; H = defaultdict(Counter)
for _ in range(int(sys.argv[2])):
    r = rng.randint(2, 30); k = rng.randint(2, 40)
    res = sorted(rng.randint(1, r-1) for _ in range(k)) if r > 2 else [1]*k
    U = rule_B4.Uinf(r, res); n += 1
    if rule_chains.Uinf(r, res) != U: bad += 1; print('chain-formula mismatch', r, res)
    T, eo, ee = rule_chains.tops(r, res)
    if not (eo > ee >= eo - 3): s2 += 1; print('S2 violation', r, res, sorted(U))
    H[(k-1)//10][T - eo] += 1
print(f'seed={sys.argv[1]} multisets={n} chain-formula mismatches={bad} S2-shape violations={s2}')
for kk in sorted(H): print(f'  k in [{10*kk+1},{10*kk+10}]: T-e_odd histogram {dict(sorted(H[kk].items()))}')
