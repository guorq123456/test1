# Generic symmetric A with (E) e unimodal on positive half and (CU) folded A symmetric-decreasing on Z_r about D/2 or D/2+r/2.
# Question: does U = [1,B_pos] or [1,B_pos]\{B_pos-1} hold for such A (i.e. are (E)+(CU) enough for S2-shape)?
import random, sys
from collections import Counter
from generalA import mul, unimodal, U_of
def randA(D,mode):
    # build d on m=0..H-1 unimodal, d_0=1 ; A = cumulative sums, symmetric
    H=(D+1)//2 + (0 if (D+1)%2==0 else 1)
    p=random.randint(0,H-1); vals=[0]*H; v=1; vals[0]=1
    for m in range(1,p+1): v+=random.randint(0,mode); vals[m]=v
    for m in range(p+1,H): v=max(0,v-random.randint(0,mode)); vals[m]=v
    d=[0]*(D+2)
    for m in range(H): d[m]=vals[m]; d[D+1-m]=-vals[m]
    if (D+1)%2==0: d[(D+1)//2]=0
    A=[];s=0
    for m in range(D+1): s+=d[m]; A.append(s)
    assert A==A[::-1] and s+d[D+1]==0
    return A
def cu_center(A,r):
    D=len(A)-1; G=[sum(A[t::r]) for t in range(r)]
    res=[]
    for c2 in (D, D+r):   # centre c = c2/2
        ok=True
        # symmetric decreasing about c: for t, distance dist(t)=circular |t-c|; G nonincreasing in dist
        pts=[(min(abs(2*t-c2)%(2*r), (2*r-abs(2*t-c2)%(2*r))), G[t]) for t in range(r)]
        pts.sort()
        for (x1,g1),(x2,g2) in zip(pts,pts[1:]):
            if x2>x1 and g2>g1: ok=False
            if x2==x1 and g2!=g1: ok=False
        if ok: res.append(c2)
    return res
def Bpos_of(A,r):
    D=len(A)-1
    d=[A[0]]+[A[m]-A[m-1] for m in range(1,D+1)]+[-A[D]]
    L=D+2+2*r; g=[0]*L
    for n in range(L): g[n]=(d[n] if n<=D+1 else 0)+(g[n-r] if n>=r else 0)
    istar=next((i for i in range(L) if g[i]<0),None)
    if istar is None: return None
    b=1
    while D+r*b<2*istar: b+=1
    return b
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(2,7); D=random.randint(3,36); A=randA(D,random.randint(1,4))
        cs=cu_center(A,r)
        if not cs: c['noCU']+=1; continue
        bp=Bpos_of(A,r)
        if bp is None: c['div']+=1; continue
        U=U_of(A,r,(D+1)//r+4)
        S=set(U); full=set(range(1,bp+1))
        sh='S2shape' if (S==full or S==full-{bp-1}) else 'FAIL'
        c[sh]+=1
        if sh=='FAIL' and len(ex)<6: ex.append((r,A,U,bp,cs))
    print(c)
    for e in ex: print(e)
