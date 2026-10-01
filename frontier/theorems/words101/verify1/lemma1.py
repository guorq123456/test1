from math import comb
import sympy as sp
N=40
# DP grid W[i][j]
s0=[[0]*(N+1) for _ in range(N+1)]; s1=[[0]*(N+1) for _ in range(N+1)]; s2=[[0]*(N+1) for _ in range(N+1)]
s0[0][0]=1
for i in range(N+1):
    for j in range(N+1):
        if i==0 and j==0: continue
        if j>0:
            s0[i][j]+=s0[i][j-1]+s2[i][j-1]; s2[i][j]+=s1[i][j-1]
        if i>0:
            s1[i][j]+=s0[i-1][j]+s1[i-1][j]
W=lambda i,j: s0[i][j]+s1[i][j]+s2[i][j]
y=sp.symbols('y')
for n in range(1,N+1):
    ser=sp.series((1-y)**-2*(1/(1-y)-y)**(n-1),y,0,N+1).removeO()
    p=sp.Poly(ser,y)
    for m in range(N+1):
        assert p.coeff_monomial(y**m)==W(n,m),(n,m)
print("Lemma 1 W(n,m) ok n,m<=",N)
# symbolic checks
x=sp.symbols('x')
R=sp.sqrt((1+x)/(1-3*x))
print("Lemma6:",sp.simplify((1+x)*(1-3*x)*sp.diff(R,x)-2*R))
A=(1+x)*(R-1)/(2*x)
print("ODE:",sp.simplify(x*(1+x)*(1-3*x)*sp.diff(A,x)+(1-5*x)*A-(1+x)))
G=2*(1-x**2)/(3*x**2-4*x+1+sp.sqrt((1-x**2)**2-4*(x-x**2)*(1-x**2)))
print("G-A series:",sp.series(G-A,x,0,30))
B=1/sp.sqrt(1-4*x)
print("4.1:",sp.series(2*x**2*sum(comb(2*k+3,k+1)*x**k for k in range(40))-(B-1-2*x),x,0,40))
