"""All-equal family a_i = a (k <= 60, a <= 100): exact E, E6, sandwich (actual g), sandwich (B4), asymptotic prediction."""
import sys, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst
from theory import sandwich_actual, sandwich_b4, asym_pred
r = int(sys.argv[1]); a = int(sys.argv[2]); ks = list(range(int(sys.argv[3]), int(sys.argv[4]) + 1, int(sys.argv[5]) if len(sys.argv) > 5 else 1))
s = a % r
ap = asym_pred(r, [s])
print("# r=%d a=%d s=%d sigma1=%.3f L=%.4f theta*=%.4f c=%.4f kappa=%.4f" % (r, a, s, ap['sigma1'], ap['L'], ap['theta'], ap['c'], ap['kappa']))
print("# k E E6 | sandA(nlo nhi Elo Ehi mono) | sandB4(nlo nhi Elo Ehi) | ck  ck-kappa*logk | holes")
for k in ks:
    I = Inst(r, [a] * k)
    E, U = I.excess(); E6 = I.T6() - 1 - I.F
    (nlo, nhi, Elo, Ehi), M, mono = sandwich_actual(I)
    (bnlo, bnhi, bElo, bEhi), _ = sandwich_b4(r, [s] * k)
    p = asym_pred(r, [s] * k)
    holes = [b - 1 - I.F for b in range(1, max(U)) if b not in U]
    print(k, E, E6, "|", nlo, nhi, Elo, Ehi, int(mono), "|", bnlo, bnhi, bElo, bEhi, "| %.2f %.2f" % (p['lead'], p['withlog']), "|", holes, flush=True)
