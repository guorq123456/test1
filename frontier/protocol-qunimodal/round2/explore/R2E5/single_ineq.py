# Candidates C2/C3/C4: single-inequality simplifications of the flat window criterion, compared with E_inf (r<=30,k<=60, e in 1..E6+2)
# C2: min_t tau_t + c_{K-M} - c_M >= 0           (sufficient)
# C3: Phi(m*) >= 0 for m* = window m with most negative tau_m (necessary)
# C4: Phi(m*) >= 0 for m* = largest window m with tau_m < 0
from rule_allequal_middle import _tau, _c
err={'C2':0,'C3':0,'C4':0}; tot=0
for r in range(4,31):
    for s in range(2,r-1):
        for k in range(3,61):
            tau=_tau(r,s,k); L=k*(s-1)//2+2*r+4; c=_c(r,k,L)
            H=lambda j: c[j] if j>=0 else 0
            for e in range(1,(k*(s-1)+1)//r+3):
                K=k*(s-1)+1-r*(2+e); M=(K-1)//2; W=list(range(M,M-r,-1))
                phi={m:tau[m%r]+H(K-m)-H(m) for m in W}
                truth=all(v>=0 for v in phi.values())
                c2=min(tau)+H(K-M)-H(M)>=0
                mstar=min(W,key=lambda m:tau[m%r]); c3=phi[mstar]>=0
                neg=[m for m in W if tau[m%r]<0]; c4=phi[max(neg)]>=0 if neg else True
                tot+=1
                err['C2']+=(c2!=truth); err['C3']+=(c3!=truth); err['C4']+=(c4!=truth)
print('(r,s,k,e) cases',tot,'errors',err)
