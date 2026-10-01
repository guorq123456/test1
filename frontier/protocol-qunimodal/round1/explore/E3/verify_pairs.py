# Re-verify every aggregate-statistic collision pair with the ground-truth checker (exact __int128 arithmetic).
# Aggregate key: (r, k, b, multiset of a_i mod r, F=sum floor(a_i/r), D=sum(a_i-1)).
from load import load
from collections import defaultdict
import subprocess
recs=load(); FULL=(1<<60)-1
G=defaultdict(list)
for r,a,m in recs:
    G[(r,len(a),tuple(sorted(x%r for x in a)),sum(x//r for x in a),sum(x-1 for x in a))].append((a,m))
pairs=[]
for key,mem in G.items():
    for b in range(1,61):
        ys=[a for a,m in mem if (m>>(b-1))&1]; ns=[a for a,m in mem if not (m>>(b-1))&1]
        if ys and ns: pairs.append((key[0],ys[0],ns[0],b))
inp=''.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}\n" for r,y,n,b in pairs for a in (y,n))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()
ok=all(out[2*i]=='1' and out[2*i+1]=='0' for i in range(len(pairs)))
print('collision keys:',len(pairs),' each witnessed by a pair re-checked with uni:',ok)
with open('collision_pairs.txt','w') as f:
    for r,y,n,b in pairs:
        f.write(f"r={r} b={b} unimodal a={y} | not unimodal a={n}\n")
print('smallest pair by k then sum:',min(pairs,key=lambda p:(len(p[1]),sum(p[1])+sum(p[2]),p[3])))
