# Rule R3E7-STAB (0 free parameters).
# domain(r,a): r divides no a_i, all a_i>=2, and the zero pattern Z(a) = {a_i : a_i < r} passes the hybrid test H.
# predict(r,a,b): b <= F+1 or (b-F) in U_inf(r, residues).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Res
from functools import lru_cache

@lru_cache(maxsize=4096)
def _res(r, s):
    return Res(r, list(s))

def _H(R, Z):
    gf = R.gfun(sorted(Z))
    return all(R.Rk(e, gf) for e in R.Uinf if e >= 2)

def domain(r, a):
    if any(x % r == 0 for x in a) or min(a) < 2: return False
    R = _res(r, tuple(sorted(x % r for x in a)))
    Z = [x for x in a if x < r]
    return _H(R, Z)

def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    R = _res(r, tuple(sorted(x % r for x in a)))
    F = sum(x // r for x in a)
    return b <= F + 1 or (b - F) in R.Uinf
