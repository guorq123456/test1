# For each residue-count vector: distribution of unimodal-beyond-threshold masks (incl. mask 0 = conjecture holds)
import sys, itertools, re
from collections import defaultdict, Counter
r=int(sys.argv[1]); kmin=int(sys.argv[2]); kmax=int(sys.argv[3]); A=int(sys.argv[4]); fn=sys.argv[5]
masks=defaultdict(Counter)
for line in open(fn):
    m=re.match(r"U r=(\d+) k=(\d+) F=(\d+) S=(\d+) res=([\d,]+) mask=([0-9a-f]+)",line)
    if not m or int(m.group(1))!=r: continue
    masks[tuple(map(int,m.group(5).split(',')))][int(m.group(6),16)]+=1
tot=Counter()
vals=[x for x in range(2,A+1) if x%r]
for k in range(kmin,kmax+1):
    for a in itertools.combinations_with_replacement(vals,k):
        c=[0]*(r-1)
        for x in a: c[x%r-1]+=1
        tot[tuple(c)]+=1
def S(res): return sum(c*(i) for i,c in enumerate(res))  # residue i+1 contributes i
nd=0
for key in sorted(masks, key=lambda t:(sum(t),t)):
    cm=masks[key]; n0=tot[key]-sum(cm.values())
    desc=", ".join("j<=%d:%d"%(mk.bit_length()-1,cnt) if mk==(1<<mk.bit_length())-1 else "mask%x:%d"%(mk,cnt) for mk,cnt in sorted(cm.items()))
    flag="" if n0==0 and len(cm)==1 else "  <-- residue-dependent only? NO"
    if flag: nd+=1
    print("k=%d res=%s S=%d tot=%d none=%d  %s%s"%(sum(key),key,S(key),tot[key],n0,desc,flag))
print("keys:",len(masks),"non-determined:",nd)
