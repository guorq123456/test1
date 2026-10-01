from itertools import product
def is_TL(d,k):
    e=d[2]
    if any(d[j]!=e for j in range(2,k+1)): return False
    return d[1]-d[0] <= e-d[1] <= 0
def is_BR(d,k):
    e=d[0]
    if any(d[j]!=e for j in range(0,k-1)): return False
    u=d[k-1]-e; v=d[k]-d[k-1]; return 0<=u<=v
for k in (2,3):
    words=list(product((0,1),repeat=k+1))
    for W in words:
        if len(set(W))==1: continue
        f=sum(1 for R in words if is_TL([W[j]-R[j] for j in range(k+1)],k))
        g=sum(1 for R in words if is_BR([R[j]-W[j] for j in range(k+1)],k))
        print(k,''.join(map(str,W)),f,g,f*g)
# n=1 weights: TL weights grouped by e
m=lambda d: 2 if d==0 else 1
from collections import Counter
c=Counter()
for t in product((-1,0,1),repeat=3):
    if t[1]-t[0]<=t[2]-t[1]<=0: c[t[2]]+=m(t[0])*m(t[1])
print('TL weights by e',dict(c))
c=Counter()
for t in product((-1,0,1),repeat=3):
    e,a,b=t
    if 0<=a-e<=b-a: c[e]+=m(a)*m(b)
print('BR weights by e',dict(c))
