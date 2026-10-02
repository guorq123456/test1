# Per-b gap analysis: f_b(l) = h_{(K+l)/2} - h_{(K-l)/2}, l in [1,2r], l = K mod 2.
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from phi import Inst
def gaps(I,b):
    K=I.Kb(b); r=I.r; out={}
    for l in range(1,2*r+1):
        if (K-l)%2: continue
        out[l]=I.h2((K+l)//2)-I.h2((K-l)//2)   # 2*f
    return out
def inner_ok(I,b): return all(v>=0 for l,v in gaps(I,b).items() if l<I.r)
def outer_ok(I,b): return all(v>=0 for l,v in gaps(I,b).items() if l>=I.r)
def report(r,a,bmax=None):
    I=Inst(r,a)
    if bmax is None: bmax=(I.D+1)//r+3
    print("r",r,"a",a,"D",I.D,"F",I.F,"E",I.E,"tau",I.tau)
    for b in range(1,bmax+1):
        G=gaps(I,b)
        fails=[l for l,v in G.items() if v<0]
        print(f" b={b} beta={b-I.F} K={I.Kb(b)} U={'Y' if not fails else '.'} inner={'Y' if inner_ok(I,b) else '.'} outer={'Y' if outer_ok(I,b) else '.'} fails={fails}")
if __name__=="__main__":
    r=int(sys.argv[1]); a=list(map(int,sys.argv[2].split(',')))
    report(r,a)
