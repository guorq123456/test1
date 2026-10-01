# Smallest number k' of nontrivial factors (a_i>1) for which some (r,a,b) in the box, with no r|a_i,
# is unimodal although b > 1+F; plus counts of such instances per r.
from load import load
from collections import defaultdict
recs=load(); mink={}; cnt=defaultdict(int); ex={}
for r,a,m in recs:
    if 1 in a: continue   # count each polynomial once (trivial factors removed)
    if any(x%r==0 for x in a): continue
    F=sum(x//r for x in a)
    for b in range(F+2,61):
        if (m>>(b-1))&1:
            cnt[r]+=1
            if r not in mink or len(a)<mink[r]: mink[r]=len(a); ex[r]=(a,b)
print('min k\' with unimodal b>1+F (no r|a_i):',mink)
print('example at min k\':',ex)
print('# instances (a without 1s) unimodal with b>1+F and no r|a_i, by r:',dict(cnt))
