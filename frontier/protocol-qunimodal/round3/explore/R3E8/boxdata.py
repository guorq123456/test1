# Generate data: random families in the fit box (r<=120,k<=140), exact chain tops and closed-form X (A and B).
# output CSV: r,block,k,S1,e_odd,e_even,XoA,XeA,XoB,XeB
import random, sys
from uinf import uinf
from rule_asym import asym_tops
from variants import tops_B
from boxcheck import allowed
seed=int(sys.argv[1]); nfam=int(sys.argv[2]); rmin=int(sys.argv[3]); rmax=int(sys.argv[4]); out=open(sys.argv[5],'w')
random.seed(seed)
for f in range(nfam):
    r=random.randint(rmin,rmax); p=random.randint(1,4)
    block=[random.randint(1,r-1) for _ in range(p)]
    if not any(2<=x<=r-2 for x in block): continue
    for m in range(1,140//p+1):
        s=block*m; k=len(s)
        if k<3 or not allowed(r,s): continue
        ex=uinf(r,s); A=asym_tops(r,s); B=tops_B(r,s)
        out.write('%d,%s,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f\n'%(r,'-'.join(map(str,block)),k,sum(x-1 for x in s),ex['e_odd'],ex['e_even'],A[0],A[1],B[0],B[1]))
    out.flush()
