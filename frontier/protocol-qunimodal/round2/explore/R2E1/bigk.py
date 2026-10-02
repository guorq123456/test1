# S2 and failure-height analysis in large-k, middle-residue regimes (inside fit box).
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from core import U_set
from test_s2 import s2_ok
def thread_G(T,rho,sig):
    z=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): z.append(m)
        m+=1
    return z,[0,0]+[T.g[x] for x in z]
def analyze(r,a):
    T=Thr(r,a); U=U_set(r,a)
    ok,why=s2_ok(U,T.F)
    res=[]
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j>=-1 else 0
        fo=[n for n in range(-1,I) if (n-pi)%2==0 and Gf(n)-Gf(n-1)<Tv]
        fm=[n for n in range(-1,I) if (n-pi)%2==1 and Gf(n+1)-Gf(n-2)<Tv]
        res.append((max(fo) if fo else None, max(fm) if fm else None, Tv<0))
    return U,T.F,T.e,ok,res
if __name__=="__main__":
    for (r,a) in [(30,[15]*40),(30,[15]*60),(20,[10]*40),(20,[7]*40+[]),(12,[6]*30),(25,[12]*50),(30,[14]*20+[16]*20)]:
        U,F,e,ok,res=analyze(r,a)
        print(r,a[:3],len(a),"U",U,"F",F,"e",e,"S2",ok,"max fail n (off,main):",[(x,y) for x,y,_ in res][:8], "TSneg",any(t for _,_,t in res))
