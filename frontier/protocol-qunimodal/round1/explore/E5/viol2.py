# for cases where residue-only (i) prediction overshoots, show failing pairs at first failure
from load import *
from scond import Sfun, uni_via_S
from predF import pred_excess_i, Fvec
import sys
r=int(sys.argv[1]); cnt=0
for a,mask in load(r):
    S_=uniset(mask); B=max(S_); Q=sum(x//r for x in a); true=B-1-Q
    p=pred_excess_i(r,a)
    if true!=p:
        ff=min(b for b in range(1,61) if b not in S_)
        S,Dg=Sfun(a,r); ok,bad,M=uni_via_S(a,r,ff)
        F,sig=Fvec(r,a)
        print(a,[x%r for x in a],"sig",sig,"Q",Q,"true",true,"pred",p,"firstfail b",ff,"M",M,"bad",[(v,M-v,S(v),S(M-v)) for v in bad[:3]],"F",F)
        cnt+=1
        if cnt>=int(sys.argv[2]): break
