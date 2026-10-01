# verify r=3 rule (unimodal iff b <= F+1+2*floor(S/6)) from c54 mode-1 output, counting all enumerated multisets
import re, itertools, sys
from collections import Counter
fn=sys.argv[1]; K=int(sys.argv[2]); A=int(sys.argv[3])
obs=Counter(); bad=0
for line in open(fn):
    m=re.match(r"U r=3 k=(\d+) F=(\d+) S=(\d+) res=([\d,]+) mask=([0-9a-f]+) nonmono=(\d)",line)
    if m:
        S=int(m.group(3)); mask=int(m.group(5),16)
        if mask!=(1<<(2*(S//6)))-1 or m.group(6)!='0': bad+=1; print("BAD",line.strip())
        obs[S]+=1
if re.search("SUFF",open(fn).read()): print("SUFF failure present!"); bad+=1
tot=Counter()
vals=[x for x in range(2,A+1) if x%3]
for k in range(1,K+1):
    for a in itertools.combinations_with_replacement(vals,k):
        S=sum(1 for x in a if x%3==2)
        if S>=6: tot[S]+=1
for S in tot:
    if obs[S]!=tot[S]: bad+=1; print("MISSING",S,obs[S],tot[S])
print("r=3 rule check: multisets with S>=6:",sum(tot.values()),"mismatches:",bad)
