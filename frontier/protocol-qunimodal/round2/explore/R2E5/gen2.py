# fast generation: data2/U_r{r}.txt lines: r s n k F T6 U   (uses T1 for b<=F+1)
import sys,os
from core import Uset_fast
os.makedirs('data2',exist_ok=True)
r=int(sys.argv[1]); kmax=int(sys.argv[2]); nlist=[int(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else None
with open(f'data2/U_r{r}.txt','w') as f:
    for s in range(2,r-1):
        for n in (nlist if nlist else range(0,100)):
            a=n*r+s
            if a>100: break
            for k in range(3,kmax+1):
                U,F,T6=Uset_fast(r,[a]*k,extra=2)
                f.write(f"{r} {s} {n} {k} {F} {T6} {' '.join(map(str,U))}\n"); f.flush()
