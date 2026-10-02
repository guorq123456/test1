# Normalized (C)-margin per thread: for j = F mod 2 with V_j<0 (off failure at j):
#   m = -(V_{j+2}+d_{j+3}) / (|V_{j+2}|+d_{j+3})   ; (C) holds iff m>0 for all such j. Report min margin.
import sys, itertools, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
def min_margin(r,a):
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    best=None
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0: continue
            num=-(Vs[j+2]+d[j+3]); den=abs(Vs[j+2])+d[j+3]
            m=num/den if den else 1.0
            if best is None or m<best[0]: best=(m,pair,j,ys[j:j+4],d[j:j+4],Vs[j],Vs[j+2])
    return best
if __name__=="__main__":
    mode=sys.argv[1]; glob=None; n=0
    if mode=='F0':   # all a_i < r, exhaustive multisets for given r, k range
        r=int(sys.argv[2]); kmax=int(sys.argv[3])
        for k in range(2,kmax+1):
            for a in itertools.combinations_with_replacement(range(2,r),k):
                a=list(a)
                if not in_box(r,a): continue
                mm=min_margin(r,a); n+=1
                if mm and (glob is None or mm[0]<glob[0]): glob=(mm[0],r,a,mm)
    print("instances",n,"min margin",glob)
