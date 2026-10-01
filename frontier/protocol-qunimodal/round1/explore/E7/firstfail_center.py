# At the first failing b (b=B+1) of each tuple: number of strict valleys (nd) and offset of the first descent t
# and of the following ascent s from the centre h=floor(N/2).  Also nd distribution at later b.
import collections
first_fail={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    B=0
    while B<60 and (m>>B)&1: B+=1
    first_fail[(r,a)]=B+1
ff=collections.Counter(); later=collections.Counter(); off=collections.Counter(); n=0
for L in open('/tmp/claude-0/qu/explore/E7/viol.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); b,D,R,N,t,s,nd=x[2+k:]
    h=N//2
    if b==first_fail[(r,a)]:
        n+=1; ff[nd]+=1; off[(h-t, s-h if s>=h else 's<h')]+=1
    else: later[(r, min(nd,5))]+=1
print("first-failure instances",n,"valley count distribution",dict(ff))
print("(h-t, s-h) at first failure:",sorted(off.items(),key=str))
print("later b: valley counts (capped at 5) by r:",sorted(later.items()))
