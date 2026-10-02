# Coverage of the proved sufficient condition (Theorem 15b): B_off >= F + e - 4  ==> S2 holds.
# Also checks Theorem 15a's hypothesis (L' at first off-failure for some failing thread) on each instance.
import sys, itertools, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import U_set, in_box
from threads import threads, V
C=Counter()
def run(r,a):
    U=U_set(r,a); F=sum(x//r for x in a); E=sum(x%r-1 for x in a); e=(E+1)//r
    Boff=max([b for b in U if (b-F)%2==0],default=0)
    C['inst']+=1
    if Boff>=F+e-4: C['cond15b']+=1
    # 15a: exists thread with V_{j*}<0 at j*=Boff+2 and L' there
    js=Boff+2
    th,D=threads(r,a,js+6)
    ok=False
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(js+5)]
        if Vs[js]<0 and d[js]-d[js+1]>=d[js+3]: ok=True
    if ok: C['cond15a']+=1
mode=sys.argv[1]
if mode=='exh':
    for r in range(4,9):
        vals=[x for x in range(2,2*r+3) if x%r]
        for k in range(1,7):
            for a in itertools.combinations_with_replacement(vals,k): run(r,list(a))
else:
    random.seed(int(sys.argv[2]))
    for it in range(int(sys.argv[3])):
        r=random.randint(4,30); k=random.randint(2,40)
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort()
        if in_box(r,a): run(r,a)
print(mode,dict(C))
