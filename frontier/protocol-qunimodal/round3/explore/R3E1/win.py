"""Window (t-coordinate) reformulation of the class-pair framework.
Doubled coordinate Z = D+1-2x; eps(Z) = delta_x (odd in Z). For b == F (mod 2) and gap g in (0,r),
V_b(g) = sum_{j=0}^{b-1} eps(g + (2j-(b-1)) r)   (b-window centred at z=g/2, binding windows for b==F),
Q_b(g) = V_{b-1}(g) + e(g + b r)                 (b-window centred at z=(g+r)/2, binding for b==F+1).
n*(g) = (least b==F with V_b(g)<0) - 1 ; N* = min_g n*(g); S2 <=> exists g with Q_{N*+4}(g) < 0.
"""
import numpy as np, sys
def load(fn):
    with open(fn) as f:
        r,k,D,F,E=map(int,f.readline().split())
        d=np.array([float(l) for l in f])
    return r,k,D,F,d
class Inst:
    def __init__(s,r,D,F,delta):
        s.r,s.D,s.F=r,D,F; s.delta=delta; s.X=len(delta)-1
    def e(s,Z):  # Z>0 doubled coordinate, Z==D+1 mod 2
        Z=np.asarray(Z); x=(s.D+1-Z)//2
        out=np.zeros(Z.shape)
        m=(Z>0)&(x>=0)
        out[m]=s.delta[x[m]]
        return out
    def eps(s,Z):
        Z=np.asarray(Z); return np.sign(Z)*s.e(np.abs(Z))
    def gaps(s,b):
        r=s.r; g=np.arange(1,r)
        ok=((g-(b-1)*r-(s.D+1))%2==0)
        return g[ok]
    def V(s,b,g):
        g=np.asarray(g); r=s.r
        js=np.arange(b)
        Z=g[:,None]+((2*js-(b-1))*r)[None,:]
        return s.eps(Z).sum(axis=1)
    def Q(s,b,g):
        return s.V(b-1,g)+s.e(np.asarray(g)+b*s.r)
    def analyze(s,bmax=None):
        r,F=s.r,s.F
        b0=2 if F%2==0 else 1
        g=s.gaps(b0)
        nstar=np.full(g.shape,10**9)
        b=b0; v=s.V(b,g)
        while (nstar>=10**9).any() and b<4*(s.D+1)//r+10:
            m=(v<0)&(nstar>=10**9); nstar[m]=b-1
            v=v+s.eps(g+(b+1)*r)+s.eps(g-(b+1)*r); b+=2
        N=nstar.min()
        return g,nstar,N
if __name__=="__main__":
    r,k,D,F,d=load(sys.argv[1]); I=Inst(r,D,F,d)
    g,ns,N=I.analyze()
    print("r",r,"k",k,"D",D,"F",F,"N*",N,"binding g range",g[ns==N].min(),g[ns==N].max(),"count",(ns==N).sum())
    for bb in (N+2,N+4):
        q=I.Q(bb,g); print("Q_%d min"%bb,q.min(),"at g",g[q.argmin()],"#neg",(q<0).sum())
