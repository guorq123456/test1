# Check Conjecture S2 on instances in fit box using tcrit (validated vs ground truth).
import random, sys, itertools
sys.path.insert(0,'.')
from tcrit import TS, F_of
def Uset(r,a):
    t=TS(r,a); bmax=(t.D+1)//r+3
    return [b for b in range(1,bmax+1) if t.uni_fast(b)], t
def s2ok(r,a,U):
    F=F_of(r,a)
    B=max(U)
    if (B-1-F)%2: return False,'parity'
    full=set(range(1,B+1))
    S=set(U)
    if S==full or S==full-{B-1}: return True,''
    return False,'shape'
if __name__=='__main__':
    mode=sys.argv[1]
    cnt=0; bad=0
    if mode=='exh':
        r=int(sys.argv[2]); k=int(sys.argv[3]); amax=int(sys.argv[4])
        for a in itertools.combinations_with_replacement(range(1,amax+1),k):
            if any(x%r==0 for x in a): continue
            U,t=Uset(r,list(a)); cnt+=1
            ok,why=s2ok(r,a,U)
            if not ok:
                bad+=1
                if bad<=10: print("FAIL",r,a,U,"F",F_of(r,a),why)
    else:
        seed=int(sys.argv[2]); N=int(sys.argv[3]); random.seed(seed)
        for it in range(N):
            r=random.randint(2,30); k=random.randint(1,12)
            amax=random.choice([r+3,2*r,3*r,100])
            a=sorted(random.randint(1,min(100,amax)) for _ in range(k))
            if any(x%r==0 for x in a): continue
            U,t=Uset(r,a); cnt+=1
            ok,why=s2ok(r,a,U)
            if not ok:
                bad+=1
                if bad<=10: print("FAIL",r,a,U,"F",F_of(r,a),why)
    print(mode,sys.argv[2:],"instances",cnt,"S2 failures",bad)
