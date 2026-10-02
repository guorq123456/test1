# Zigzag (per class-pair) criterion, derived in proof file (Lemma Z):
# For delta in (0,r/2) with delta in M+Z (M=(D+1)/2), let pi_0<pi_1<... enumerate {x>0 : x = +-delta mod r},
# E_j = e(pi_j) = d_{M-pi_j} (d = coeffs of (1-q)A), A_s = E_s - E_{s-1} + ... +-E_0 (A_{-1}=0).
# Claim: P_b unimodal <=> for every such delta:  A_{b-1} >= 0  and  A_{b-2}+A_{b-1}+A_b >= 0.
import sys, random
sys.path.insert(0,'.')
from tcrit import poly_a
class ZZ:
    def __init__(self,r,a,smax=None):
        self.r=r; al=poly_a(a); D=len(al)-1; self.D=D
        d=[al[0]]+[al[m]-al[m-1] for m in range(1,D+1)]+[-al[D]]
        self.d=d
        if smax is None: smax=2*(D+2)//r+8
        self.data={}
        for d2 in range(1,r):           # 2*delta
            if (D+1-d2)%2: continue
            xs=[]
            n=0
            while len(xs)<smax+3:
                xs.append(d2+2*r*n); xs.append(2*r-d2+2*r*n); n+=1
            xs.sort()
            E=[]
            for x2 in xs:
                m2=D+1-x2; E.append(d[m2//2] if m2>=0 else 0)
            A=[]; prev=0
            for s,Ev in enumerate(E):
                prev=Ev-prev; A.append(prev)
            self.data[d2]=(E,A)
    def Ud(self,d2,b):
        E,A=self.data[d2]
        Am=lambda s: 0 if s<0 else A[s]
        return Am(b-1)>=0 and Am(b-2)+Am(b-1)+Am(b)>=0
    def uni(self,b):
        return all(self.Ud(d2,b) for d2 in self.data)
if __name__=='__main__':
    sys.path.insert(0,'/tmp/claude-0/qu/tools')
    from uni_ref import poly, unimodal
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); bad=0
    for it in range(N):
        r=random.randint(2,10); k=random.randint(1,7)
        a=sorted(random.randint(1,25) for _ in range(k)); b=random.randint(1,14)
        z=ZZ(r,a,smax=b+4)
        gt=unimodal(poly(r,a,b)); p=z.uni(b)
        if gt!=p: bad+=1; print("MISMATCH",r,a,b,gt,p)
    print("zigzag criterion vs ground truth: tested",N,"mismatches",bad)
