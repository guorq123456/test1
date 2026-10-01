# Base thresholds: for tuples with all a_i < r (a_i>=2), B = max initial unimodal run in b.
import collections
U={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    U[(r,a)]=m
def B_of(m):
    B=0
    while B<60 and (m>>B)&1: B+=1
    return B
for r in range(2,7):
    print("r=",r)
    for (rr,a),m in sorted(U.items()):
        if rr!=r or any(x>=r for x in a): continue
        B=B_of(m); D=sum(x-1 for x in a)
        Us=[b for b in range(1,61) if (m>>(b-1))&1]
        if B>1: print("  E=",a,"D=",D,"B=",B, "extra" if len(Us)!=B else "", Us if len(Us)!=B else "")
