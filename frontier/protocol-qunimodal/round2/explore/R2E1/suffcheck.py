# Test candidate lemma: for b != F (mod 2), b>=4, V_{b-1}<0  ==>  d_{b-3} >= d_{b-2} + d_b.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
C=Counter(); bad=[]
for it in range(N):
    r=random.randint(3,30); k=random.randint(2,40)
    u=random.random()
    if u<0.4:
        a=sorted(random.choice(range(2,r-1 if r>3 else 3))+r*random.randint(0,(100-r)//r) for _ in range(k))
    elif u<0.7:
        a=[]
        while len(a)<k:
            x=random.randint(2,min(100,r+4))
            if x%r: a.append(x)
        a.sort()
    else:
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort()
    if not in_box(r,a) or any(x%r==0 for x in a): continue
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for b in range(4,len(d)):
            if (b-F)%2==0: continue
            if Vs[b-1]<0:
                C['negV']+=1
                if not d[b-3]>=d[b-2]+d[b]:
                    C['lemma_fail']+=1
                    if Vs[b-1]+d[b]>=0: C['crit_fail']+=1
                    bad.append((r,a,pair,b,d[b-4:b+2],Vs[b-1]))
print(dict(C))
for x in bad[:8]: print(x)
