# Second, independent verification with sympy polynomial expansion
from sympy import symbols, Poly, expand
q=symbols('q')
def qi(a,r=1): return sum(q**(r*i) for i in range(a))
def coeffs(expr): return Poly(expand(expr),q).all_coeffs()[::-1]
def unimodal(c):
    i=0;n=len(c)
    while i+1<n and c[i]<=c[i+1]: i+=1
    while i+1<n and c[i]>=c[i+1]: i+=1
    return i==n-1
cases=[(3,(2,)*6,2),(3,(2,)*6,3),(3,(2,)*5,2),(3,(2,)*6,4),(3,(2,2,2,2,2,5),3),(3,(5,)*6,8),(3,(5,)*6,9),(3,(5,)*6,10),(3,(2,)*12,5),(3,(2,)*12,6),(4,(3,3,3,3),2),(2,(3,3,3,3,3,3,3),9)]
for r,a,b in cases:
    expr=qi(b,r)
    for x in a: expr*=qi(x)
    c=coeffs(expr)
    F=sum(x//r for x in a); cond=any(x%r==0 for x in a) or b<=1+F
    print("r=%d a=%s b=%d  condition=%s  unimodal=%s  coeffs=%s"%(r,a,b,cond,unimodal(c),c if len(c)<=20 else str(c[:12])+'...'))
