from brute import indep_poly_subsets, indep_poly_backtrack
import sympy as sp, mpmath as mp, subprocess
x = sp.symbols('x')
mp.mp.dps = 40
def pari_sturm(c):
    p = '+'.join(f'({a})*x^{i}' for i, a in enumerate(c))
    out = subprocess.run(['gp','-q'], input=f'P={p};print(poldegree(P)," ",polsturm(P)," ",issquarefree(P)," ",poldisc(P))\n', capture_output=True, text=True).stdout
    return out.strip()
for (n,k) in [(3,1),(7,3),(7,2),(9,2),(9,4)]:
    c1 = indep_poly_subsets(n,k); c2 = indep_poly_backtrack(n,k)
    assert c1 == c2
    P = sp.Poly(list(reversed(c1)), x)
    nreal_sympy = P.count_roots()  # counts real roots (with multiplicity)
    rr = sorted(mp.polyroots(list(reversed(c1)), maxsteps=200, extraprec=200), key=lambda z: mp.re(z))
    print(n, k, c1, 'deg', P.degree(), 'sympy_real', nreal_sympy, 'pari(deg,sturm,sqfree,disc)', pari_sturm(c1))
    for r in rr: print('    ', mp.nstr(r, 10))
