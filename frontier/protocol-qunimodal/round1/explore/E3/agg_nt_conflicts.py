# List all inconsistent keys of the aggregate key computed after dropping trivial factors a_i=1.
from load import load
from collections import defaultdict
recs=load()
FULL=(1<<60)-1
G=defaultdict(list)
for r,a,m in recs:
    a2=tuple(x for x in a if x>1)
    key=(r,len(a2),tuple(sorted(x%r for x in a2)),sum(x//r for x in a2),sum(x-1 for x in a2))
    G[key].append((a2,m))
for key,mem in sorted(G.items()):
    o=0;an=FULL
    for a2,m in mem: o|=m; an&=m
    cb=o&~an
    for b in range(1,61):
        if (cb>>(b-1))&1:
            yes=sorted(set(a2 for a2,m in mem if (m>>(b-1))&1)); no=sorted(set(a2 for a2,m in mem if not (m>>(b-1))&1))
            print(f'r={key[0]} k\'={key[1]} res={key[2]} F={key[3]} D={key[4]} b={b} (1+F={1+key[3]})')
            print('   unimodal:',yes); print('   not     :',no)
