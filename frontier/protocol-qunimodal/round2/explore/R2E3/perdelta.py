# Per class-pair sets U_delta = {b : A_{b-1}>=0 and A_{b-2}+A_{b-1}+A_b>=0}.  Test:
#  (PD1) each U_delta is all of [1,bmax] or [1,B] or [1,B]\{B-1};  (PD2) finite B_delta == 1+F (mod 2).
import sys, random, itertools
sys.path.insert(0,'.')
from zigzag import ZZ
from tcrit import F_of
from collections import Counter
def shape(S,bmax):
    if S==set(range(1,bmax+1)): return 'all',None
    B=max(S)
    if S==set(range(1,B+1)): return 'int',B
    if S==set(range(1,B+1))-{B-1}: return 'gap',B
    return 'other',B
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(3,14); k=random.randint(1,10)
        a=sorted(random.randint(1,random.choice([r-1,2*r,4*r,60])) for _ in range(k))
        if any(x%r==0 for x in a): continue
        z=ZZ(r,a); F=F_of(r,a); bmax=(z.D+1)//r+6
        for d2 in z.data:
            S={b for b in range(1,bmax+1) if z.Ud(d2,b)}
            sh,B=shape(S,bmax)
            par='' if B is None else ('par_ok' if (B-1-F)%2==0 else 'par_BAD')
            c[(sh,par)]+=1
            if (sh=='other' or par=='par_BAD') and len(ex)<8: ex.append((r,a,d2,sorted(S),F))
    for k_,v in sorted(c.items()): print(k_,v)
    for e in ex: print(e)
