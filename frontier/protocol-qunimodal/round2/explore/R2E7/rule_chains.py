# Explicit two-chain description of U_inf (path R2E7).  Proved equivalent to rule_B4 (proofs.txt Thm 5).
#   T = 1+floor((K0-2mu)/r), K0 = S-k+1, Delta_e = K0 - r(e+1).
#   For a chain top c in {T, T-1} with Delta = Delta_c and window Wn = {m: Delta/2 < m <= Delta/2 + r}:
#     J(m) = least j>=0 with w_{m+jr} - w_{Delta-m+jr} >= tau_{m mod r}
#     top of chain = c - 2*max_{m in Wn} J(m)
#   U_inf = {odd e <= e_odd} u {even e, 2 <= e <= e_even} (always contains 1).
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from rule_B4 import _tau, _w, L0
from rule_B4 import domain as _dom

def domain(r, a):
    return len(a) >= 2 and _dom(r, a)

def chain_top(r, k, tau, Delta, c):
    lo = Delta//2 + 1
    J = 0
    for m in range(lo, lo + r):
        j = 0
        while True:
            hi = m + j*r + 1
            w = _w(k, r, max(hi, 0) + 1); W = lambda n: w[n] if n >= 0 else 0
            if W(m + j*r) - W(Delta - m + j*r) >= tau[m % r]: break
            j += 1
            if c - 2*j < 0: break
        J = max(J, j)
    return c - 2*J

def tops(r, res):
    k = len(res); tau = _tau(r, res); K0 = sum(res) - k + 1
    mu = max([t for t in range(r) if tau[t] > 0], default=0)
    T = 1 + (K0 - 2*mu)//r
    eo = chain_top(r, k, tau, K0 - r*(T+1), T)
    ee = chain_top(r, k, tau, K0 - r*T, T-1)
    return T, max(eo, 1), max(ee, 0)

def Uinf(r, res):
    T, eo, ee = tops(r, res)
    return {e for e in range(1, T+1) if (e % 2 == 1 and e <= eo) or (e % 2 == 0 and e <= ee)}

def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    F = sum(x//r for x in a)
    return b <= F + 1 or (b - F) in Uinf(r, [x % r for x in a])
