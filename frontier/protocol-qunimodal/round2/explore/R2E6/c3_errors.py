"""Breakdown of C3 (beta=-0.5) excess errors on the fit set."""
import sys, json, math
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import asym_pred
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
d = Counter(); byk = Counter(); tot_k = Counter(); byr = Counter(); hole_err = 0
for R in rows:
    r, a, F, U = R['r'], R['a'], R['F'], R['U']
    s = [x % r for x in a]; k = len(a)
    X = asym_pred(r, s)['withlog']
    Ep = 2 * math.floor((X - 0.5) / 2)
    E = max(U) - 1 - F
    d[E - Ep] += 1
    kb = (k - 1) // 10
    tot_k[kb] += 1
    if E != Ep: byk[kb] += 1; byr[r] += 1
    if E == Ep and len(U) != max(U): hole_err += 1
print("E - E_pred distribution:", sorted(d.items()))
print("instances with E==E_pred but a hole (error 1 pair):", hole_err)
print("wrong-E rate by k-decade:", {10*kb+1: "%d/%d" % (byk[kb], tot_k[kb]) for kb in sorted(tot_k)})
print("wrong-E by r:", sorted(byr.items()))
