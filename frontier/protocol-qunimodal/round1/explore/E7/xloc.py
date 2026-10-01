# Location of the type-I failure point X (b-independent) relative to D, quasi-center c=(D-r+1)/2, and r-blocks.
# Over all 69212 tuples (no r|a_i, entries 2..12, k<=8).
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p, _g
firsthalf_ok=True; minXD=collections.defaultdict(lambda:10**9); maxXD=collections.defaultdict(lambda:-10**9)
late=collections.Counter(); Zc=collections.Counter(); Zbad=0
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k])
    p=_p(a); D=len(p)-1; g=_g(p,r,D+3*r)
    i0=next(i for i in range(len(g)) if g[i]<0); X=i0-1
    if 2*i0 <= D-r+1: firsthalf_ok=False
    minXD[r]=min(minXD[r],X-D); maxXD[r]=max(maxXD[r],X-D)
    late[(r,'X>=D-r+1 (tail zone)' if X>=D-r+1 else 'X<D-r+1 (interior zone)')]+=1
    F=sum(v//r for v in a); Z=2*X+1-D-r*F
    if not (1<=Z%(2*r)<=r-1): Zbad+=1
    Zc[(r,Z//r)]+=1
print("first negative coefficient of G always strictly beyond quasi-center (D-r+1)/2:",firsthalf_ok)
for r in range(2,7): print("r",r,"X-D range",minXD[r],maxXD[r])
for kk in sorted(late): print(kk,late[kk])
print("tuples violating Z mod 2r in [1,r-1] (Z=2X+1-D-rF):",Zbad)
print("floor(Z/r) = B_A-1-F distribution:",sorted(Zc.items()))
