# For the O-failure residue multisets, compute U(a) for some lifts a (inside the fit box) and check the S2 shape,
# plus mu*(a) and whether ND_a(K_j) holds at the j where ND_rho failed.
from reslev import *
import subprocess
def Ufull(R,r,bmax):
    return [b for b in range(1,bmax+1) if R.unimodal(b)]
def mustar(R,r):
    # max u with Q_u<0 ; Q_u=0 for u>=D+1
    best=None
    for u in range(-r,R.D+2):
        if R.Q(u)<0: best=u
    return best
cases=[(57,[6, 7, 9, 15, 18, 20, 22, 23, 25, 26, 27, 28, 30, 33, 37],37,1),
       (28,[2, 3, 5, 5, 6, 7, 7, 7, 9, 10, 11, 12, 12, 13, 13, 17, 17, 18, 18, 23, 23],58,3)]
for r,rp,m,jf in cases:
    for t1,t2 in [(1,0),(1,1),(3,2),(6,5)]:
        a=sorted([1+r*t1]*m+[x+r*t2 for x in rp])
        if max(a)>400 or not inbox(r,a): continue
        R=Res(r,a); F=R.F; sigma=sum(x%r-1 for x in a)
        T=F+12
        U=Ufull(R,r,T)
        ms=mustar(R,r)
        Kj=sigma+1-r*(jf+2)
        print('r',r,'lift t1,t2',t1,t2,'k',len(a),'F',F,'U',U,'mu*(a)',ms,'ND_a(K_jf)',R.ND(Kj),flush=True)
        # cross-check two b values with the ground-truth tool
        for b in [U[-1],U[-1]+1]:
            line=f"{r} {len(a)} {' '.join(map(str,a))} {b}\n"
            out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=line,capture_output=True,text=True).stdout.strip()
            print('   uni b=',b,out, 'mine',int(b in U))
