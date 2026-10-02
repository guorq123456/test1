# for each (r,s): does E(0) (n=0 data) equal flat E_inf for all k<=60? report max s with a difference, per r
import glob
from flat import flat_fast
from collections import defaultdict
diff=defaultdict(list)
for f in glob.glob('data/U_r*.txt')+glob.glob('data2/U_r*.txt'):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=x[6:]
        if n!=0: continue
        E=[b-1 for b in U if b>=2]
        if E!=flat_fast(r,s,k): diff[(r,s)].append(k)
for r in range(4,31):
    ss=sorted(s for (rr,s) in diff if rr==r)
    print(r,'s with n=0 != flat:',ss, ' max s/r=%.3f'%(max(ss)/r if ss else 0))
