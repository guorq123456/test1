# Prediction from condition (i) alone: residues-only.
# beta = coeffs of (1-q)*prod[s_i]_q, F_s = class sums mod r, sigma=sum(s_i-1)
# excess m OK iff F_{v mod r}>=0 for all integers v in [sigma+2-r(m+1), (sigma+1-rm)/2)
from load import *
from collections import Counter
def Fvec(r,a):
    s=[x%r for x in a]
    B=[1]
    for x in s:
        n=[0]*(len(B)+x-1)
        for i,v in enumerate(B):
            for j in range(x): n[i+j]+=v
        B=n
    sig=len(B)-1
    beta=[(B[j] if j<=sig else 0)-(B[j-1] if j>=1 else 0) for j in range(sig+2)]
    F=[0]*r
    for j,v in enumerate(beta): F[j%r]+=v
    return F,sig
def okm(r,F,sig,m):
    M=sig+1-r*m
    v=M-r+1
    while 2*v<M:
        if F[v%r]<0: return False
        v+=1
    return True
def pred_excess_i(r,a,mmax=40):
    F,sig=Fvec(r,a); m=0
    while m<mmax and okm(r,F,sig,m+1): m+=1
    return m
if __name__=='__main__':
    for r in range(2,7):
        D=load(r); C=Counter(); exs=[]
        for a,mask in D:
            B=max(uniset(mask)); Q=sum(x//r for x in a); true=B-1-Q
            p=pred_excess_i(r,a)
            C[(true,p)]+=1
            if true!=p and len(exs)<4: exs.append((a,true,p))
        print(r,sorted(C.items()),exs)
