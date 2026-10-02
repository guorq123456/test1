# End-to-end sanity: exact U (Theorem A criterion, lib4.U) has the S2 shape for random fit-box instances, r=4,5,6.
import random, sys
from lib4 import U, in_box
random.seed(int(sys.argv[1])); n=0; bad=0
for it in range(int(sys.argv[2])):
    r=random.choice([4,5,6]); k=random.randint(1,22)
    a=sorted(random.choice([x for x in range(1,4*r) if x%r]) for _ in range(k))
    if not in_box(r,a): continue
    u=U(r,a); n+=1
    B=max(u)
    if not (u==list(range(1,B+1)) or (B>=3 and u==[b for b in range(1,B+1) if b!=B-1])): bad+=1; print(r,a,u)
print("instances",n,"S2 violations",bad)
