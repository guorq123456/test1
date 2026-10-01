# For first-failure instances (b=B+1), tabulate offsets t-D, t-R, s-t, and N-2t, by r and sign(R-D)
import collections
first_fail={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    B=0
    while B<60 and (m>>B)&1: B+=1
    first_fail[(r,a)]=B+1
cnt=collections.Counter()
for L in open('/tmp/claude-0/qu/explore/E7/viol.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); b,D,R,N,t,s,nd=x[2+k:]
    if b!=first_fail[(r,a)]: continue
    cnt[(r, 'R>=D' if R>=D else 'R<D', 't-min(D,R)=%d'%(t-min(D,R)), 's-t=%d'%(s-t), 'nd=%d'%nd)]+=1
for k in sorted(cnt): print(k,cnt[k])
