# Claim C: for w>=0, g=(D+1+w)%3 in {1,2}: e_{w+g}-e_w >= delta(w+g). Find first violation position v=w+g; compare to D/2.
from common import *
from explore_e import eseq, delta_fn
from collections import Counter
worst=Counter(); viol_in_range=[]
for a in box_instances():
    if min(a)<2: continue
    p=[int(x) for x in pprod(a)]; D=len(p)-1; S=sum(1 for x in a if x%3==2)
    e=eseq(p,D+10); dl=delta_fn(S)
    first=None
    for w in range(0,D+5):
        g=(D+1+w)%3
        if g==0: continue
        if e[w+g]-e[w]<dl(w+g):
            first=w+g;break
    # needed range: v < D/2 - 2
    if first is not None and 2*first < D-4: viol_in_range.append((a,first,D))
    worst[(first-D/2) if first is not None else None]+=1
print("violations inside needed range:",len(viol_in_range))
for x in viol_in_range[:20]: print(x)
print("distribution of (first violation v) - D/2:",sorted(worst.items(),key=lambda t:(t[0] is None, t[0]))[:40])
