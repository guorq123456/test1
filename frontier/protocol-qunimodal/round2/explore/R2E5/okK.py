# OK(K) for flat condition as function of K (independent of e); prints the set of non-OK K in [-3r, Kmax]
import sys
from flat import tau_of, cser
def okK(r,s,k,K,tau,c):
    cc=lambda j: c[j] if j>=0 else 0
    m0=(K-1)//2
    return all(tau[m%r]+cc(K-m)-cc(m)>=0 for m in range(m0,m0-r,-1))
def badK(r,s,k,Kmax=None):
    tau=tau_of(r,s,k)
    if Kmax is None: Kmax=k*(s-1)+1
    c=cser(r,k,Kmax+4*r+10)
    return [K for K in range(-3*r,Kmax+1) if not okK(r,s,k,K,tau,c)]
if __name__=='__main__':
    r,s=map(int,sys.argv[1:3])
    for k in range(3,61):
        B=badK(r,s,k)
        print(k, 'maxbadK',max(B), 'bad>=0:',[x for x in B if x>=-r])
