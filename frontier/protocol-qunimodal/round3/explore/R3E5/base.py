# Base family rho=(m1,m2,m3,(r-1)^n). Exact window test (R2E5 Lemma 6) using low coefficients only.
def series_A(ms, n, r, J):
    # coefficients 0..J of prod [m]_q * [r-1]_q^n
    c=[0]*(J+1); c[0]=1
    for A in list(ms)+[r-1]*n:
        d=[0]*(J+1); s=0
        for t in range(J+1):
            s+=c[t]
            if t-A>=0: s-=c[t-A]
            d[t]=s
        c=d
    return c
def tau_of(ms,n,r):
    # residue sums of (1-q)A mod q^r-1 ; (1-q)A == (1-q)R3 (-q^{-1})^n
    R=[1]
    for A in ms:
        d=[0]*(len(R)+A-1)
        for i,v in enumerate(R):
            for j in range(A): d[i+j]+=v
        R=d
    t3=[0]*r
    for j in range(len(R)+1):
        v=(R[j] if j<len(R) else 0)-(R[j-1] if j>=1 else 0)
        t3[j%r]+=v
    sg=(-1)**n
    return [sg*t3[(t+n)%r] for t in range(r)]
def params(ms,n,r):
    M3=sum(ms)-3; D=M3+n*(r-2)
    tau=tau_of(ms,n,r)
    mu=0
    for j in range(1,r):
        if tau[j]>0: mu=j
    T6=1+(D+1-2*mu)//r
    s=(D+1)%r
    fire= tau[s]<=-2 and s>=2*mu
    return D,tau,mu,T6,s,fire,T6-2*fire
def window(ms,n,r,b,J=None):
    D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
    K=D+1-r*(b+1)
    lo=-(-(K-2*r)//2)  # ceil((K-2r)/2) : m >= K/2 - r
    ms_=[m for m in range(lo, lo+r+2) if 2*m<K and 2*m>=K-2*r]
    assert len(ms_)==r
    top=max(K-m for m in ms_)
    if J is None: J=max(top,0)+1
    A=series_A(ms,n,r,J)
    delta=[A[j]-(A[j-1] if j>0 else 0) for j in range(J+1)]
    g=[0]*(J+1)
    for j in range(J+1): g[j]=delta[j]+(g[j-r] if j>=r else 0)
    G=lambda j: 0 if j<0 else g[j]
    out=[]
    for m in ms_:
        out.append((tau[m%r]+G(K-m)-G(m), m, K-m, tau[m%r]))
    return out
def ok(ms,n,r,b):
    return all(x[0]>=0 for x in window(ms,n,r,b))
