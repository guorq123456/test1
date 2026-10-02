# Conjectural closed shape of U_inf (path R2E7): with T = 1+floor((S-k+1-2mu)/r) (= T6-F),
#   U_inf = [1,T]            if beta1 and beta2
#         = [1,T] \ {T-1}    if beta1 and not beta2
#         = [1,T-2]          if not beta1
# beta1: for all m in [max(0, floor(D_T/2)+1), mu]:  C(m+k-2,k-2) - [m<=D_T] C(D_T-m+k-2,k-2) >= tau_m,
#        D_T = S-k+1-r(T+1)      (only positions m<=mu; all m<r)
# beta2: R(D_{T-1}) (full window test), D_{T-1} = D_T + r.
# mu = largest t in [0,r-1] with tau_t > 0 (0 if none).  Same domain as rule_B4.
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from math import comb
from rule_B4 import _tau, R, domain, L0

def B(n, k):
    if n < 0: return 0
    return comb(n + k - 2, k - 2) if k >= 2 else (1 if n == 0 else 0)

def shape(r, res):
    k = len(res); tau = _tau(r, res); K0 = sum(res) - k + 1
    mu = max([t for t in range(r) if tau[t] > 0], default=0)
    T = 1 + (K0 - 2*mu)//r
    DT = K0 - r*(T+1)
    beta1 = all(B(m, k) - (B(DT - m, k) if m <= DT else 0) >= tau[m] for m in range(max(0, DT//2 + 1), mu + 1))
    beta2 = R(r, k, tau, DT + r) if T - 1 >= 2 else True
    if beta1 and beta2: U = set(range(1, T+1))
    elif beta1: U = set(range(1, T+1)) - {T-1}
    else: U = set(range(1, T-1))
    return U | {1}

def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    F = sum(x//r for x in a)
    return b <= F + 1 or (b - F) in shape(r, [x % r for x in a])
