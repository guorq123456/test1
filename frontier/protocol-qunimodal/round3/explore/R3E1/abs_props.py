"""For abstract S2 counterexamples: compute |A(zeta^j)|/alpha_0 (aliasing vs edge coefficient), T6 = 1+floor((D+1-2mu)/r)
(mu = least t with Gamma_t>=...>=Gamma_{r-1}) versus max U, and the decay kappa = ln(e(z)/e(z+r)) at the crossing level."""
import cmath, math, sys
from geo2 import alpha
from geo3 import mul
from geo_test import U_of, s2shape
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a
def props(al,r):
    D=len(al)-1
    alias=min(abs(sum(c*cmath.exp(2j*math.pi*jj*x/r) for x,c in enumerate(al))) for jj in range(1,r) if math.gcd(jj,r)==1)
    Gam=[sum(al[x] for x in range(D+1) if x%r==t) for t in range(r)]
    mu=min(t for t in range(r) if all(Gam[i]>=Gam[i+1] for i in range(t,r-1)))
    T6=1+(D+1-2*mu)//r
    U=U_of(al,r,2*len(al)//r+6)
    N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
    # kappa at crossing level: L=(N+2)r/2 in z; x = (D+1)/2 - z
    zc=(N+2)*r/2; x1=int(round((D+1)/2-zc)); x2=x1-r
    alx=al+[0]; d=lambda x: (alx[x]-(alx[x-1] if x>0 else 0)) if x>=0 else 0
    kap=math.log(d(x1)/d(x2)) if x2>=0 and d(x2)>0 and d(x1)>0 else float('inf')
    return dict(D=D,U=U[:10],Nstar=N,maxU=max(U),T6=T6,alias_over_a0=alias/al[0],kappa=kap,S2=s2shape(U))
if __name__=="__main__":
    ex=[("geo2 m8 G10",alpha(8,10),3),("geo2 m13 G10",alpha(13,10),6),("geo*[6][4]",mul(alpha(13,40),poly_a([6,4])),8),
        ("geo*[29]",mul(alpha(8,20),poly_a([29])),3),("geo*[32]",mul(alpha(20,40),poly_a([32])),18)]
    for name,al,r in ex: print(name,"r",r,props(al,r))
