"""Is delta = (1-q)prod[a_i]_q log-concave on [0, argmax delta] (the outer tail of e)?  Random fit-box instances r<=120.
Counts violations (exact integer test delta_x^2 >= delta_{x-1} delta_{x+1})."""
import random, sys
from winx import InstX
from box import in_box
import survey2
rng=random.Random(int(sys.argv[1])); n=bad=0; ex=[]
for it in range(int(sys.argv[2])):
    r,a=survey2.gen(rng,False)
    if not in_box(r,a) or any(x%r==0 for x in a): continue
    I=InstX(r,a); d=I.delta; p=max(range(len(d)),key=lambda x:d[x]); n+=1
    v=[x for x in range(1,p) if d[x]*d[x]<d[x-1]*d[x+1]]
    if v: bad+=1; ex.append((r,len(a),v[:3],p))
print("instances",n,"with a log-concavity violation of delta on [0,argmax]",bad, ex[:5])
