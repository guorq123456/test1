# Principal-value central criterion (Lemma 4 in proof file):
# h_n = g_n - tau_n/2 where g = power-series coeffs of A/[r]_q, tau = r-periodic class sums of (1-q)A.
# zeta=(D+1-r)/2. P(b) unimodal <=> h_n <= h_{n+rb} for all integers n with  zeta - r <= n + rb/2 < zeta.
import sys
from fractions import Fraction as Fr
sys.path.insert(0,'.')
from tcrit import poly_a, F_of
class HS:
    def __init__(self,r,a):
        self.r=r; self.a=sorted(a)
        al=poly_a(a); self.D=D=len(al)-1
        d=[al[0]]+[al[m]-al[m-1] for m in range(1,D+1)]+[-al[D]]
        self.d=d
        L=D+2+r
        g=[0]*L
        for n in range(L):
            g[n]=(d[n] if n<=D+1 else 0)+(g[n-r] if n>=r else 0)
        self.g=g
        self.tau=[g[L-r+((t-(L-r))%r)] for t in range(r)]  # periodic tail
        self.R=1+sum(x%r-1 for x in a)
    def G(self,n):
        if n<0: return 0
        if n<len(self.g): return self.g[n]
        return self.tau[n%self.r]
    def h2(self,n):  # 2*h_n (integer)
        return 2*self.G(n)-self.tau[n%self.r]
    def uni(self,b):
        r=self.r; D=self.D
        # zeta - r <= n + rb/2 < zeta  <=> 2*zeta-2r <= 2n+rb < 2 zeta ; 2zeta = D+1-r
        lo2=D+1-r-2*r; hi2=D+1-r
        ok=True
        for n in range((lo2-r*b)//2-2,(hi2-r*b)//2+3):
            v=2*n+r*b
            if lo2<=v<hi2:
                if self.h2(n)>self.h2(n+r*b): return False
        return True
if __name__=='__main__':
    import random
    sys.path.insert(0,'/tmp/claude-0/qu/tools')
    from uni_ref import poly, unimodal
    random.seed(11); bad=0
    for it in range(3000):
        r=random.randint(2,9); k=random.randint(1,6)
        a=sorted(random.randint(1,20) for _ in range(k)); b=random.randint(1,12)
        gt=unimodal(poly(r,a,b)); p=HS(r,a).uni(b)
        if gt!=p: bad+=1; print("MISMATCH",r,a,b,gt,p)
    print("principal-value central criterion mismatches:",bad,"of 3000")
