# Test: for every non-unimodal instance with b > B_A (B_A = threshold of condition (I)), number of strict valleys == b - B_A.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p, _g
BA={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k])
    p=_p(a); D=len(p)-1; g=_g(p,r,D+3*r)
    X=next(i for i in range(len(g)) if g[i]<0)-1
    BA[(r,a)]=1+(2*X+1-D)//r
c=collections.Counter(); ex=[]
for L in open('/tmp/claude-0/qu/explore/E7/viol.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); b,D,R,N,t,s,nd=x[2+k:]
    j=b-BA[(r,a)]
    if j<=0: c['b<=B_A (type II)']+=1; continue
    ok = (nd==j)
    c['nd==b-B_A' if ok else 'nd!=b-B_A']+=1
    if not ok and len(ex)<10: ex.append((r,a,b,BA[(r,a)],nd))
print(dict(c)); print(ex)
