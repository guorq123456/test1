# For given (r,a), list for each b in [1,T6] the failing indices i (g_i < g_{i-rb}) relative to N/2, D.
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
def fails(r,a,b):
    D,F,Gam,mu,T6=stats(r,a); N=D+r*(b-1)
    g=gseq(a,r,N//2+2); rb=r*b
    return [(i, g[i], g[i-rb] if i>=rb else 0) for i in range(1,N//2+1) if g[i] < (g[i-rb] if i>=rb else 0)]
if __name__=='__main__':
    r=int(sys.argv[1]); a=sorted(map(int,sys.argv[2].split(',')))
    D,F,Gam,mu,T6=stats(r,a)
    print("D",D,"F",F,"mu",mu,"T6",T6,"Gam diffs tau",[Gam[t]-Gam[t-1] for t in range(r)])
    g=gseq(a,r,D+3*r); print("g",g)
    for b in range(1,T6+2):
        N=D+r*(b-1); f=fails(r,a,b); print(b,"N/2",N/2,"rb",r*b, f[:6])
