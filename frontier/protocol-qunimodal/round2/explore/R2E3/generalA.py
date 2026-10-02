# Test generalized S2' : for symmetric A (alpha_0>=1), U={b: A(q)[b]_{q^r} unimodal} equals [1,B] or [1,B]\{B-1},
# with B = T6 (mod 2), T6 = 1+floor((D+1-2mu)/r), mu = least t in [0,r-1] with Gamma_t>=...>=Gamma_{r-1}
# (Gamma_t = class-t coefficient sums of A). Families: (L) random symmetric log-concave; (P) products of [a]_q and 1+cq+q^2.
import random, sys, math
from collections import Counter
def mul(p,q):
    c=[0]*(len(p)+len(q)-1)
    for i,x in enumerate(p):
        if x:
            for j,y in enumerate(q): c[i+j]+=x*y
    return c
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
def U_of(A,r,bmax):
    out=[]
    for b in range(1,bmax+1):
        B=[0]*(r*(b-1)+1)
        for y in range(b): B[r*y]=1
        if unimodal(mul(A,B)): out.append(b)
    return out
def T6(A,r):
    D=len(A)-1
    G=[sum(A[t::r]) for t in range(r)]
    mu=next(t for t in range(r) if all(G[s]>=G[s+1] for s in range(t,r-1)))
    return 1+(D+1-2*mu)//r
def divisible_by_r(A,r):
    # A(zeta)=0 for all primitive... test: class sums all equal <=> [r] | A? (equal class sums iff A(w)=0 for all w^r=1,w!=1)
    G=[sum(A[t::r]) for t in range(r)]
    return len(set(G))==1
def shape(U,T):
    if not U: return 'empty'
    B=max(U); S=set(U)
    if S==set(range(1,B+1)): sh='interval'
    elif S==set(range(1,B+1))-{B-1}: sh='gap1'
    else: return 'other'
    return sh+('_par_ok' if (B-T)%2==0 else '_par_BAD')
def randLC(D):
    # symmetric log-concave: log alpha concave; build half of concave increments
    H=D//2
    inc=sorted([random.uniform(0,3) for _ in range(H)],reverse=True)
    la=[0.0]
    for x in inc: la.append(la[-1]+x)
    half=[max(1,int(round(math.exp(v)))) for v in la]
    A=half+half[::-1][(D+1)%2==1 and 1 or 0:] if False else None
    if D%2==0: A=half+half[-2::-1]
    else: A=half+half[::-1]
    return A[:D+1] if len(A)>=D+1 else None
def is_lc(A):
    return all(A[i]*A[i]>=A[i-1]*A[i+1] for i in range(1,len(A)-1))
if __name__=='__main__':
    fam=sys.argv[1]; random.seed(int(sys.argv[2])); N=int(sys.argv[3])
    c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(2,7)
        if fam=='L':
            D=random.randint(2,30); A=randLC(D)
            if A is None or not is_lc(A) or A!=A[::-1]: c['skip']+=1; continue
        else:
            A=[1]
            for _ in range(random.randint(1,4)): A=mul(A,[1]*random.randint(1,9))
            for _ in range(random.randint(1,3)): A=mul(A,[1,random.randint(1,4),1])
        if divisible_by_r(A,r): c['div']+=1; continue
        D=len(A)-1
        U=U_of(A,r,(D+1)//r+4); sh=shape(U,T6(A,r)); c[sh]+=1
        if ('other' in sh or 'BAD' in sh) and len(ex)<6: ex.append((r,A,U,T6(A,r)))
    print(fam,c)
    for e in ex: print(e)
