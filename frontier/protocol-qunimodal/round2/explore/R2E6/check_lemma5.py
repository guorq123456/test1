"""Check Lemma 5 (window width bound) on the fit+holdout residue vectors."""
import sys, json, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import sandwich_b4
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
bad = 0; n = 0; wmax = 0
for R in rows:
    r, a = R['r'], R['a']; s = [x % r for x in a]; k = len(a)
    (nlo, nhi, Elo, Ehi), M = sandwich_b4(r, s)
    Elo_raw = (sum(x - 1 for x in s) + 1 - 2 * r - 2 * nlo) // r
    n += 1
    if nlo >= 1:
        Rr = (nlo + k - 3) / nlo
        ok = (nlo - nhi) < r + math.log(2 * r) / math.log(Rr) if Rr > 1 else True
        okE = (Ehi - Elo_raw) < 3 + 2 * math.log(2 * r) / (r * math.log(Rr)) if Rr > 1 else True
    else:
        ok = nlo - nhi <= r; okE = True
    bad += not (ok and okE)
    wmax = max(wmax, Ehi - Elo_raw)
print("checked", n, "violations", bad, "max E_hi-E_lo", wmax)
