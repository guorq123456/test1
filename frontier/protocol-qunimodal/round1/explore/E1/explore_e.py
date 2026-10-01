# Explore e = p/Phi_3 (power series) for p=prod [a_i], a_i nondiv by 3; check identities and Claim C.
import sys
from common import *
def eseq(p,M):
    e=[0]*(M+1)
    for m in range(M+1):
        pm=p[m] if m<len(p) else 0
        e[m]=pm-(e[m-1] if m>=1 else 0)-(e[m-2] if m>=2 else 0)
    return e
def delta_fn(S):
    s=S%6; sig=1 if s%2==0 else -1; eps=(2*s)%3
    def dl(m):
        r=m%3
        if r==eps: return sig
        if r==(eps+1)%3: return -sig
        return 0
    return dl
if __name__=="__main__":
    bad_ident=0; bad_nonneg=[]; cnt=0
    for a in box_instances():
        if min(a)<2: continue
        p=[int(x) for x in pprod(a)]; D=len(p)-1; S=sum(1 for x in a if x%3==2)
        e=eseq(p,D+10); dl=delta_fn(S)
        cnt+=1
        # identity e_m - e_{D-2-m} = delta(m) for all m in [-3, D+8]
        E=lambda m: e[m] if m>=0 else 0
        for m in range(-3,D+8):
            if E(m)-E(D-2-m)!=dl(m): bad_ident+=1
        # nonnegativity on [0,D-2]
        neg=[m for m in range(0,D-1) if e[m]<0]
        if neg: bad_nonneg.append((a,neg))
    print("polys",cnt,"identity failures",bad_ident)
    print("polys with negative e on [0,D-2]:",len(bad_nonneg))
    for x in bad_nonneg[:20]: print(x)
