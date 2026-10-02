# Explore parity mechanism: B0 = min(E6, Z*), Z* from beta = max Bad.  Check Q1,Q2,Q3 and print failing P-pairs.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter

def analyze(r, a):
    ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
    rho = [x % r for x in a]
    sigma = sum(x - 1 for x in rho); mu = mu_of(tt, r); e6 = (sigma + 1 - 2 * mu) // r
    Kj = lambda j: sigma + 1 - r * (j + 2)
    if bad:
        beta = max(bad); zs = (sigma + 1 - 2 * r - beta) // r
    else:
        beta = None; zs = 10 ** 9
    B0 = min(e6, zs)
    pset = [j for j in range(0, B0 + 1) if P_ok(r, ds, tt, Kj(j))]
    return dict(ds=ds, tt=tt, bad=bad, sigma=sigma, mu=mu, e6=e6, beta=beta, zs=zs, B0=B0, pset=pset, Kj=Kj)

def pfails(r, info, K):
    ds, tt = info['ds'], info['tt']
    return [(x, K - x) for x in range(0, (K + 1) // 2) if 2 * x < K and ds(K - x) - ds(x) < -tt[x % r]]

if __name__ == '__main__':
    r, kmax, amax = map(int, sys.argv[1:4])
    vals = [x for x in range(1, amax + 1) if x % r]
    C = Counter(); shown = Counter()
    for k in range(1, kmax + 1):
        for a in itertools.combinations_with_replacement(vals, k):
            a = list(a); I = analyze(r, a); B0 = I['B0']; ps = set(I['pset'])
            if B0 < 0: C['B0<0'] += 1; continue
            q1 = all(j in ps for j in range(0, B0 - 1))
            C[('Q1', q1)] += 1
            if B0 % 2 == 1:
                C[('Q2: B0 odd; B0 notin P', B0 not in ps, 'B0-1 in P', (B0 - 1) in ps)] += 1
                key = 'odd'
            else:
                if B0 not in ps: C[('Q3: B0 even notin P; B0-1 notin P', (B0 - 1) not in ps)] += 1
            if B0 % 2 == 1 and shown['odd'] < 6:
                shown['odd'] += 1
                K = I['Kj'](B0)
                print("odd B0:", a, "sigma", I['sigma'], "mu", I['mu'], "E6", I['e6'], "bad", I['bad'], "Z*", I['zs'], "K_B0", K, "Pfails", pfails(r, I, K)[:4])
    print(r, kmax, amax, sorted(C.items(), key=str))
