# Compare true threshold B with case-A prediction B_A = 1+floor((2X+1-D)/r); classify first failing b as case A or B
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import X_of
cnt=collections.Counter(); ex=collections.defaultdict(list)
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    X,D,L=X_of(r,a)
    B=0
    while B<60 and (m>>B)&1: B+=1
    BA=1+(2*X+1-D)//r
    b=B+1; R=r*(b-1); h=(D+R)//2
    case='A' if h<=R+r-1 else 'B'
    F=sum(v//r for v in a)
    key=(r,case,'B==BA' if B==BA else ('B<BA' if B<BA else 'B>BA'), 'BA-F=%d'%(BA-F))
    cnt[key]+=1
    if len(ex[key])<5: ex[key].append((a,D,X,B,BA))
for k in sorted(cnt): print(k,cnt[k],ex[k][:3])
