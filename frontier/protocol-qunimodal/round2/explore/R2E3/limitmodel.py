# Limit model (all a_i large, residues rho_i fixed, r divides no a_i):
#  c_j = [q^j] 1/((1-q)^{k-1}(1-q^r)) for j>=0, 0 for j<0;  tau_j = class-(j mod r) sum of coeffs of (1-q)prod[rho_i]_q.
#  For beta' >= 1 put K = S+1-r-r*beta', S = sum(rho_i-1).  Claim: F+beta' in U  <=>  for all integers j > K/2 : c_j - tau_j >= c_{K-j}.
import sys, random
sys.path.insert(0,'.')
from tcrit import poly_a, F_of
from s2check import Uset
def limit_U(r,rho,bmax=60):
    k=len(rho); S=sum(x-1 for x in rho)
    R=poly_a(rho); d=[R[0]]+[R[m]-R[m-1] for m in range(1,len(R))]+[-R[-1]]
    tau=[sum(d[t::r]) for t in range(r)]
    L=4*r*(bmax+3)+S+10
    # c: 1/((1-q)^{k-1}(1-q^r))
    c=[0]*L; c[0]=1
    for _ in range(k-1):
        for j in range(1,L): c[j]+=c[j-1]
    for j in range(r,L): c[j]+=c[j-r]
    C=lambda j: c[j] if j>=0 else 0
    out=[]
    for bp in range(1,bmax+1):
        K=S+1-r-r*bp
        ok=True
        for j in range(K//2+1, L//2):
            if 2*j<=K: continue
            if C(j)-tau[j%r] < C(K-j): ok=False;break
        if ok: out.append(bp)
    return out
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); bad=0; n=0
    for it in range(N):
        r=random.randint(2,8); k=random.randint(1,7)
        rho=[random.randint(1,r-1) for _ in range(k)]
        mult=random.randint(4,6)
        a=sorted(x+r*random.randint(mult,mult+3) for x in rho)
        if max(a)>100: continue
        U,t=Uset(r,a); F=F_of(r,a)
        Ul=limit_U(r,sorted(rho),bmax=max(U)-F+5)
        pred=list(range(1,F+1))+[F+x for x in Ul]
        n+=1
        if pred!=U: bad+=1; print("MISMATCH",r,a,U,pred)
    print("limit model vs exact (a_i>=4r): instances",n,"mismatches",bad)
