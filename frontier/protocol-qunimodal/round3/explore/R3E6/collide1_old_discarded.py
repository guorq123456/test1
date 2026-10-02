# 3-multisets in [1,M] (no multiple of r) with equal sum, product, residue multiset mod r,
# but different number of parts equal to 1.  Output coll1_r{r}.txt
import sys
from collections import defaultdict
r=int(sys.argv[1]); M=int(sys.argv[2])
d=defaultdict(list)
vals=[x for x in range(1,M+1) if x%r]
for i,x in enumerate(vals):
    for j in range(i,len(vals)):
        y=vals[j]
        for l in range(j,len(vals)):
            z=vals[l]
            d[(x+y+z,x*y*z,tuple(sorted((x%r,y%r,z%r))))].append((x,y,z))
out=open(f'coll1_r{r}.txt','w'); n=0
for key,lst in d.items():
    ones=set(t.count(1) for t in lst)
    if len(ones)>1:
        n+=1; out.write(repr(lst)+'\n')
print(r,n)
