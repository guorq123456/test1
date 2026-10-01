from flint import arb, ctx, fmpq
from fractions import Fraction as F
import sympy as sp
ctx.prec = 400
g_ = arb.const_euler()
def H(k): return arb(0) if k==0 else arb(k+1).digamma()+g_
# Lemma 3.1 for k=1..20000 and sample large k
def phi(x): return 1/(24*x**2)
def psi(x): return 1/(24*x**2) - 1/(120*x**4)
bad=0
ks = list(range(1,20001)) + [10**6, 10**9, 10**15, 10**30, 10**60]
for k in ks:
    kk = arb(k); half=arb(1)/2
    g = ((kk+half)/(kk-half)).log() - 1/kk
    lo = psi(kk-half)-psi(kk+half); hi = phi(kk-half)-phi(kk+half)
    if not (g > lo and g < hi): bad+=1; print("L3.1 fail/undecided", k)
print("Lemma 3.1 checked on", len(ks), "values; failures", bad)
# Lemma 3.2: D(m) = H(m) - log(m+1/2) - gamma ; bounds
bad=0
ms = list(range(0,20001)) + [10**6, 10**9, 10**15, 10**30, 10**50]
for m in ms:
    b = arb(m)+arb(1)/2
    D = H(m) - b.log() - g_
    if not (D > 1/(24*b**2) - 1/(120*b**4) and D < 1/(24*b**2)): bad+=1; print("L3.2 fail", m, D)
print("Lemma 3.2 bounds checked on", len(ms), "values; failures", bad)
# D strictly decreasing small m
print("D decreasing m<=2000:", all((H(m)-(arb(m)+0.5).log()) > (H(m+1)-(arb(m+1)+0.5).log()) for m in range(2000)))
# Check sum_{k>m} g(k) = D(m) loosely for m=0 using partial sum + tail bound
m=0; s=arb(0)
for k in range(1,100001):
    kk=arb(k); s += ((kk+0.5)/(kk-0.5)).log()-1/kk
print("D(0)=", (H(0)-arb(0.5).log()-g_).str(10), " partial sum g(1..1e5)=", s.str(10), " tail<phi(1e5+.5)=", (1/(24*arb(100000.5)**2)).str(3))
# P(s) expansion
s_=sp.symbols('s')
P = sp.expand((10+6*s_)*(1-s_)**4 - 10*(1-s_)**2 + 16*s_*(1+s_))
print("P(s) =", P)
# check the reduction: (2/3 + 2/5 s) - [(2/3)/(1-s)^2 - (16/15) s (1+s)/(1-s)^4] = P/(15(1-s)^4)
expr = sp.simplify((sp.Rational(2,3)+sp.Rational(2,5)*s_) - (sp.Rational(2,3)/(1-s_)**2 - sp.Rational(16,15)*s_*(1+s_)/(1-s_)**4) - P/(15*(1-s_)**4))
print("reduction identity residual:", expr)
print("min P(s)/s on (0,1/4]:", min(float((P/s_).subs(s_, sp.Rational(i,4000))) for i in range(1,1001)))
t,k=sp.symbols('t k', positive=True)
print("phi diff identity:", sp.simplify((1/(24*(k-sp.Rational(1,2))**2) - 1/(24*(k+sp.Rational(1,2))**2)) - (sp.Rational(2,3)*t**3/(1-t**2)**2)).subs(k,1/(2*t)).simplify())
print("4th power identity:", sp.simplify((1/(k-sp.Rational(1,2))**4 - 1/(k+sp.Rational(1,2))**4).subs(k,1/(2*t)) - 128*t**5*(1+t**2)/(1-t**2)**4))
# constants of section 4
c = F(4,605)+F(2,81)+F(8712,9789)
print("1 - (4/605+2/81+8712/9789) =", 1-c, float(1-c), " claimed 1-147315962/159903315 =", F(1)-F(147315962,159903315), (1-c)==F(1)-F(147315962,159903315))
print("72/(81-12/121) =", F(72)/(F(81)-F(12,121)))
print("110/24 =", 110/24, "<= 11/2")
# exact n=2 case
H54 = sum(F(1,j) for j in range(1,55)); H53 = H54 - F(1,54)
T2 = 2*sum(F(1,j) for j in range(1,6))
print("T2 =", T2)
print("H54-T2 =", H54-T2, H54-T2 == F(479812184179176959849,54749786241679275146400))
print("T2-H53 =", T2-H53, T2-H53 == F(1602218238666873295253,164249358725037825439200))
import math
print("hand: log(109/11)-1/726 =", math.log(109/11)-1/726, " H5 =", 137/60, " log(107/11)+1/(24*53.5^2)=", math.log(107/11)+1/(24*53.5**2))
