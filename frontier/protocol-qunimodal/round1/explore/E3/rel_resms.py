# Key (r, residue multiset of nontrivial a_i, d=b-1-F): list conflicts, and the distribution of the
# set of unimodal d>=1 for records without residue 0.
from load import load
from collections import defaultdict, Counter
recs=load()
G=defaultdict(lambda: defaultdict(set))   # key -> d -> set of outcomes
Ex=defaultdict(set)
for r,a,m in recs:
    a2=tuple(x for x in a if x>1); res=tuple(sorted(x%r for x in a2)); F=sum(x//r for x in a2)
    if 0 in res: continue
    for b in range(1,61):
        d=b-1-F; u=(m>>(b-1))&1
        G[(r,res)][d].add(u)
        if d>=1 and u: Ex[(r,res)].add(d)
nconf=0
for key,dd in G.items():
    for d,s in dd.items():
        if len(s)>1:
            nconf+=1; print('conflict',key,'d=',d)
print('conflicts',nconf)
C=Counter((k[0],tuple(sorted(v))) for k,v in Ex.items())
allkeys=Counter(k[0] for k in G)
print('residue-multiset keys (no 0) per r:',dict(allkeys))
for (r,s),c in sorted(C.items()): print('r',r,'unimodal d>=1 set (union over members)',s,'#res multisets',c)
