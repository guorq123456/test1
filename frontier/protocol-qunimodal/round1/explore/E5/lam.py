# closed form for condition (i): lambda = # leading nonpositive among F_{-1},F_{-2},...; m_i = max(0, floor((sig+2lam+3-2r)/r))
from load import *
from predF import Fvec, pred_excess_i
from collections import Counter
for r in range(2,7):
    C=Counter(); seen={}
    for a,mask in load(r):
        F,sig=Fvec(r,a)
        lam=0
        while lam<r and F[(-1-lam)%r]<=0: lam+=1
        mi=max(0,(sig+2*lam+3-2*r)//r)
        p=pred_excess_i(r,a)
        C[(p,mi)]+=1
    print(r,sorted(C.items()))
