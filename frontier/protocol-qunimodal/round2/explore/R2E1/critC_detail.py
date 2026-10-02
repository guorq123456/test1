# Detail of critical (C) configurations in top-down terms: b != F mod 2, V_{b-1} in [-d_b,0).
# Report whether the sufficient inequality d_{b-3} >= d_{b-2} + d_b holds, and margins.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box, poly_a
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
C=Counter(); rows=[]
for it in range(N):
    r=random.randint(4,30); k=random.randint(4,40)
    if random.random()<0.5:
        a=sorted(random.choice(range(2,r-1))+r*random.randint(0,(100-r)//r) for _ in range(k))
    else:
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort()
    if not in_box(r,a): continue
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for b in range(4,len(d)-1):
            if (b-F)%2==0: continue
            if Vs[b-1]<0 and Vs[b-1]+d[b]>=0:
                C['crit']+=1
                suff = d[b-3]>=d[b-2]+d[b]
                C['suff' if suff else 'nosuff']+=1
                if Vs[b-3]<0: C['VIOL']+=1
                if not suff: rows.append((r,a,pair,b,d[b-3:b+1],Vs[b-3],Vs[b-1]))
print(dict(C))
for x in rows[:10]: print(x)
