# Generate exhaustive sweep jobs: for each r in 4..30, k>=3, largest vmax (<=100) with #multisets <= CAP
from math import comb
import sys
CAP=int(sys.argv[1]) if len(sys.argv)>1 else 3_000_000
jobs=[]
for r in range(4,31):
    for k in range(3,41):
        best=None
        for vmax in range(3,101):
            n=sum(1 for v in range(1,vmax+1) if v%r)
            if comb(n+k-1,k)<=CAP: best=vmax
            else: break
        if best is None or best<3: continue
        # need at least 3 middle values possible
        if not any(2<=v%r<=r-2 for v in range(1,best+1)): continue
        jobs.append((r,k,1,best))
for j in jobs: print(*j)
