# Machine checks of every algebraic identity / numeric constant used in proof.md.
from fractions import Fraction as F
import sympy as sp
from mpmath import mp, mpf, log, harmonic, euler, sqrt

k, t, s, x = sp.symbols('k t s x', positive=True)
phi = lambda X: 1/(24*X**2)
psi = lambda X: 1/(24*X**2) - 1/(120*X**4)
sub = {k: 1/(2*t)}
# (L1) phi(k-1/2)-phi(k+1/2) = (2/3) t^3/(1-t^2)^2
d1 = (phi(k-sp.Rational(1,2)) - phi(k+sp.Rational(1,2))).subs(sub)
assert sp.simplify(d1 - sp.Rational(2,3)*t**3/(1-t**2)**2) == 0
# (L2) 1/(k-1/2)^4 - 1/(k+1/2)^4 = 128 t^5 (1+t^2)/(1-t^2)^4
d4 = (1/(k-sp.Rational(1,2))**4 - 1/(k+sp.Rational(1,2))**4).subs(sub)
assert sp.simplify(d4 - 128*t**5*(1+t**2)/(1-t**2)**4) == 0
# (L3) psi-difference
d2 = (psi(k-sp.Rational(1,2)) - psi(k+sp.Rational(1,2))).subs(sub)
assert sp.simplify(d2 - (sp.Rational(2,3)*t**3/(1-t**2)**2 - sp.Rational(16,15)*t**5*(1+t**2)/(1-t**2)**4)) == 0
# (L4) 15(1-s)^4 * [ (2/3)+(2/5)s - (2/3)/(1-s)^2 + (16/15) s(1+s)/(1-s)^4 ] = 2s+42s^2-4s^3-14s^4+6s^5
P = sp.expand(sp.simplify(15*(1-s)**4*(sp.Rational(2,3)+sp.Rational(2,5)*s - sp.Rational(2,3)/(1-s)**2
                                        + sp.Rational(16,15)*s*(1+s)/(1-s)**4)))
assert sp.expand(P - (2*s+42*s**2-4*s**3-14*s**4+6*s**5)) == 0
# P > 0 on (0,1/4]: real roots of P/s
print("real roots of P(s)/s:", [r for r in sp.Poly(sp.cancel(P/s), s).nroots() if abs(sp.im(r)) < 1e-30])
assert sp.Poly(sp.cancel(P/s), s).count_roots(0, sp.Rational(1,4)) == 0 and P.subs(s, sp.Rational(1,8)) > 0
# Series of g: g = ln((1+t)/(1-t)) - 2t = 2 sum_{j>=1} t^{2j+1}/(2j+1)
gser = sp.series(sp.log((1+t)/(1-t)) - 2*t, t, 0, 12).removeO()
assert sp.expand(gser - sum(sp.Rational(2, 2*j+1)*t**(2*j+1) for j in range(1, 6))) == 0
print("symbolic identities (L1)-(L4) and series of g: OK")

# (C1) constants in the main estimate
c = F(4,605) + F(2,81) + F(8712,9789)
print("4/605 + 2/81 + 8712/9789 =", c, "=", float(c)); assert c < 1
assert F(72,1)/(81 - F(12,121)) == F(8712,9789)
assert F(110,24) < F(11,2)

# (C2) b_n facts, exact rationals, n up to 2000
b = [F(1,2), F(11,2)]
while len(b) < 2001: b.append(10*b[-1]-b[-2])
assert all(b[n-1]**2 - b[n]*b[n-2] == 3 for n in range(2, 2001))
rho = [None] + [b[n]/b[n-1] for n in range(1, 2001)]
assert rho[1] == 11 and all(9 < rho[n] <= 11 for n in range(1, 2001)) and all(rho[n] < 10 for n in range(2, 2001))
assert all(rho[n] > rho[n+1] for n in range(1, 2000))
print("b_n invariant and ratio bounds: OK (n <= 2000)")

# (N1) numeric sanity check of Lemma 1:  psi(m+1/2) < D(m) < phi(m+1/2),  D(m) = H(m) - gamma - ln(m+1/2)
mp.dps = 60
worst_lo, worst_hi = mpf(10), mpf(10)
H = mpf(0)
for m in range(0, 20001):
    if m: H += mpf(1)/m
    B = mpf(m) + mpf(1)/2
    D = H - euler - log(B)
    lo = 1/(24*B**2) - 1/(120*B**4); hi = 1/(24*B**2)
    assert lo < D < hi, m
    worst_lo = min(worst_lo, (D-lo)*B**4); worst_hi = min(worst_hi, (hi-D)*B**4)
for m in [10**6, 10**9, 10**15, 10**30]:
    mp.dps = 4*len(str(m)) + 60
    B = mpf(m) + mpf(1)/2; D = harmonic(m) - euler - log(B)
    assert 1/(24*B**2) - 1/(120*B**4) < D < 1/(24*B**2)
print("Lemma 1 numerically confirmed for m=0..20000 and m=1e6,1e9,1e15,1e30;"
      " min (D-lower)*B^4 = %s, min (upper-D)*B^4 = %s" % (mp.nstr(worst_lo, 6), mp.nstr(worst_hi, 6)))
print("   (asymptotically D = 1/(24B^2) - 7/(960B^4) + ..., so these tend to 1/120-7/960=%s and 7/960=%s)"
      % (mp.nstr(mpf(1)/120 - mpf(7)/960, 6), mp.nstr(mpf(7)/960, 6)))

# (N2) hand check of the n=2 case with Lemma 1 (logs at 50 digits)
mp.dps = 50
lo54 = log(mpf(109)/11) - 1/(24*mpf(11/2)**2)   # H(54)-H(5) > ln(54.5/5.5) + 0 - D(5)
hi53 = log(mpf(107)/11) + 1/(24*mpf(107/2)**2)  # H(53)-H(5) < ln(53.5/5.5) + D(53) - 0
print("H(54)-H(5) >", mp.nstr(lo54, 12), " ; H(5) = 137/60 =", mp.nstr(mpf(137)/60, 12), " ; H(53)-H(5) <", mp.nstr(hi53, 12))
assert hi53 < mpf(137)/60 < lo54
mp.dps = 30
print("ln(5+2sqrt6) =", log(5+2*sqrt(6)), "; 5+2sqrt6 =", 5+2*sqrt(6))
print("ALL CHECKS PASSED")
