# Exact rule (proved, see proof_S2_partial.txt, Lemma 4 + Corollary 7): thread / parity-split criterion.
# predict(r,a,b) -> bool : is prod [a_i]_q * [b]_{q^r} weakly unimodal?
# No free parameters.  Domain: all r>=2, a_i>=1, b>=1.
def _poly(a):
    c=[1]
    for A in a:
        n=len(c)+A-1; d=[0]*n; s=0
        for t in range(n):
            if t<len(c): s+=c[t]
            if 0<=t-A<len(c): s-=c[t-A]
            d[t]=s
        c=d
    return c
def domain(r,a):
    return True
def predict(r,a,b):
    a=sorted(a); A=_poly(a); D=len(A)-1
    F=sum(x//r for x in a)
    def delta(j):
        return (A[j] if 0<=j<=D else 0)-(A[j-1] if 0<=j-1<=D else 0)
    top=D//2                       # largest integer < c0=(D+1)/2
    seen=set()
    for rho in range(r):
        sig=(D+1-rho)%r
        if sig==rho: continue      # fixed class: always fine
        key=(min(rho,sig),max(rho,sig))
        if key in seen: continue
        seen.add(key)
        # thread positions y_0>y_1>... (integers < c0 congruent to rho or sig), need d_0..d_b
        d=[]; y=top
        while len(d)<b+1:
            if y%r in key: d.append(delta(y))
            y-=1
        # V_m = sum_{i<m} (-1)^{m-1-i} d_i
        V=[0]*(b+1)
        for m in range(1,b+1): V[m]=d[m-1]-V[m-1]
        if (b-F)%2==0:             # off parity: condition V_b>=0 (outer automatic, Lemma 6)
            if V[b]<0: return False
        else:                      # main parity: condition V_{b-1}+d_b>=0 (inner automatic, Lemma 6)
            if V[b-1]+d[b]<0: return False
    return True
