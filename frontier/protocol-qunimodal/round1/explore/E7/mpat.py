# Pattern of unimodality as a function of m=b-1-F, F=sum floor(a_i/r). Check m<=0 always unimodal; tabulate patterns for m=0..8.
import collections
pat=collections.Counter(); neg_ok=True; ex={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    F=sum(v//r for v in a)
    for b in range(1,61):
        mm=b-1-F
        if mm<=0 and not (m>>(b-1))&1: neg_ok=False
    # pattern for mm=0..8 when b in range
    s=''
    for mm in range(0,9):
        b=mm+1+F
        s+= str((m>>(b-1))&1) if b<=60 else '?'
    pat[(r,s)]+=1; ex.setdefault((r,s),a)
print("all m<=0 unimodal:",neg_ok)
for k in sorted(pat): print(k,pat[k],'e.g.',ex[k])
