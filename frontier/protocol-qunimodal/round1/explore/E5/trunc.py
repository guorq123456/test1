# Truncated exact criterion: unimodal at b iff for all integers v with 2v<M and M-v<2r:
#   F_{v mod r} + T(M-v) - T(v) >= 0, T(w)=0 (w<r), T(w)=f_{w-r} (r<=w<2r); f_j = A_j - A_{j-1}
# M = D+1-r(b-1). Here F from residues.
from load import *
from predF import Fvec
from scond import Apoly
from collections import Counter
def lowf(a,r):
    A=Apoly(a)+[0]*(2*r)
    return [A[j]-(A[j-1] if j else 0) for j in range(r)]
def trunc_ok(r,a,b,F=None,sig=None,f=None):
    if F is None: F,sig=Fvec(r,a)
    if f is None: f=lowf(a,r)
    D=sum(x-1 for x in a); M=D+1-r*(b-1)
    T=lambda w: 0 if w<r else f[w-r]
    v=M-2*r+1
    while 2*v<M:
        if F[v%r]+T(M-v)-T(v)<0: return False
        v+=1
    return True
if __name__=='__main__':
    for r in range(2,7):
        bad=0;tot=0
        for a,mask in load(r):
            F,sig=Fvec(r,a); f=lowf(a,r)
            for b in range(1,61):
                tot+=1
                if trunc_ok(r,a,b,F,sig,f)!=bool((mask>>(b-1))&1): bad+=1
        print(r,"instances",tot,"errors",bad)
