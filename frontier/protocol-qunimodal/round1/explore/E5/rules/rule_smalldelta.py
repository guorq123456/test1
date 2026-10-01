# RULE S (closed form on the sub-domain where the residue-class counts are "flat"):
# domain: max_t |Gamma_t - Gamma_{t+1}| <= 1  (indices mod r; always true for r<=3, and whenever
#         every a_i is congruent to 1 or -1 mod r), or some r | a_i.
# predict: b <= B*_A = 1 + floor((D+1-2*mu)/r), mu = least t>=0 with Gamma_t>=Gamma_{t+1}>=...>=Gamma_{r-1}.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import gamma
def domain(r, a):
    if any(x % r == 0 for x in a): return True
    G = gamma(r, sorted(a))
    return max(abs(G[i]-G[(i+1) % r]) for i in range(r)) <= 1
def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    G = gamma(r, sorted(a)); D = sum(x-1 for x in a)
    mu = r-1
    while mu > 0 and G[mu-1] >= G[mu]: mu -= 1
    return b <= 1 + (D + 1 - 2*mu)//r
