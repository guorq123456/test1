# Exhaustive test of Conjecture S2 on small parameter ranges (inside fit box).
import sys, itertools
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
def s2_ok(U,F):
    B=max(U)
    S=set(U)
    full=set(range(1,B+1))
    if (B-(1+F))%2!=0: return False,'parity'
    if S==full: return True,''
    if S==full-{B-1}: return True,''
    return False,'shape'
def main():
    rmin,rmax,kmax,amax=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
    cnt=0;bad=[]
    from collections import Counter
    shapes=Counter()
    for r in range(rmin,rmax+1):
        vals=[x for x in range(2,amax+1) if x%r!=0]
        for k in range(1,kmax+1):
            for a in itertools.combinations_with_replacement(vals,k):
                a=list(a)
                U=U_set(r,a); F=sum(x//r for x in a)
                cnt+=1
                ok,why=s2_ok(U,F)
                B=max(U)
                shapes['full' if set(U)==set(range(1,B+1)) else 'gap']+=1
                if not ok:
                    bad.append((r,a,U,F,why))
    print("tested",cnt,"bad",len(bad),dict(shapes))
    for x in bad[:30]: print(x)
if __name__=="__main__":
    main()
