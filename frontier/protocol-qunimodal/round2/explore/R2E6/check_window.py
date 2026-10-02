"""Check E_inf (B4 limit, = exact E for in-box realizations checked in fam_mix) lies in the explicit window
computed from (r,k,S1,L) only. Families: residue patterns cycled; k up to 40 (60 for single residue)."""
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import U_inf
from theory import explicit_window, sandwich_b4
fams = [(4,[2]),(5,[2]),(5,[3]),(6,[2]),(6,[3]),(6,[4]),(7,[2]),(7,[3]),(7,[4]),(7,[5]),(8,[2]),(8,[3]),(8,[4]),(8,[5]),(8,[6]),
        (9,[4]),(10,[5]),(10,[3]),(12,[6]),(12,[5]),(15,[7]),(20,[10]),(20,[3]),(30,[15]),(30,[2]),
        (6,[2,3,4]),(7,[2,3,4,5]),(8,[2,3,4,5,6]),(6,[1,2,3,4,5]),(6,[1,3]),(6,[2,5]),(8,[1,4,7]),(10,[2,5,8]),(12,[1,6,11]),(9,[2,2,7]),(16,[3,8,13])]
tot = 0; bad = 0; width = []
for r, pat in fams:
    kmax = 60 if len(set(pat)) == 1 else 40
    for j in range(1, kmax // len(pat) + 1):
        s = pat * j; k = len(s)
        if k < 3: continue
        Ui, tau, M, S1 = U_inf(r, s)
        E = max(Ui)
        Em, Ep, npl, nmi = explicit_window(r, s)
        (nlo, nhi, Elo, Ehi), _ = sandwich_b4(r, s)
        tot += 1
        width.append(Ep - Em)
        if not (Em <= Elo <= E <= Ehi <= Ep):
            bad += 1; print("VIOLATION", r, pat, k, Em, Elo, E, Ehi, Ep)
print("cases", tot, "violations", bad, "max explicit width", max(width), "mean width %.2f" % (sum(width)/len(width)))
