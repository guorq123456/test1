# candidate peeling: Z_c(b) = [r-1]^j [b+e]_{q^r} - q^{c}[b]_{q^r}, check nonneg+palindromic+unimodal
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a,times_b,unimodal
def Z(r,j,e,b):
    c=times_b(poly_a([r-1]*j),r,b+e)
    deg=len(c)-1
    sh=(deg-r*(b-1))
    assert sh%2==0
    sh//=2
    z=c[:]
    for t in range(b): z[sh+r*t]-=1
    return z
for r in [5,6,7,8,10]:
  for (j,e) in [(2,2),(1,1),(3,2),(4,3)]:
    res=[]
    for b in range(1,12):
        z=Z(r,j,e,b)
        res.append('N' if min(z)<0 else ('U' if unimodal(z) else 'x'))
    print(r,j,e,''.join(res))
