# Thread reformulation in (P,Q,tau,n) form.
# For thread rho<sigma (rho+sigma = D+1 mod r, rho!=sigma): P_s=g_{rho+rs}, Q_s=g_{sigma+rs}, tau=tau_rho.
# n = e + [low] - beta,  e=floor((E+1)/r), low <=> rho+sigma == (E+1)%r.
# OK(n): n<=-1: tau==0;  n=2s+1: P_{s-1}-Q_s <= tau <= P_s-Q_{s-1};  n=2s+2: P_s-Q_s <= tau <= P_{s+1}-Q_{s-1}
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
class Thr:
    def __init__(s,r,a):
        assert in_box(r,a), 'outside fit box'
        s.r=r; s.a=sorted(a); s.A=poly_a(s.a); s.D=len(s.A)-1
        s.F=sum(x//r for x in a); s.E=sum(x%r-1 for x in a)
        s.e=(s.E+1)//r; s.lam=(s.E+1)%r
        L=s.D+3*r+5; s.g=gseq(s.A,r,L)
        base=(s.D//r+2)*r; s.tau=[s.g[base+t] for t in range(r)]
        s.c0=(s.D+1)/2
        s.threads=[]
        for rho in range(r):
            sig=(s.D+1-rho)%r
            if sig<=rho: continue
            low = (rho+sig==s.lam)
            s.threads.append((rho,sig,low))
    def G(s,m):
        if m<0: return 0
        assert m < s.c0, (m,s.c0)
        return s.g[m]
    def P(s,rho,t): return s.G(rho+s.r*t) if t>=0 else 0
    def interval(s,rho,sig,n):
        if n<0: return (0,0)
        if n%2==1:
            t=(n-1)//2
            return (s.P(rho,t-1)-s.P(sig,t), s.P(rho,t)-s.P(sig,t-1))
        t=(n-2)//2
        return (s.P(rho,t)-s.P(sig,t), s.P(rho,t+1)-s.P(sig,t-1))
    def ok_thread(s,th,beta):
        rho,sig,low=th
        n=s.e+(1 if low else 0)-beta
        lo,hi=s.interval(rho,sig,n)
        return lo<=s.tau[rho]<=hi
    def ok(s,beta):
        return all(s.ok_thread(th,beta) for th in s.threads)
if __name__=="__main__":
    import random
    random.seed(11); bad=0
    for it in range(3000):
        r=random.randint(3,12);k=random.randint(1,8)
        a=sorted(random.choice([x for x in range(2,30) if x%r]) for _ in range(k))
        T=Thr(r,a); U=U_set(r,a)
        bmax=max(U)+4
        U2=[b for b in range(1,bmax+1) if T.ok(b-T.F)]
        if U2!=[b for b in U if b<=bmax]: bad+=1; print(r,a,U,U2) if bad<10 else None
    print("mismatch",bad)
