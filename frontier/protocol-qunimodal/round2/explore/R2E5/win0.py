# n=0: test whether the r-window criterion (r largest m<K/2) with g=[s]^k(1-q)/(1-q^r) equals full Thm A truth
import sys
from core import gseries, Uset_fast
from flat import tau_of
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a
def win_ok(r,s,k,b,g,tau):
    D=k*(s-1); K=D+1-r*(b+1)
    gg=lambda j: g[j] if j>=0 else 0
    m0=(K-1)//2
    return all(tau[m%r]+gg(K-m)-gg(m)>=0 for m in range(m0,m0-r,-1))
bad=0;tot=0
for r in range(4,int(sys.argv[1])+1):
    for s in range(2,r-1):
        for k in range(3,61):
            A=poly_a([s]*k); D=len(A)-1
            U,F,T6=Uset_fast(r,[s]*k)
            g=gseries(A,r,D+r*(T6+3)); tau=tau_of(r,s,k)
            W=[b for b in range(1,T6+3) if win_ok(r,s,k,b,g,tau)]
            tot+=1
            if W!=U: bad+=1; print('diff',r,s,k,U,W)
print('n=0 window-criterion checked',tot,'mismatch',bad)
