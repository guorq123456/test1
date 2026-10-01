# monotonicity in b: for each tuple (r,a) list set of unimodal b in 1..60; check if initial segment
import collections
nonmono=[]; tot=0; byr=collections.Counter(); allu=0
out=open('/tmp/claude-0/qu/explore/E7/nonmono.txt','w')
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=x[2:2+k]; m=x[2+k]
    tot+=1
    U=[b for b in range(1,61) if (m>>(b-1))&1]
    if len(U)==60: allu+=1
    B=0
    while B<60 and (m>>B)&1: B+=1
    # initial segment iff U == 1..B
    if len(U)!=B:
        nonmono.append((r,a,B,U)); byr[r]+=1
        out.write(f"r={r} a={a} first_fail_b={B+1} unimodal_b={U}\n")
print("tuples",tot,"all-60-unimodal",allu,"nonmonotone",len(nonmono),dict(byr))
for t in nonmono[:60]: print(t)
