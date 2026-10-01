# RULE A (closed form, residue-only): B*_A = 1 + floor((D+1-2*mu)/r),
# mu = least t in [0,r-1] with Gamma_t >= Gamma_{t+1} >= ... >= Gamma_{r-1}.
# predict: b <= B*_A. Proven to be an UPPER bound for the unimodal range (necessary condition);
# exact for r=2,3 in the fit box; overshoots for some r=4,5,6 cases.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import gamma
def domain(r, a):
    return True
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a):
        return True
    G = gamma(r, a); D = sum(x-1 for x in a)
    mu = r-1
    while mu > 0 and G[mu-1] >= G[mu]:
        mu -= 1
    return b <= 1 + (D + 1 - 2*mu)//r
