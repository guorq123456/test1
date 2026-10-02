"""kappa at the crossing for real instances with small k (4..10 parts, all residues middle), r<=120 and r>=1000."""
import random, sys, math
from winx import InstX
from box import in_box
from kappa_real import kappa
rng=random.Random(int(sys.argv[1])); res=[]
for it in range(int(sys.argv[2])):
    big=rng.random()<0.2
    r=rng.randint(1000,5000) if big else rng.randint(5,120); k=rng.randint(4,10)
    a=sorted(rng.randint(0,(400//r) if not big else 2)*r+rng.randint(2,r-2) for _ in range(k))
    if not in_box(r,a): continue
    I=InstX(r,a); N,kp=kappa(I); res.append((kp,r,a,N))
res=[t for t in res if t[0]==t[0]]; res.sort(key=lambda t:(t[0]==float("inf"),t[0]))
for t in res[:12]: print("kappa %.3f r %d N* %d a %s"%(t[0],t[1],t[3],t[2]))
print("count",len(res))
