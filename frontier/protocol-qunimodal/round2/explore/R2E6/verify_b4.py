"""Check U_inf(residues) (B4 limit) against exact U for in-box a with the same residues and a_i large (near 100)."""
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst
from b4limit import U_inf
random.seed(int(sys.argv[1]))
agree = 0; dis = 0
for trial in range(int(sys.argv[2])):
    r = random.randint(4, 12); k = random.randint(2, 30)
    s = [random.randint(1, r - 1) for _ in range(k)]
    a = sorted(max(x for x in range(1, 101) if x % r == si) for si in s)  # largest a_i<=100 with residue s_i
    I = Inst(r, a)
    U = I.U(); Ui, tau, M, S1 = U_inf(r, s)
    Ue = [b - 1 - I.F for b in U if b - 1 - I.F >= 0]
    if Ue == Ui: agree += 1
    else:
        dis += 1; print("DIFF r=%d s=%s exact=%s inf=%s" % (r, sorted(s), Ue, Ui))
print("agree", agree, "differ", dis)
