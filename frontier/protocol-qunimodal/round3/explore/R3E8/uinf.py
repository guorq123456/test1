# Exact U_inf(r, residues) via R2E7 Theorems 3,5 (window criterion R_k(Delta)).
# residues s_i in [1,r-1]; k=len(s) >= 2.  Returns dict with T, e_odd, e_even, Uinf (sorted list), E=max(Uinf)-1.
import gmpy2
from gmpy2 import mpz
def tau_of(r, s):
    # (1-q) prod [s_i]_q mod q^r-1
    v=[mpz(0)]*r; v[0]=mpz(1)
    for si in s:
        # multiply by [si]_q mod q^r-1 : new_t = sum_{j<si} v_{t-j}
        pre=[mpz(0)]*(2*r+1)
        ext=v+v
        for i in range(2*r): pre[i+1]=pre[i]+ext[i]
        nv=[mpz(0)]*r
        for t in range(r):
            # indices t, t-1, ..., t-si+1 mod r -> in ext use t+r-si+1 .. t+r
            nv[t]=pre[t+r+1]-pre[t+r-si+1]
        v=nv
    return [v[t]-v[(t-1)%r] for t in range(r)]
def Wn(n, r, k):
    # w_n = sum_{j>=0} C(n-jr+k-2, k-2), n>=0 ; 0 for n<0
    if n<0: return mpz(0)
    tot=mpz(0)
    while n>=0:
        tot+=gmpy2.comb(n+k-2,k-2); n-=r
    return tot
def floordiv2(x): return x//2
def window(D, r):
    # integers m with D/2 < m <= D/2 + r
    lo=D//2+1   # smallest m with 2m > D
    return list(range(lo, lo+r))
def chain_top(r, k, K0, tau, par, T):
    # largest e (>=2, e%2==par) with R_k(Delta_e); walk down from top; uses incremental w.
    e=T if T%2==par else T-1
    if e<2: return None
    D=K0-r*(e+1)
    ms=window(D,r)
    wm=[Wn(m,r,k) for m in ms]
    wy=[Wn(D-m,r,k) for m in ms]
    while e>=2:
        ok=all(wm[i]-wy[i]>=tau[ms[i]%r] for i in range(r))
        if ok: return e
        # e -> e-2 : D -> D+2r, m -> m+r, y=D-m -> y+r
        e-=2; D+=2*r
        ms=[m+r for m in ms]
        for i in range(r):
            m=ms[i]; y=D-m
            if m+k-2>=k-2 and m>=0: wm[i]=wm[i]+gmpy2.comb(m+k-2,k-2)
            if y>=0: wy[i]=wy[i]+gmpy2.comb(y+k-2,k-2)
    return None
def uinf(r, s):
    s=list(s); k=len(s); assert k>=2 and all(1<=x<=r-1 for x in s)
    S=sum(s); K0=S-k+1
    tau=tau_of(r,s)
    mu=max([t for t in range(r) if tau[t]>0], default=0)
    T=1+(K0-2*mu)//r
    eo=chain_top(r,k,K0,tau,1,T); ee=chain_top(r,k,K0,tau,0,T)
    if eo is None: eo=1
    if ee is None: ee=0
    U=sorted(set([e for e in range(1,eo+1,2)]+[e for e in range(2,ee+1,2)]))
    return dict(T=T,e_odd=eo,e_even=ee,Uinf=U,E=max(U)-1,mu=mu,S1=K0-1)
if __name__=='__main__':
    import sys
    r=int(sys.argv[1]); s=list(map(int,sys.argv[2:]))
    print(uinf(r,s))
