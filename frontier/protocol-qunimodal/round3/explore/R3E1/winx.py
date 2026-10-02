"""EXACT window reformulation of the class-pair framework (Python big ints).
Doubled coordinate Z = D+1-2x; eps(Z) = delta_x, odd in Z; e = eps on Z>0.
For b == F (mod 2), gap g in (0,r) (g == D+1+(b-1)r mod 2):
  V_b(g) = sum_{j=0}^{b-1} eps(g + (2j-(b-1)) r)        [b-window centred at z=g/2]
  Q_b(g) = V_{b-1}(g) + e(g + b r)  (b == F+1)          [b-window centred at z=(g+r)/2]
  n*(g)  = (least b == F with V_b(g) < 0) - 1 ;  N* = min_g n*(g)
  Theorem 4.2 (synthesis) <=> U = [1,N*] u {N*+2,...,beta}; S2 <=> exists g with Q_{N*+4}(g) < 0.
(F even: g = r - C; F odd: g = C, C the class pair.)"""
import subprocess, math, os
from box import in_box
HERE=os.path.dirname(os.path.abspath(__file__))
class InstX:
    def __init__(s,r,a):
        assert in_box(r,a), "outside fit box"
        s.r=r; s.a=list(a); s.k=len(a)
        s.D=sum(x-1 for x in a); s.F=sum(x//r for x in a)
        bits=sum(math.log2(x) for x in a)+8; W=int(bits//64)+2
        out=subprocess.run([HERE+"/dumpdelta",str(W),str(r)]+[str(x) for x in a],capture_output=True,text=True,env=dict(os.environ,HEX="1")).stdout.split()
        s.delta=[int(h,16) for h in out[5:]]
        s.X=len(s.delta)-1
    def e(s,Z):
        if Z<=0: return 0
        x=(s.D+1-Z)//2
        return s.delta[x] if x>=0 else 0
    def eps(s,Z):
        return s.e(Z) if Z>0 else -s.e(-Z)
    def gaps(s,parity_b):
        return [g for g in range(1,s.r) if (g-(parity_b-1)*s.r-(s.D+1))%2==0]
    def V(s,b,g):
        return sum(s.eps(g+(2*j-(b-1))*s.r) for j in range(b))
    def Q(s,b,g):
        return s.V(b-1,g)+s.e(g+b*s.r)
    def analyze(s):
        """returns gaps list G, dict nstar[g], N*, and Vtab[g][b] for b==F up to N*+5"""
        r=s.r; b0=2 if s.F%2==0 else 1
        G=s.gaps(b0)
        nstar={}; Vt={g:{} for g in G}
        for g in G:
            b=b0; v=s.V(b,g); lim=4*(s.D+1)//r+10
            while b<lim:
                Vt[g][b]=v
                if v<0 and g not in nstar: nstar[g]=b-1
                if g in nstar and b>=nstar[g]+8: break
                v=v+s.eps(g+(b+1)*r)+s.eps(g-(b+1)*r); b+=2
        N=min(nstar.values())
        s.G,s.nstar,s.N,s.Vt=G,nstar,N,Vt
        return G,nstar,N
