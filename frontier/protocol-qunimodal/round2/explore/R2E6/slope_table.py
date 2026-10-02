"""For residue-pattern families (in-box realization a_i = largest value <=100 with the residue; E computed
exactly from B4 limit U_inf, which equals the exact E for these realizations -- see fam_mix.py / analyze_fitset.py),
fit E + kappa ln k = alpha k + beta by least squares over the available k-range and compare alpha with c.
Also report residual range of E - (c k - kappa ln k)."""
import sys, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import U_inf
from theory import asym_pred
from excess import Inst
import numpy as np
fams = [(4,[2]),(5,[2]),(5,[3]),(6,[2]),(6,[3]),(6,[4]),(7,[3]),(7,[4]),(8,[2]),(8,[4]),(8,[6]),(9,[4]),(10,[5]),(10,[3]),
        (12,[6]),(15,[7]),(20,[10]),(30,[15]),(30,[2]),(6,[2,3,4]),(7,[2,3,4,5]),(8,[2,3,4,5,6]),(6,[1,2,3,4,5]),
        (8,[1,4,7]),(10,[2,5,8]),(12,[1,6,11]),(16,[3,8,13])]
check_exact = '--exact' in sys.argv
print("r pattern | c  kappa | alpha_fit (k-range) | resid min max | E at kmax, E6 at kmax")
for r, pat in fams:
    kmax = 60 if len(set(pat)) == 1 else 40
    ks = []; Es = []; Xs = []
    for j in range(1, kmax // len(pat) + 1):
        s = pat * j; k = len(s)
        if k < 6: continue
        E = max(U_inf(r, s)[0])
        if check_exact:
            a = sorted(max(x for x in range(1, 101) if x % r == si) for si in s)
            I = Inst(r, a); Ee, U = I.excess(); assert Ee == E, (r, s)
        q = asym_pred(r, s)
        ks.append(k); Es.append(E); Xs.append(q['withlog'])
    q = asym_pred(r, pat)
    k_arr = np.array(ks, float); y = np.array(Es, float) + q['kappa'] * np.log(k_arr)
    A = np.vstack([k_arr, np.ones_like(k_arr)]).T
    alpha, beta = np.linalg.lstsq(A, y, rcond=None)[0]
    res = np.array(Es) - np.array(Xs)
    a = sorted(max(x for x in range(1, 101) if x % r == si) for si in pat * (ks[-1] // len(pat)))
    E6 = Inst(r, a).T6() - 1 - Inst(r, a).F
    print(r, pat, "| %.4f %.4f | %.4f (k=%d..%d) | %.2f %.2f | %d %d" % (q['c'], q['kappa'], alpha, ks[0], ks[-1], res.min(), res.max(), Es[-1], E6), flush=True)
