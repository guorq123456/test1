# Find pairs of 3-multisets X != Y (elements in [2,M], no multiple of r) with equal sum, equal product,
# equal residue multiset mod r, for given r. Output to coll_r{r}.txt
import sys
from collections import defaultdict
r=int(sys.argv[1]); M=int(sys.argv[2])
d=defaultdict(list)
vals=[x for x in range(2,M+1) if x%r]
for i,x in enumerate(vals):
    for j in range(i,len(vals)):
        y=vals[j]
        for l in range(j,len(vals)):
            z=vals[l]
            key=(x+y+z,x*y*z,tuple(sorted((x%r,y%r,z%r))))
            d[key].append((x,y,z))
out=open(f'coll_r{r}.txt','w'); n=0
for key,lst in d.items():
    if len(lst)>1:
        n+=1; out.write(repr(lst)+'\n')
print(r,n)
