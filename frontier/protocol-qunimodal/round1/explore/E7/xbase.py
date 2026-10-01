# For base tuples (2<=a_i<r), print X (first descent of L = first neg coef of G=p/[r] minus 1), D, and G coefficients
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import X_of, pcoef
import itertools, collections
def G(r,a,n):
    p=pcoef(a); g=[0]*(n+1)
    # g = p*(1-q)/(1-q^r)
    pq=[0]*(n+2)
    for i,v in enumerate(p):
        if i<=n: pq[i]+=v
        if i+1<=n: pq[i+1]-=v
    for i in range(n+1):
        g[i]=pq[i]+(g[i-r] if i>=r else 0)
    return g
for r in [3,4]:
    vals=list(range(2,r))
    for k in range(1,9):
        for a in itertools.combinations_with_replacement(vals,k):
            X,D,L=X_of(r,a)
            g=G(r,a,D+2*r)
            print(r,a,"D=",D,"X=",X,"X-D=",X-D,"2X+1-D=",2*X+1-D, "g=",g[max(0,X-4):X+3])
