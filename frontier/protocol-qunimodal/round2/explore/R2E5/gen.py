# generate U for all-equal family, middle residue, writes data/U_r{r}.txt lines: r s n k F T6 U
import sys,os
from core import Uset
os.makedirs('data',exist_ok=True)
r=int(sys.argv[1]); kmax=int(sys.argv[2]) if len(sys.argv)>2 else 60
nmax=int(sys.argv[3]) if len(sys.argv)>3 else 99
with open(f'data/U_r{r}.txt','w') as f:
    for s in range(2,r-1):
        for n in range(0,nmax+1):
            a=n*r+s
            if a>100: break
            for k in range(3,kmax+1):
                U,F,T6=Uset(r,[a]*k,extra=2)
                f.write(f"{r} {s} {n} {k} {F} {T6} {' '.join(map(str,U))}\n"); f.flush()
