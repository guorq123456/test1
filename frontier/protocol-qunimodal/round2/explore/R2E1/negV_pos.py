# Where can V_j<0 (j = F mod 2) occur? record positions relative to min(a), r, k; and margin ratio for Lemma L'.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
mx=Counter(); worst_ratio=None; stats=Counter()
for it in range(N):
    r=random.randint(3,30); k=random.randint(2,40)
    u=random.random()
    if u<0.3:
        a=sorted(random.choice(range(2,r-1 if r>3 else 3))+r*random.randint(0,(100-r)//r) for _ in range(k))
    elif u<0.6:
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
    if not in_box(r,a): continue
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    amin=min(a)
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0 or d[j]==0: continue
            stats['negV']+=1
            # position of y_j relative to amin
            if ys[j]>=amin: stats['y_j>=amin']+=1
            if ys[j+1]>=amin: stats['y_j+1>=amin']+=1
            if ys[j]>=r: stats['y_j>=r']+=1
            if ys[j]>=2*r: stats['y_j>=2r']+=1
            rat=(d[j]-d[j+1])/(d[j+3]) if d[j+3]>0 else float('inf')
            if worst_ratio is None or rat<worst_ratio[0]: worst_ratio=(rat,r,a,pair,j,ys[j:j+4],d[j:j+4],Vs[j])
print(dict(stats)); print("worst ratio",worst_ratio)
