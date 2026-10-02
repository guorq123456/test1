# Split Thm A into Pos(b): g_i>=0 for all i<=min(N/2, rb-1)  and Cmp(b): g_i>=g_{i-rb} for rb<=i<=N/2.
# Pos(b) <=> b <= B_pos := largest b with D+r(b-1) < 2 i*, i* = least i with g_i<0.
# Report: is B_pos == 1+F (mod 2)?  how does B*=max U compare with B_pos?
import sys, random, itertools
sys.path.insert(0,'.')
from tcrit import poly_a, F_of
from s2check import Uset
from collections import Counter
def gseq(a,r):
    al=poly_a(a); D=len(al)-1
    d=[al[0]]+[al[m]-al[m-1] for m in range(1,D+1)]+[-al[D]]
    L=D+2+2*r; g=[0]*L
    for n in range(L): g[n]=(d[n] if n<=D+1 else 0)+(g[n-r] if n>=r else 0)
    return g,D
def Bpos(a,r):
    g,D=gseq(a,r)
    istar=next(i for i in range(len(g)) if g[i]<0)
    b=1
    while D+r*b < 2*istar: b+=1   # b+1 still ok?  condition for b: D+r(b-1)<2i*
    return b,istar,D
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(2,12); k=random.randint(1,9)
        a=sorted(random.randint(1,random.choice([r-1,2*r,4*r,60])) for _ in range(k))
        a=[x for x in a if x>=1]
        if any(x%r==0 for x in a) or max(a)>100: continue
        U,t=Uset(r,a); F=F_of(r,a); Bs=max(U)
        bp,istar,D=Bpos(a,r)
        key=('Bpos_par_ok' if (bp-1-F)%2==0 else 'Bpos_par_BAD', 'B*==Bpos' if Bs==bp else ('B*<Bpos' if Bs<bp else 'B*>Bpos??'))
        c[key]+=1
        if key[0].endswith('BAD') and len(ex)<5: ex.append((r,a,U,F,bp))
    for k_,v in sorted(c.items()): print(k_,v)
    for e in ex: print(e)
