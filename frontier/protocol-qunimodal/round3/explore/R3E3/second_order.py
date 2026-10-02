# Test candidate second-order inequalities for alpha = prod [a_i] (k' parts >=2):
#  (S1) D2(alpha)_x / alpha_x >= D2(binom)_x / binom_x  where D2 f_x = f_x - 2 f_{x-1} + f_{x-2}, binom = C(k',x)
#       for 2 <= x <= x where binomial D2>0
#  (S2) M(A) = (1+q)^2 A'' - 2(k'-1)(1+q)A' + k'(k'-1)A >= 0 coefficientwise
import random
from math import comb
from lib4 import polyA
random.seed(5); v1=0; v2=0; n=0; ex1=None; ex2=None
for it in range(3000):
    k=random.randint(2,25); a=[random.choice([2,2,3,3,4,5,6,7,9,13,20]) for _ in range(k)]
    c=polyA(a); D=len(c)-1; n+=1
    C=lambda x: comb(k,x) if 0<=x<=k else 0
    al=lambda x: c[x] if 0<=x<=D else 0
    for x in range(2,min(k,D//2)+1):
        db=C(x)-2*C(x-1)+C(x-2)
        if db<=0: break
        da=al(x)-2*al(x-1)+al(x-2)
        if da*C(x)<db*al(x): v1+=1; ex1=(a,x)
    # M(A)
    d1=[(j+1)*al(j+1) for j in range(D+1)]  # A'
    d2=[(j+2)*(j+1)*al(j+2) for j in range(D+1)]
    for j in range(D+1):
        t2=d2[j]+2*(d2[j-1] if j>=1 else 0)+(d2[j-2] if j>=2 else 0)
        t1=d1[j]+(d1[j-1] if j>=1 else 0)
        m=t2-2*(k-1)*t1+k*(k-1)*al(j)
        if m<0 and j<=D//2: v2+=1; ex2=(a,j,m); break
print(n,"S1 viol",v1,ex1,"S2 viol",v2,ex2)
