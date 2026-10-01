# list (r,a) with y*>=0 and compare with residue-only y*_pi and c(t)
import sys, itertools, random
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import *
from ystar import ystar
def cval(r,a):
    tt=tau(r,a); cs=[c for c in range(r) if tt[c]>0]
    return max(cs) if cs else None
random.seed(3)
rows=[]
for r in range(4,7):
    for k in range(4,9):
        combos=list(itertools.combinations_with_replacement(range(1,13),k))
        if len(combos)>1500: combos=random.sample(combos,1500)
        for a in combos:
            a=list(a)
            if any(x%r==0 for x in a): continue
            y=ystar(r,a)
            if y is not None and y>=0:
                t=sorted(x%r for x in a)
                ypi=ystar(r,t)
                rows.append((r,a,t,y,ypi,cval(r,a)))
print(len(rows))
for row in rows[:60]: print(row)
# does y* depend only on t?
from collections import defaultdict
g=defaultdict(set)
for r,a,t,y,ypi,c in rows: g[(r,tuple(t))].add(y)
print("t-classes",len(g),"with multiple y*:",sum(1 for v in g.values() if len(v)>1))
print("y*==ypi count",sum(1 for row in rows if row[3]==row[4]))
