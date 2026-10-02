"""Statistics on the fit set: E vs B4-limit E_inf, vs sandwich window, vs asymptotic X = ck - kappa ln k."""
import sys, json, math
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import U_inf
from theory import sandwich_b4, explicit_window, asym_pred
rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
st = Counter(); res = []
for R in rows:
    r, a, F, U = R['r'], R['a'], R['F'], R['U']
    s = [x % r for x in a]; k = len(a)
    E = max(U) - 1 - F
    Ui, tau, M, S1 = U_inf(r, s)
    Ei = max(Ui)
    (nlo, nhi, Elo, Ehi), _ = sandwich_b4(r, s)
    q = asym_pred(r, s)
    amin = min(a)
    hyp = amin >= 2 * nlo + 2 * r
    st['n'] += 1
    st['E==Einf'] += (E == Ei)
    st['E in [Elo,Ehi]'] += (Elo <= E <= Ehi)
    st['hyp(amin>=2nlo+2r)'] += hyp
    st['hyp and E in window'] += hyp and (Elo <= E <= Ehi)
    st['amin>=r'] += amin >= r
    st['amin>=r and E==Einf'] += amin >= r and E == Ei
    st['E even'] += (E % 2 == 0)
    holes = [b for b in range(1, max(U)) if b not in U]
    st['has hole'] += bool(holes)
    st['hole only at B*-1'] += holes == [max(U) - 1]
    res.append((E - q['withlog'], R['typ'], r, k))
for kk, v in st.items(): print(kk, v)
rr = [x[0] for x in res]
print("residual E-(ck-kappa ln k): min %.2f max %.2f mean %.2f" % (min(rr), max(rr), sum(rr)/len(rr)))
for t in 'ABCD':
    z = [x[0] for x in res if x[1] == t]
    print(t, len(z), "min %.2f max %.2f" % (min(z), max(z)))
