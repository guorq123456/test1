# Distribution of the unimodal-b set (pattern over b=1..8) for base tuples (all 2<=a_i<r), and for all tuples by (B-F)
import collections
U={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    U[(r,a)]=m
pat=collections.Counter()
for (r,a),m in U.items():
    if any(x>=r for x in a): continue
    s=''.join(str((m>>i)&1) for i in range(10))
    pat[(r,s)]+=1
for k in sorted(pat): print(k,pat[k])
print("--- all tuples: B-F (F=sum floor(a_i/r)) distribution ---")
c2=collections.Counter()
for (r,a),m in U.items():
    B=0
    while B<60 and (m>>B)&1: B+=1
    F=sum(x//r for x in a)
    c2[(r,B-F)]+=1
for k in sorted(c2): print(k,c2[k])
