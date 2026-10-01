# (1) rule_Abound errors are all false positives (consistent with Theorem 2: unimodal => b <= B*_A)
# (2) m_A (=B*_A-1-Q) == 0 for all k<=3 tuples (=> necessity of conjecture bound for k<=3 via Theorem 2), r=2..6 in box
import sys; sys.path.insert(0,'rules')
from common import gamma
from load import load, uniset
fp=fn=0; mA_k3=set(); cnt=0
for r in range(2,7):
    for a,mask in load(r):
        G=gamma(r,a); D=sum(x-1 for x in a); Q=sum(x//r for x in a)
        mu=r-1
        while mu>0 and G[mu-1]>=G[mu]: mu-=1
        BA=1+(D+1-2*mu)//r
        for b in range(1,61):
            t=bool((mask>>(b-1))&1); p=b<=BA
            if p and not t: fp+=1
            if t and not p: fn+=1
        if len(a)<=3: mA_k3.add(BA-1-Q); cnt+=1
print("false positives",fp,"false negatives",fn)
print("k<=3 tuples",cnt,"set of m_A values",mA_k3)
