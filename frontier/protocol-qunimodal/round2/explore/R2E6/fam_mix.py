"""Residue-pattern families: residues s_i cycle through PATTERN (fixed proportions), k = len(pattern)*j.
In-box realization a_i = largest value <= 100 with residue s_i (k <= 40, or <= 60 if pattern has one residue).
Prints exact E (actual a), E_inf (B4 limit), sandwich (B4 delta), asymptotic prediction.
usage: fam_mix.py r s1,s2,... kmax
"""
import sys, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst, in_box
from b4limit import U_inf
from theory import sandwich_b4, asym_pred

r = int(sys.argv[1]); pat = [int(x) for x in sys.argv[2].split(',')]; kmax = int(sys.argv[3])
val = {s: max(x for x in range(1, 101) if x % r == s) for s in set(pat)}
p = len(pat)
ap = asym_pred(r, pat)
print("# r=%d pattern=%s sigma1=%.4f L=%.4f theta*=%.4f c=%.4f kappa=%.4f" % (r, pat, ap['sigma1'], ap['L'], ap['theta'], ap['c'], ap['kappa']))
print("# k E_exact E_inf E6 Elo Ehi | c*k  c*k-kappa*ln k | resid=E-(ck-kappa ln k) | holes(e-values)")
for j in range(1, kmax // p + 1):
    s = pat * j
    k = len(s)
    a = sorted(val[x] for x in s)
    if not in_box(r, a) or k < 3:
        continue
    I = Inst(r, a)
    E, U = I.excess()
    E6 = I.T6() - 1 - I.F
    Ui, tau, M, S1 = U_inf(r, s)
    (nlo, nhi, Elo, Ehi), _ = sandwich_b4(r, s)
    q = asym_pred(r, s)
    holes = [b - 1 - I.F for b in range(1 + I.F, max(U)) if b not in U]
    flag = "" if max(Ui) == E else " MISMATCH"
    print(k, E, max(Ui), E6, Elo, Ehi, "| %.2f %.2f | %.2f |" % (q['lead'], q['withlog'], E - q['withlog']), holes, flag, flush=True)
