# Records (no residue 0) whose unimodal b-set is not an initial segment {1..B}: distribution by r, k'.
from load import load
from collections import Counter
recs=load(); C=Counter(); pats=Counter()
for r,a,m in recs:
    if any(x%r==0 for x in a): continue
    B=0
    while B<60 and (m>>B)&1: B+=1
    if m!=(1<<B)-1:
        a2=tuple(x for x in a if x>1); F=sum(x//r for x in a)
        C[(r,len(a2))]+=1
        pats[tuple(b-1-F for b in range(1,61) if (m>>(b-1))&1)]+=1
print('non-initial records by (r,k\'):',dict(C))
print('patterns of unimodal b-(1+F):',dict(pats))
