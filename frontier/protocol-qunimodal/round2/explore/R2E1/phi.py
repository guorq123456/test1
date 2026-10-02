# Phi(K): for all m < K/2: h_m <= h_{K-m}; h = principal value of A/[r]_q.  (2h integer)
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
class Inst:
    def __init__(s,r,a):
        assert in_box(r,a)
        s.r=r; s.a=sorted(a); s.A=poly_a(s.a); s.D=len(s.A)-1
        s.F=sum(x//r for x in a); s.E=sum(x%r-1 for x in a)
        L=s.D+3*r+5
        s.g=gseq(s.A,r,L)
        s.tau=[s.g[s.D+r+t - ((s.D+r+t)%r) + t] if False else None for t in range(r)]
        base=(s.D//r+2)*r
        s.tau=[s.g[base+t] for t in range(r)]
    def gg(s,m):
        if m<0: return 0
        if m>=len(s.g): return s.tau[m%s.r]
        return s.g[m]
    def h2(s,m):  # 2*h_m
        return 2*s.gg(m)-s.tau[m%s.r]
    def phi_window(s,K):
        r=s.r; top=-((-K)//2)-1  # ceil(K/2)-1
        return all(s.h2(m)<=s.h2(K-m) for m in range(top-r+1,top+1))
    def phi_full(s,K,lo=None):
        r=s.r; top=-((-K)//2)-1
        if lo is None: lo=min(K,0)-3*r
        return all(s.h2(m)<=s.h2(K-m) for m in range(lo,top+1))
    def Kb(s,b): return s.D+1-s.r*(b+1)
if __name__=="__main__":
    import random
    random.seed(5); bad=0
    for it in range(400):
        r=random.randint(3,9);k=random.randint(1,7)
        a=sorted(random.choice([x for x in range(2,25) if x%r]) for _ in range(k))
        I=Inst(r,a); U=U_set(r,a)
        bm=max(U)+3
        U2=[b for b in range(1,bm+1) if I.phi_window(I.Kb(b))]
        U3=[b for b in range(1,bm+1) if I.phi_full(I.Kb(b))]
        if U2!=[b for b in U if b<=bm] or U3!=U2: bad+=1; print(r,a,U,U2,U3)
        # window vs full for all K
        for K in range(-4*r, I.D+2-r):
            if I.phi_window(K)!=I.phi_full(K): bad+=1; print("winfull",r,a,K); break
    print("bad",bad)
