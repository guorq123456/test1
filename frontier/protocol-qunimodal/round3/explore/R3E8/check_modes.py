# (1) dominant mode set is {1,r-1} whenever a middle residue is present; (2) on the window lattice the
# dominant-mode part of tau equals (4 sin(pi/r)/r) e^{l1} (-1)^e sin(2 pi u/r); report max relative error
# of that approximation vs exact tau for k in [20,60] (subdominant modes) and Stirling constant c0 check.
import random, math
from variants import _dom, gdom
from uinf import tau_of
random.seed(7); wc=0; ws=0; ndom=0
for _ in range(300):
    r=random.randint(4,30); k=random.randint(20,60); s=[random.randint(2,r-2) for _ in range(k)]+[1]
    k=len(s); S1=sum(x-1 for x in s)
    Lk,dom=_dom(r,s); assert sorted(j for v,j,sg in dom)==[1,r-1]; ndom+=1
    tau=tau_of(r,s); A=math.exp(Lk)
    for e in (1,2):
        D=S1+1-r*(e+1)
        for m in range(D//2+1, D//2+1+r):
            u=m-D/2
            ex=float(tau[m%r])/A
            b=4*math.sin(math.pi/r)/r*((-1)**e)*math.sin(2*math.pi*u/r)
            ws=max(ws,abs(b-ex))
print('instances',ndom,'dominant set {1,r-1} in all; max |tau/e^l1 - formula| =',ws)
mx=0
for k,th in ((1000,0.5),(4000,2.0),(20000,0.3)):
    for x in (0,3,-5):
        m=th*k+x
        lnB=math.lgamma(m+k-1)-math.lgamma(k-1)-math.lgamma(m+1)
        H=(1+th)*math.log(1+th)-th*math.log(th); lam=math.log(1+1/th)
        c0=-1.5*math.log(1+th)-0.5*math.log(th)-0.5*math.log(2*math.pi)
        mx=max(mx,abs(lnB-(k*H-0.5*math.log(k)+lam*x+c0)))
print('Stirling expansion max abs error (k>=1000, |x|<=5):',mx)
