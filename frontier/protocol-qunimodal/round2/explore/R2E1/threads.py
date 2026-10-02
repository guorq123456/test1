# Thread formula: for each mirror pair {rho, sigma=D+1-rho mod r}, rho != sigma,
# y_0>y_1>... = integers < c0=(D+1)/2 in rho U sigma; d_i = delta_{y_i};
# V_b = sum_{i<b} (-1)^{b-1-i} d_i.  Claim: b in U <=> all threads: V_b>=0 and V_{b-1}+d_b>=0.
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
def delta_seq(A):
    D=len(A)-1
    return lambda j: (A[j] if 0<=j<=D else 0)-(A[j-1] if 0<=j-1<=D else 0)
def threads(r,a,length):
    assert in_box(r,a), 'outside fit box'
    A=poly_a(a); D=len(A)-1; dl=delta_seq(A)
    out=[]
    seen=set()
    for rho in range(r):
        sig=(D+1-rho)%r
        if sig==rho or (min(rho,sig),max(rho,sig)) in seen: continue
        seen.add((min(rho,sig),max(rho,sig)))
        # integers y < (D+1)/2, y = rho or sig mod r, decreasing
        top=D//2 if True else None   # largest integer < (D+1)/2 is floor(D/2)
        ys=[]; y=top
        while len(ys)<length:
            if y%r in (rho,sig): ys.append(y)
            y-=1
        out.append(((rho,sig),ys,[dl(y) for y in ys]))
    return out,D
def V(d,b):
    return sum((-1)**(b-1-i)*d[i] for i in range(b))
def U_threads(r,a,bmax):
    th,D=threads(r,a,2*bmax+4)
    res=[]
    for b in range(1,bmax+1):
        ok=all(V(d,b)>=0 and V(d,b-1)+d[b]>=0 for _,_,d in th)
        if ok: res.append(b)
    return res
if __name__=="__main__":
    import random
    random.seed(7); bad=0; n=0
    for it in range(3000):
        r=random.randint(2,12);k=random.randint(1,8)
        a=sorted(random.randint(2,30) for _ in range(k))
        A=poly_a(a);D=len(A)-1
        bmax=(D+1)//r+4
        U=U_set(r,a,bmax); U2=U_threads(r,a,bmax); n+=1
        if U!=U2: bad+=1; print(r,a,U,U2) if bad<10 else None
    print("tested",n,"mismatch",bad)
