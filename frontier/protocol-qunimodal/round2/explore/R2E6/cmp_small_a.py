"""Compare exact E (actual a, possibly small) with B4-limit E_inf (same residues), all-equal families."""
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst
from b4limit import U_inf
from theory import sandwich_actual
r = int(sys.argv[1]); a = int(sys.argv[2]); kmax = int(sys.argv[3])
s = a % r
nd = 0
rows = []
for k in range(3, kmax + 1):
    I = Inst(r, [a] * k)
    E, U = I.excess()
    Ui, tau, M, S1 = U_inf(r, [s] * k)
    Ue = [b - 1 - I.F for b in U if b - 1 - I.F >= 0]
    sa, M2, mono = sandwich_actual(I)
    Elo, Ehi = (sa[2], sa[3]) if sa else (None, None)
    if Ue != Ui:
        nd += 1
    rows.append((k, E, max(Ui), Elo, Ehi, int(mono), Ue == Ui))
for row in rows:
    print(*row)
print("# r=%d a=%d: k with U_exact != F+U_inf: %d of %d" % (r, a, nd, len(rows)))
