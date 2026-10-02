# Compute exact E(k) along a family: residues = block repeated m times, k=m*len(block).
import sys, math, json
from uinf import uinf
import mpmath as mp
def theory(r, block):
    p=len(block)
    sigma1=sum(s-1 for s in block)/p
    best=None
    for j in range(1,r):
        v=0.0; zero=False
        for s in block:
            x=abs(math.sin(math.pi*j*s/r)/math.sin(math.pi*j/r))
            if x<1e-12: zero=True;break
            v+=math.log(x)
        if zero: continue
        v/=p
        if best is None or v>best[0]: best=(v,j)
    L,j=best
    H=lambda t: (1+t)*mp.log(1+t)-t*mp.log(t) if t>0 else mp.mpf(0)
    th=mp.findroot(lambda t: H(t)-L, (1e-9, 1e6), solver='bisect') if L>0 else 0
    th=float(th); lam=math.log(1+1/th)
    c=(sigma1-2*th)/r; kappa=1/(r*lam)
    return dict(sigma1=sigma1,L=L,jstar=j,theta=th,lam=lam,c=c,kappa=kappa)
if __name__=='__main__':
    r=int(sys.argv[1]); kmax=int(sys.argv[2]); block=list(map(int,sys.argv[3:]))
    th=theory(r,block); print(json.dumps(th))
    p=len(block)
    for m in range(1,kmax//p+1):
        k=m*p
        if k<2: continue
        res=uinf(r,block*m)
        pred=th['c']*k-th['kappa']*math.log(k)
        print(k,res['E'],res['e_odd'],res['e_even'],res['T'],round(res['E']-pred,3))
