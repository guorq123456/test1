# Classify location of first violation (t = first strict descent followed by ascent; s = first ascent after t)
# relative to D=deg p, R=r(b-1), center N/2.
import collections
first_fail={}  # (r,tuple a) -> B+1
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    B=0
    while B<60 and (m>>B)&1: B+=1
    first_fail[(r,a)]=B+1
allc=collections.Counter(); ffc=collections.Counter(); ex=collections.defaultdict(list)
for L in open('/tmp/claude-0/qu/explore/E7/viol.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); b,D,R,N,t,s,nd=x[2+k:]
    assert 2*t < N
    if R>=D:
        reg = 'R>=D: t<D' if t<D else 'R>=D: D<=t<=R'
    else:
        reg = 'R<D: t<R' if t<R else 'R<D: R<=t<D'
    isff = (b==first_fail[(r,a)])
    allc[(r,reg)]+=1
    if isff:
        ffc[(r,reg)]+=1
        if len(ex[(r,reg)])<6: ex[(r,reg)].append((a,b,D,R,N,t,s,nd))
print("ALL non-unimodal instances by region of first violation:")
for k in sorted(allc): print(' ',k,allc[k])
print("First-failure b=B+1 only:")
for k in sorted(ffc): print(' ',k,ffc[k], ex[k][:4])
