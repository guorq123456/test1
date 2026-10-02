# Residue-level certificate for S2 (peeling path).  For a residue multiset rho (all parts in [1,r-1]):
#  (E_rho): ND_rho(K) holds for every K = sigma+1 (mod 2r) with K <= sigma+1-2r          [even j family]
#  (O_rho): ND_rho(K) holds for every K = sigma+1+r (mod 2r) with 2 mu*_inf + 3r <= K <= sigma+1-2r   [odd j]
# where ND(K): for all integers x with K - r <= 2x < K:  Q_{K-x} >= d_x,
#   d = coeffs of A_rho(q)/[r]_q (0 at negative index), tau_t = residue sums of (1-q)A_rho, Q_u = d_u - tau_{u mod r},
#   mu*_inf = max{u in Z : f_u < tau_u}, f = coeffs of 1/((1-q)^{k-1}(1-q^r)) (0 at negative index).
# Theorem (proof file): if (E_rho) and (O_rho) hold then S2 holds for EVERY a (any sizes) with residue multiset rho.
# Usage: python3 residue_check.py r kmax   -> prints counts; exits nonzero on failure.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau, dinf_seq

def mustar_inf(r, rho, tt):
    k = len(rho); sigma = sum(x - 1 for x in rho)
    L = sigma + 3 * r + 5
    tmax = max(tt)
    while True:
        f = dinf_seq(k, r, L)
        # k>=2: f nondecreasing, so f_u >= f_{L-r..L} min >= tmax guarantees no u>L-r with f_u<tau_u
        if k == 1 or min(f[L - r:L + 1]) >= tmax: break
        L *= 2
    fu = lambda u: f[u] if u >= 0 else 0
    # Q_inf,u = f_u - tau_u ; for u > L it is >= 0 (k>=2: f nondecreasing and f >= max tau beyond L-r;
    # k=1: f_u=[r|u], tau in {0,+1,-1} with +1 only at class 0, so f_u<tau_u only for u<0)
    for u in range(L, -2 * r - 1, -1):
        if fu(u) < tt[u % r]: return u
    return None

def nd_ok(r, ds, tt, K):
    lo = (K - r) // 2 - 1
    for x in range(lo, (K + 1) // 2 + 1):
        if not (K - r <= 2 * x < K): continue
        u = K - x
        if ds(u) - tt[u % r] < ds(x): return False
    return True

def check_rho(r, rho):
    ds = DS(r, rho); tt = tau(r, rho)
    sigma = sum(x - 1 for x in rho)
    ms = mustar_inf(r, rho, tt)
    Kmax = sigma + 1 - 2 * r
    okE = okO = True
    K = Kmax
    while K >= -4 * r:   # even family: all K (negative K included; trivially true there by tau sign pattern)
        even = ((K - sigma - 1) % (2 * r)) == 0
        if even:
            if not nd_ok(r, ds, tt, K): okE = False
        else:
            if ms is not None and K >= 2 * ms + 3 * r and not nd_ok(r, ds, tt, K): okO = False
        K -= r
    return okE, okO, ms

if __name__ == '__main__':
    r, kmax = int(sys.argv[1]), int(sys.argv[2])
    tot = 0; fE = 0; fO = 0
    for k in range(1, kmax + 1):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            okE, okO, ms = check_rho(r, list(rho))
            tot += 1
            if not okE: fE += 1; print("E FAIL", r, rho, flush=True)
            if not okO: fO += 1; print("O FAIL", r, rho, ms, flush=True)
    print(f"r={r} kmax={kmax}: residue multisets {tot}, E failures {fE}, O failures {fO}", flush=True)
    sys.exit(1 if (fE or fO) else 0)
