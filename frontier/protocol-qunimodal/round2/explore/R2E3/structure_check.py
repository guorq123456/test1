# Check the proved structure theorem numerically and measure the open gap:
#   U = [1,sigma] U {sigma+2, sigma+4, ..., tau*-2},  sigma = min_delta s0^delta, tau* = min_delta t1^delta,
#   sigma == tau* == 1+F (mod 2), tau* >= sigma+2.   (S2  <=>  tau* <= sigma+4.)
# U computed independently by tcrit (validated vs ground truth in val1.py).
import sys, random, itertools
sys.path.insert(0,'.')
from zigzag import ZZ
from tcrit import F_of
from s2check import Uset
from collections import Counter
def sig_tau(r,a):
    z=ZZ(r,a); s0s=[]; t1s=[]
    for d2,(E,A) in z.data.items():
        s0=next((s for s,v in enumerate(A) if v<0),None)
        if s0 is None: continue
        Ev=lambda j: E[j] if j<len(E) else 0
        Am=lambda s: 0 if s<0 else A[s]
        b=s0+2
        while not (Ev(b)+Am(b-2)<0): b+=2
        s0s.append(s0); t1s.append(b)
    return min(s0s),min(t1s)
def run(gen,label):
    c=Counter(); bad=0; n=0
    for r,a in gen:
        if any(x%r==0 for x in a): continue
        n+=1
        sg,ts=sig_tau(r,a); F=F_of(r,a)
        U,_=Uset(r,a)
        pred=list(range(1,sg+1))+list(range(sg+2,ts-1,2))
        okpar=(sg-1-F)%2==0 and (ts-1-F)%2==0 and ts>=sg+2
        if pred!=U or not okpar: bad+=1; print("MISMATCH",r,a,U,pred,F)
        c[ts-sg]+=1
    print(label,"instances",n,"structure mismatches",bad,"distribution of tau*-sigma:",sorted(c.items()))
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2])
    def g():
        for it in range(N):
            r=random.randint(2,30); k=random.randint(1,14)
            yield r,sorted(min(100,random.randint(1,random.choice([r-1,2*r,4*r,100]))) for _ in range(k))
    run(g(),"random")
    def h(r,k,amax):
        for a in itertools.combinations_with_replacement(range(1,amax+1),k): yield r,list(a)
    run(h(6,6,13),"exh r=6 k=6 a<=13")
    run(h(5,5,16),"exh r=5 k=5 a<=16")
    run(h(4,7,9),"exh r=4 k=7 a<=9")
    run(h(3,8,10),"exh r=3 k=8 a<=10")
