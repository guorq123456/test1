# Central-window formulation (Lemma 3 in proof file):
# d_m = alpha_m - alpha_{m-1}; M=(D+1)/2; e(u)=d_{M-u} (u in Z or Z+1/2 so that M-u integer).
# U(b) <=> for all theta in (0,r) with M - theta - r(b-1)/2 integer:
#   V_b(theta) = sum_{i in I_b} e(theta + r i) >= 0, I_b = {-(b-1)/2, ..., (b-1)/2} (step 1).
# Work with doubled coordinates to stay in integers: U2 = 2u.
import sys
from fractions import Fraction as Fr
sys.path.insert(0,'.')
from tcrit import poly_a, TS, F_of
class CW:
    def __init__(self,r,a):
        self.r=r; self.a=sorted(a)
        al=poly_a(a); self.D=D=len(al)-1
        self.d=[al[0]]+[al[m]-al[m-1] for m in range(1,D+1)]+[-al[D]]
    def dd(self,m):
        return self.d[m] if 0<=m<=self.D+1 else 0
    def e2(self,u2):
        # u2 = 2u ; index m = M - u = (D+1-u2)/2 must be integer
        m2=self.D+1-u2
        assert m2%2==0
        return self.dd(m2//2)
    def thetas2(self,b):
        # theta2 = 2*theta in (0,2r) with (D+1 - theta2 - r(b-1)) even
        return [t2 for t2 in range(1,2*self.r) if (self.D+1-t2-self.r*(b-1))%2==0]
    def V(self,b,t2):
        r=self.r
        # i ranges -(b-1)/2..(b-1)/2 ; 2*(theta + r i) = t2 + r*(2i), 2i = -(b-1),...,(b-1) step 2
        return sum(self.e2(t2+r*j2) for j2 in range(-(b-1),b,2))
    def uni(self,b):
        return all(self.V(b,t2)>=0 for t2 in self.thetas2(b))
if __name__=='__main__':
    import random
    sys.path.insert(0,'/tmp/claude-0/qu/tools')
    from uni_ref import poly, unimodal
    random.seed(7); bad=0
    for it in range(3000):
        r=random.randint(2,9); k=random.randint(1,6)
        a=sorted(random.randint(1,20) for _ in range(k)); b=random.randint(1,12)
        g=unimodal(poly(r,a,b)); p=CW(r,a).uni(b)
        if g!=p: bad+=1; print("MISMATCH",r,a,b,g,p)
    print("central-window criterion mismatches:",bad,"of 3000")
