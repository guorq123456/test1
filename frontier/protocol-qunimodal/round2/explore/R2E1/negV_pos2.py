# Lemma L' margin by k: among V_j<0 (j=F mod 2) with d_{j+3}>0, min of (d_j-d_{j+1})/d_{j+3}, grouped by k.
import sys, random, itertools
from collections import Counter, defaultdict
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
best=defaultdict(lambda: None); cnt=Counter(); zero=Counter()
def run(r,a):
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    k=len(a)
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0: continue
            cnt[k]+=1
            if d[j+3]==0: zero[k]+=1; continue
            rat=(d[j]-d[j+1])/d[j+3]
            if best[k] is None or rat<best[k][0]: best[k]=(rat,r,a,pair,j,ys[j:j+4],d[j:j+4],Vs[j])
mode=sys.argv[1]
if mode=='exh':
    for r in range(3,12):
        vals=[x for x in range(2,3*r+1) if x%r]
        for k in range(2,6):
            for a in itertools.combinations_with_replacement(vals,k):
                if in_box(r,list(a)): run(r,list(a))
else:
    random.seed(int(sys.argv[2]))
    for it in range(int(sys.argv[3])):
        r=random.randint(3,30); k=random.randint(4,12)
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort(); run(r,a)
for k in sorted(cnt): print(k,cnt[k],"d_{j+3}=0:",zero[k],"min ratio:",best[k][:1] if best[k] else None, best[k][1:] if best[k] and best[k][0]<3 else "")
