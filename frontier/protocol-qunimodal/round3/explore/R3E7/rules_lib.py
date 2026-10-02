# candidate rules for sharp L0, computed from residue data only (r, s)
from core import *
def gZ(R, Z):
    """g for instance: parts in Z at value = residue, all other parts 'infinite' (absent from X)."""
    return R.gfun(sorted(Z))   # gfun skips parts > N; Z parts are residues < r
def H_exact(R, Z):
    gf = gZ(R, Z)
    return all(R.Rk(e, gf) for e in R.Uinf if e >= 2)
def H_first(R, Z):
    # first-order: g ~ w - sum_i w_{.-s_i}
    def gf(n):
        return R.wf(n) - sum(R.wf(n - x) for x in Z)
    return all(R.Rk(e, gf) for e in R.Uinf if e >= 2)
def L0_from(R, H):
    ts = sorted(set([2] + [x+1 for x in R.s if x+1 > 2]))
    for t in ts:
        Z = [x for x in R.s if x >= t]
        if H(R, Z): return t
    return max(R.s)+1
def L0_exact(R): return L0_from(R, H_exact)
def L0_first(R): return L0_from(R, H_first)
def L0_single(R):
    # t* = largest residue x such that single part x (others infinite) breaks a window; L0 = t*+1 (or 2)
    bad = [x for x in set(R.s) if not H_exact(R, [x])]
    return max([2] + [x+1 for x in bad])
def L0_sharp_true(R):
    top = max(2, R.L0_R2E7())
    Ls = sorted(set([2] + [x for x in range(2, top+1) if any((x-1-si) % R.r == 0 for si in set(R.s))]))
    for L in Ls:
        if R.stable(R.aL(L)): return L
    return top
