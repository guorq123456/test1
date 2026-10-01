# RULE W ("window criterion"), uniform in r.
# Gamma_s = residue-class counts of A=prod[a_i]_q mod r; f_j=[q^j](1-q)A(q), j<r.
# e(y) = Gamma_{y mod r}            for y < r
#      = Gamma_{y-r} - f_{y-r}      for r <= y < 2r
# M = D+1-r(b-1), D=sum(a_i-1).
# P unimodal  <=>  e(x) >= e(M-x) for every integer x with M-2r < x < M/2.
# (If some r | a_i: True, Cor. 4.3 of arXiv:2605.12822.)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import gamma, low_f
def domain(r, a):
    return True
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a):
        return True
    G = gamma(r, a); f = low_f(r, a, r)
    D = sum(x-1 for x in a); M = D + 1 - r*(b-1)
    def e(y):
        return G[y % r] - (f[y-r] if y >= r else 0)
    x = M - 2*r + 1
    while 2*x < M:
        if e(x) < e(M-x):
            return False
        x += 1
    return True
