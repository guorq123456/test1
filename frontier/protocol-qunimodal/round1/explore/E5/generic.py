# test generic closed form m = max(0, 2*floor((sigma+3-r)/(2r))) vs m_A (residue-only (A)-bound) and true m*
from load import *
from predF import pred_excess_i
from collections import Counter
for r in range(2,7):
    C1=Counter(); C2=Counter()
    for a,mask in load(r):
        B=max(uniset(mask)); Q=sum(x//r for x in a); true=B-1-Q
        sig=sum(x%r-1 for x in a)
        g=max(0,2*((sig+3-r)//(2*r)))
        mA=pred_excess_i(r,a)
        C1[(g==mA)]+=1; C2[(g==true)]+=1
    print(r,"generic==m_A:",dict(C1)," generic==true:",dict(C2))
