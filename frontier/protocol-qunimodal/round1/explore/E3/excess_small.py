# For small k' (nontrivial factors) list the excess e=B-(1+F) for r=3..6, no residue 0.
from load import load
from collections import defaultdict
recs=load()
for r in range(3,7):
  for kk in (2,3):
    rows=defaultdict(list)
    for rr,a,m in recs:
        if rr!=r: continue
        a2=tuple(x for x in a if x>1)
        if len(a2)!=kk or len(a2)!=len(a) or any(x%r==0 for x in a2): continue
        B=0
        while B<60 and (m>>B)&1: B+=1
        F=sum(x//r for x in a2)
        e=B-1-F if m==(1<<B)-1 else 'NI'
        rows[tuple(sorted(x%r for x in a2))].append((a2,e))
    print(f'r={r} k\'={kk}')
    for res,L in sorted(rows.items()):
        es=sorted(set(e for _,e in L),key=str)
        pos=[a for a,e in L if e!=0]
        print('  res',res,'excess values',es,' #e!=0:',len(pos),'of',len(L),' examples e!=0:',pos[:6])
