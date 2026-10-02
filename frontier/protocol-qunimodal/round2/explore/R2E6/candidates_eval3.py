"""C11: C3 (2 floor((ck - kappa ln k + beta)/2)) clipped to the even integers of the proven window [E_lo, E_hi]."""
import sys, json, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import asym_pred, sandwich_b4
from candidates_eval import evaluate


def make(beta):
    def E_pred(r, a):
        s = [x % r for x in a]
        X = asym_pred(r, s)['withlog']
        e = 2 * math.floor((X + beta) / 2)
        (nlo, nhi, Elo, Ehi), M = sandwich_b4(r, s)
        lo = Elo + (Elo % 2); hi = Ehi - (Ehi % 2)
        if lo <= hi:
            e = min(max(e, lo), hi)
        return e
    return E_pred


rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
best = None
for i in range(-20, 11):
    beta = i / 10
    ev = evaluate(rows, make(beta))
    print("beta=%.1f" % beta, ev, flush=True)
    if best is None or ev[0] < best[1][0]:
        best = (beta, ev)
print("C11 free=1 best beta=%.1f errors(pairs, instances) =" % best[0], best[1])
