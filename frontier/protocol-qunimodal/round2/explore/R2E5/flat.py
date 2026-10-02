# Flat-regime (n -> infinity) reduction for the all-equal family a = n r + s.
# b = kn+1+e (e>=1) in U_inf  iff  for all integers m < K/2 : tau[m mod r] + c(K-m) >= c(m)
# where K = k(s-1)+1-r(2+e), c(j) = [q^j] 1/((1-q)^(k-1)(1-q^r)) (0 for j<0),
# tau = periodic tail of [s]_q^k (1-q)/(1-q^r): tau_t = Gamma_t - Gamma_{t-1}, Gamma_t = residue sums of [s]^k.
from math import comb
from functools import lru_cache
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a

def tau_of(r,s,k):
    S=poly_a([s]*k)
    G=[0]*r
    for j,v in enumerate(S): G[j%r]+=v
    return [G[t]-G[t-1] for t in range(r)]

def cser(r,k,L):
    # c_j for j=0..L : 1/((1-q)^(k-1)(1-q^r))
    c=[0]*(L+1)
    for j in range(L+1):
        v=comb(j+k-2,k-2)
        if j>=r: v+=c[j-r]
        c[j]=v
    return c

def flat_ok(r,s,k,e,tau=None):
    if tau is None: tau=tau_of(r,s,k)
    K=k*(s-1)+1-r*(2+e)
    T=max(abs(x) for x in tau)
    # m from K/2 downwards to where c(K-m) > T surely and c(m)=0
    mhi=(K-1)//2 if K>=1 else (K//2 if K%2==1 else K//2-1)
    # m < K/2 : largest integer m with 2m<K
    mhi=(K-1)//2
    L=max(0,K)+10*r+50
    c=cser(r,k,L+5*r+1000)
    def cc(j): return c[j] if j>=0 else 0
    m=mhi
    while True:
        if tau[m%r]+cc(K-m) < cc(m): return False
        if m<0 and cc(K-m)>T: break
        m-=1
        if K-m>=len(c): break
    return True

def flat_U(r,s,k,emax=None):
    tau=tau_of(r,s,k)
    if emax is None: emax=(k*(s-1))//r+2
    return [e for e in range(1,emax+1) if flat_ok(r,s,k,e,tau)]
if __name__=='__main__':
    r,s,k=map(int,sys.argv[1:4])
    print(flat_U(r,s,k))

def cvals(r,k,L):
    return cser(r,k,max(L,0))

def window_ok(tau,gfun,K,r):
    m0=(K-1)//2
    return all(tau[m%r]+gfun(K-m)-gfun(m)>=0 for m in range(m0,m0-r,-1))

def flat_fast(r,s,k,emax=None):
    """E_inf via the r-window lemma (only the r largest m<K/2 matter)."""
    tau=tau_of(r,s,k)
    if emax is None: emax=(k*(s-1))//r+2
    Kmax=k*(s-1)+1-3*r
    c=cser(r,k,max(Kmax,0)+2*r+5)
    cc=lambda j: c[j] if j>=0 else 0
    out=[]
    for e in range(1,emax+1):
        K=k*(s-1)+1-r*(2+e)
        if window_ok(tau,cc,K,r): out.append(e)
    return out
