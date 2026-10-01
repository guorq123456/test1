from flint import arb, ctx
from fractions import Fraction as F
import math
e=[0,5]
while len(e)<3100: e.append(10*e[-1]-e[-2]+4)
b=[F(2*x+1,2) for x in e]
# Lemma 2.1 and 2.2 exactly
assert all(b[n-1]**2 - b[n]*b[n-2] == 3 for n in range(2,3100))
rho=[None]+[b[n]/b[n-1] for n in range(1,3100)]
assert rho[1]==11 and all(9<rho[n]<10 for n in range(2,3100))
assert all(rho[n+1]<rho[n] for n in range(1,3099))
print("Lemma 2.1/2.2 exact OK n<3100; rho decreasing OK")
# Section 4 chain for n = 3..300: check each displayed inequality on actual values
ctx.prec = 64
g_=None
bad=0
for n in range(3,301):
    ctx.prec = 2*e[n].bit_length()+200
    g_=arb.const_euler()
    H=lambda k: arb(0) if k==0 else arb(k+1).digamma()+g_
    u=arb(e[n-2])+arb(1)/2; v=arb(e[n-1])+arb(1)/2; w=arb(e[n])+arb(1)/2
    T=2*H(e[n-1])-H(e[n-2])
    right = H(e[n])-T
    D=lambda m: H(m)-(arb(m)+arb(1)/2).log()-g_
    # (4.1)
    r41 = (1-3/v**2).log()+D(e[n])+D(e[n-2])-2*D(e[n-1])
    ok = abs(right-r41) < arb(2)**(-ctx.prec+120)
    lb = 1/(24*u**2)-1/(120*u**4)-1/(12*v**2)-3/(v**2-3)
    ok &= bool(right > lb) and bool(lb > 0)
    rho_=v/u
    lb2 = 1 - 1/(5*u**2) - 2/rho_**2 - 72/(rho_**2-3/u**2)
    ok &= bool(abs(lb2 - 24*u**2*lb) < arb(2)**(-ctx.prec+150)) and bool(lb2 > arb(12587353)/159903315)
    left = T - (H(e[n])-arb(1)/e[n])
    ok &= bool(left > 1/arb(e[n]) - 1/(24*u**2)) and bool(1/arb(e[n]) - 1/(24*u**2) > 0)
    if not ok: bad+=1; print("chain issue at n",n)
    if n in (3,4,5,10,50,300):
        print(n, "H(e_n)-T_n*v^2 =", (right*v**2).str(8), " (T_n-H(e_n-1))*e_n =", (left*e[n]).str(8), " lb2=", lb2.str(6))
print("Section 4 chain verified n=3..300; issues:", bad)
# corollaries
a = lambda n: e[n+1]
assert all(a(n)==11*a(n-1)-11*a(n-2)+a(n-3) for n in range(4,3000))
import sympy as sp
x=sp.symbols('x')
ser = sp.series((54-55*x+5*x**2)/(1-11*x+11*x**2-x**3),x,0,40).removeO()
assert all(ser.coeff(x,i)==a(i+1) for i in range(40))
ser2 = sp.series(x*(54-55*x+5*x**2)/((1-x)*(1-10*x+x**2)),x,0,41).removeO()
assert all(ser2.coeff(x,i)==a(i) for i in range(1,41)) and ser2.coeff(x,0)==0
ctx.prec=10000
s6=arb(6).sqrt()
for n in list(range(1,200))+[1000,2000]:
    val = ((2+s6)*(5+2*s6)**(n+1)+(2-s6)*(5-2*s6)**(n+1)-4)/8
    assert abs(val-a(n)) < 0.01, n
r=5+2*s6
ratios=[F(a(n),a(n-1)) for n in range(2,2000)]
assert all(ratios[i+1]<ratios[i] for i in range(len(ratios)-1)) and all(q> F(98989794855663561963,10**19) for q in ratios)
print("ratio decreasing; first ratios", [float(q) for q in ratios[:4]], "r=", r.str(25))
print("log r =", r.log().str(30))
ctx.prec=2000
g_=arb.const_euler()
H=lambda k: arb(k+1).digamma()+g_
print("H(a(n))-H(a(n-1)) n=2..6:", [ (H(a(n))-H(a(n-1))).str(12) for n in range(2,7)], " n=200:", (H(a(200))-H(a(199))).str(25))
print("corollaries OK")
