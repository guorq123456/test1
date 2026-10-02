# Rule H1 (candidate): domain = r>=4, r divides no a_i, exactly three a_i with residue in [2,r-2].
# B* = T6 - 2 if tau_s <= -2 and s >= 2 mu else T6, where s=(D+1) mod r, tau_t = Gamma_t - Gamma_{t-1};
# predict: b <= B*.
def _tau(r,a):
    # tau = (1-q) prod [rho_i]_q  mod (q^r-1)
    c=[0]*r; c[0]=1; c[1%r]-=1
    for x in a:
        rho=x%r
        n=[0]*r
        for i,v in enumerate(c):
            if v:
                for j in range(rho): n[(i+j)%r]+=v
        c=n
    return c
def bstar(r,a):
    D=sum(x-1 for x in a); F=sum(x//r for x in a)
    tau=_tau(r,a)
    pos=[j for j in range(1,r) if tau[j]>0]
    mu=max(pos) if pos else 0
    T6=1+(D+1-2*mu)//r
    s=(D+1)%r
    return T6-2 if (tau[s]<=-2 and s>=2*mu) else T6
def domain(r,a):
    return r>=4 and all(x%r for x in a) and sum(1 for x in a if 2<=x%r<=r-2)==3
def predict(r,a,b):
    return b<=bstar(r,a)
