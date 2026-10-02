# r=4: enumerate a with exactly three a_i = 2 mod 4, others odd (not 1? include a>=3 odd), a_i<=AMAX, n_other<=NO.
# Record U shape and group by (residue multiset, F); report groups with differing U.
import sys, itertools, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
r=4; AMAX=int(sys.argv[1]); NO=int(sys.argv[2])
mids=[x for x in range(2,AMAX+1) if x%r==2]
others=[x for x in range(3,AMAX+1) if x%2==1]
groups=collections.defaultdict(set); shapes=collections.Counter(); rows=[]
for m in itertools.combinations_with_replacement(mids,3):
    for no in range(NO+1):
        for o in itertools.combinations_with_replacement(others,no):
            a=sorted(m+o)
            D,F,Gam,mu,T6=stats(r,a); U=Uset(r,a)
            isint = U==list(range(1,len(U)+1))
            delta=T6-len(U) if isint else None
            shapes[(isint,delta)]+=1
            res=tuple(sorted(x%r for x in a))
            groups[(res,F)].add(delta)
            rows.append((a,delta,T6,F,mu))
print(shapes)
bad=[(k,v) for k,v in groups.items() if len(v)>1]
print("groups",len(groups),"nonconstant",len(bad))
for k,v in bad[:10]: print(k,v)
import pickle; pickle.dump(rows,open(f'r4_{AMAX}_{NO}.pkl','wb'))
