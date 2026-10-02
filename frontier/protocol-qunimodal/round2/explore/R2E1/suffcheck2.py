# Targeted test of Lemma L / L' for small k (3..6) with large a_i (large-a regime).
import sys, random, itertools
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
C=Counter(); bad=[]
random.seed(int(sys.argv[1]))
for it in range(int(sys.argv[2])):
    r=random.randint(4,30); k=random.randint(3,6)
    a=[]
    while len(a)<k:
        x=random.randint(max(2,100-3*r),100)
        if x%r: a.append(x)
    a.sort()
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2: continue
            if Vs[j]<0:
                C['negV']+=1
                if not d[j]>=d[j+1]+d[j+3]:
                    C["L'_fail"]+=1
                    b=j+3  # main parity b=j+3? check crit: V_{b-1}=V_{j+2}
                    if Vs[j+2]+d[j+3]>=0: C['C_fail_main_ok']+=1
                    if len(bad)<5: bad.append((r,a,pair,j,d[j:j+4],Vs[j]))
            if j>=2 and Vs[j]<0 and not d[j-2]>=d[j-1]+d[j+1]:
                C['L_fail']+=1
print(dict(C))
for x in bad: print(x)
