# Exact real-valued chain thresholds X_exact (odd/even) from the exact window criterion, for comparison with
# the closed-form X of rule_asym.py.  nu_exact = Delta_e/2 - margin(Delta_e)/lambda at the exact chain top e,
# margin(Delta) = min over window m with tau_m>0 of ln(w_m - w_{Delta-m}) - ln(tau_m).
import math, gmpy2
from uinf import tau_of, Wn, window, uinf
from rule_asym import asym_tops, _Hinv, modes
def lnz(x): return float(gmpy2.log(gmpy2.mpfr(x,200)))
def margin(r,k,tau,D):
    best=None
    for m in window(D,r):
        t=tau[m%r]
        if t<=0: continue
        d=Wn(m,r,k)-Wn(D-m,r,k)
        if d<=0: return -1e300
        v=lnz(d)-lnz(t)
        if best is None or v<best: best=v
    return best
def xexact(r,s):
    k=len(s); S1=sum(x-1 for x in s); K0=S1+1
    tau=tau_of(r,s); ex=uinf(r,s)
    Lk=max(v for v,j,sg in modes(r,s)); theta=_Hinv(Lk/k); lam=math.log(1+1/theta)
    out={}
    for par,e in ((1,ex['e_odd']),(0,ex['e_even'])):
        if e<2: e=e+2  # chain top not >=2: use first element above (margin<0)
        D=K0-r*(e+1)
        mg=margin(r,k,tau,D)
        nu=D/2-mg/lam
        out[par]=(K0-r-2*nu)/r
    return out[1],out[0],ex
if __name__=='__main__':
    import sys
    r=int(sys.argv[1]); kmax=int(sys.argv[2]); block=list(map(int,sys.argv[3:]))
    p=len(block)
    for m in range(1,kmax//p+1):
        s=block*m; k=len(s)
        if k<3: continue
        Xo,Xe,ex=xexact(r,s); Ao,Ae,eo,ee=asym_tops(r,s)
        print(k, ex['e_odd'], round(Xo,4), round(Ao,4), 'dOdd %.5f'%(Ao-Xo), ex['e_even'], round(Xe,4), round(Ae,4), 'dEven %.5f'%(Ae-Xe), 'k*dOdd %.3f'%(k*(Ao-Xo)))
