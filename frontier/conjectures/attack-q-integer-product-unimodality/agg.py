# aggregate NEC lines from c54 output by (k, residue multiset, j=b-F-2) and compare against total number of cases
import sys, itertools, re
from collections import defaultdict
r=int(sys.argv[1]); kmin=int(sys.argv[2]); kmax=int(sys.argv[3]); A=int(sys.argv[4]); fn=sys.argv[5]
cnt=defaultdict(int)
for line in open(fn):
    m=re.match(r"NEC r=(\d+) k=(\d+) a=([\d,]+) b=(\d+)",line)
    if not m or int(m.group(1))!=r: continue
    a=tuple(map(int,m.group(3).split(','))); b=int(m.group(4)); F=sum(x//r for x in a)
    cnt[(len(a),tuple(sorted(x%r for x in a)),b-F-2)]+=1
tot=defaultdict(int)
vals=[x for x in range(2,A+1) if x%r]
for k in range(kmin,kmax+1):
    for a in itertools.combinations_with_replacement(vals,k):
        tot[(k,tuple(sorted(x%r for x in a)))]+=1
for key in sorted(cnt):
    k,res,j=key
    print(k,res,"j=%d"%j,"%d/%d"%(cnt[key],tot[(k,res)]), "FULL" if cnt[key]==tot[(k,res)] else "PARTIAL")
