# Independent check of BCK Conj 1.1 for small m+n: exact full polynomial via
# numerator prod (1-q^{F_{m+k}}) then exact division by each (1-q^{F_k}), k=1..n.
import numpy as np, sys, time
from math import prod
F=[0,1,1]
while len(F)<60: F.append(F[-1]+F[-2])
def fibonomial(m,n):
    A=[F[m+k] for k in range(1,n+1)]; B=[F[k] for k in range(1,n+1)]
    Ntop=sum(A); c=np.zeros(Ntop+1,dtype=object); c[:]=0; c[0]=1
    d=0
    for a in A:  # multiply by (1-q^a)
        nc=c.copy(); nc[a:d+a+1]-=c[0:d+1]; c=nc; d+=a
    for b in B:  # exact divide by (1-q^b): quotient g with g_t = c_t + g_{t-b}
        L=((d+1+b-1)//b)*b
        arr=np.zeros(L,dtype=object); arr[:]=0; arr[:d+1]=c[:d+1]
        g=np.cumsum(arr.reshape(-1,b),axis=0).reshape(-1)
        # quotient has degree d-b; remainder must be zero => g[t]=0 for t>d-b
        assert all(x==0 for x in g[d-b+1:d+1]), ("not divisible",m,n,b)
        d-=b; c=np.zeros(Ntop+1,dtype=object); c[:]=0; c[:d+1]=g[:d+1]
    # now c = prod (1-q^A)/(1-q^B) = prod [A]_q/[B]_q since #A=#B
    return [int(x) for x in c[:d+1]]
def unimodal(v):
    i=0;n=len(v)
    while i+1<n and v[i]<=v[i+1]: i+=1
    while i+1<n and v[i]>=v[i+1]: i+=1
    return i>=n-1
maxs=int(sys.argv[1])
for s in range(2,maxs+1):
    t0=time.time(); bad=[]
    for n in range(1,s//2+1):
        m=s-n
        v=fibonomial(m,n)
        exact=prod(F[1:s+1])//(prod(F[1:m+1])*prod(F[1:n+1]))
        ok=(min(v)>=0 and v==v[::-1] and unimodal(v) and sum(v)==exact)
        if not ok: bad.append((m,n,min(v)>=0,v==v[::-1],unimodal(v),sum(v)==exact))
    print(s,"pairs",s//2,"bad",bad,"deg(m=n or max)",len(v)-1,"%.1fs"%(time.time()-t0),flush=True)
