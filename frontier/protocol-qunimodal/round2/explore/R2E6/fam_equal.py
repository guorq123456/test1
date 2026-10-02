"""Excess E(k) = B*-1-F for P = [a]_q^k [b]_{q^r}, k=1..kmax (in box: k<=60, a<=100)."""
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst
r = int(sys.argv[1]); a = int(sys.argv[2]); kmax = int(sys.argv[3])
s = a % r
for k in range(1, kmax + 1):
    I = Inst(r, [a] * k)
    E, U = I.excess()
    T6 = I.T6()
    gaps = [b for b in range(1, max(U)) if b not in U]
    print(k, "E=%d" % E, "E6=%d" % (T6 - 1 - I.F), "S1=%d" % (k * (s - 1)), "holes=%s" % gaps, flush=True)
