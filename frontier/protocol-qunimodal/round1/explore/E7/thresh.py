# Compare threshold B(r,a) (largest b with 1..b all unimodal) with conjectured C=1+sum floor(a_i/r).
import collections
stats=collections.Counter(); ex=collections.defaultdict(list)
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=x[2:2+k]; m=x[2+k]
    B=0
    while B<60 and (m>>B)&1: B+=1
    C=1+sum(ai//r for ai in a)
    kk=len(a)
    key=(r, 'B<C' if B<C else ('B=C' if B==C else 'B>C'))
    stats[key]+=1
    if B!=C and len(ex[key])<8: ex[key].append((a,B,C))
for k in sorted(stats): print(k,stats[k], ex.get(k,''))
