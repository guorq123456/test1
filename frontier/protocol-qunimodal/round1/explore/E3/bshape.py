# Shape of the unimodal b-set for each (r,a) in the box: is it {1..B} (initial segment)? Compare B with 1+F.
from load import load
from collections import Counter
recs=load()
FULL=(1<<60)-1
shape=Counter(); excess=Counter(); exc_by_r=Counter(); tot_by_r=Counter()
nonint=[]
for r,a,m in recs:
    if any(x%r==0 for x in a):
        shape['has0, all b' if m==FULL else 'has0, NOT all b']+=1; continue
    # initial segment?
    B=0
    while B<60 and (m>>B)&1: B+=1
    init = (m == (1<<B)-1)
    if not init:
        shape['no0, not initial segment']+=1
        if len(nonint)<10: nonint.append((r,a,[b for b in range(1,61) if (m>>(b-1))&1]))
        continue
    shape['no0, initial segment']+=1
    F=sum(x//r for x in a)
    excess[B-(1+F)]+=1; tot_by_r[r]+=1
    if B>1+F: exc_by_r[r]+=1
print(dict(shape))
print('B-(1+F) distribution (no residue 0, initial segment):',dict(sorted(excess.items())))
print('records with B>1+F by r:',dict(exc_by_r),' totals:',dict(tot_by_r))
for x in nonint: print(x)
