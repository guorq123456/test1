# at b=B*+1 (first failure), list violating v and M; also R_s values
from load import *
from scond import Sfun, uni_via_S
import sys, random
r=int(sys.argv[1]); random.seed(int(sys.argv[2]))
D=load(r)
for a,m in random.sample(D,int(sys.argv[3])):
    S_=uniset(m); B=max(S_); first_fail=min(b for b in range(1,61) if b not in S_)
    S,Dg=Sfun(a,r)
    ok,bad,M=uni_via_S(a,r,first_fail)
    R=[S(-r+s) if s>0 else S(-r) for s in range(r)]
    R=[S(s-r) for s in range(r)]
    Q=sum(x//r for x in a); sig=sum(x%r-1 for x in a)
    print(a,"res",[x%r for x in a],"B*",B,"Q",Q,"sig",sig,"D",Dg,"M",M,"bad v",bad[:6],"R",R,"pairs",[(S(v),S(M-v)) for v in bad[:3]])
