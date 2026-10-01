# Boundary Lemma: for z = w mod 3, 0<=w<z, z+w in {D-3,D-4}: e_z - e_w >= 0. Report min slack per class of p.
from common import *
from explore_e import eseq
from collections import defaultdict
minsl=defaultdict(lambda:10**18); argmin={}
zero_cases=[]
for a in box_instances():
    if min(a)<2: continue
    p=[int(x) for x in pprod(a)]; D=len(p)-1
    e=eseq(p,D+10)
    for sm in (D-3,D-4):
        for w in range(0,sm//2+1):
            z=sm-w
            if z<=w or (z-w)%3: continue
            sl=e[z]-e[w]
            key=len(a)
            if sl<minsl[key]: minsl[key]=sl; argmin[key]=(a,z,w,D)
            if sl<0: print("VIOLATION",a,z,w)
            if sl==0 and len(a)>=3: zero_cases.append((a,z,w,D))
for k in sorted(minsl): print(k,minsl[k],argmin[k])
print("zero-slack cases with k>=3:",len(zero_cases))
for x in zero_cases[:15]: print(x)
