# Directed search for witness pairs with identical Gamma data AND no part equal to 1 (so same k and same
# number of nontrivial parts): X={2,y,z} ~ Y={x,u,v} (equal sum/prod/residues) embedded with extra parts W.
# Prefilter with truncated (A mod q^{3r}) evaluation of rule_simple's LOW; confirm candidates with exact U.
import sys, random, json
from core import U, inv
seed=int(sys.argv[1]); tries=int(sys.argv[2]); rmax=int(sys.argv[3])
random.seed(seed)
trip=[tuple(map(int,l.split())) for l in open('coll2_all.txt')]
cand=[]
for r in range(5,rmax+1):
    for y,z,x,u,v in trip:
        X=(2,y,z); Y=(x,u,v)
        if any(t%r==0 for t in X+Y): continue
        if sorted(t%r for t in X)==sorted(t%r for t in Y): cand.append((r,X,Y))
print('cand',len(cand))
def trunc_prod(a,L):
    c=[1]+[0]*(L-1)
    for A in a:
        d=[0]*L; s=0
        for t in range(L):
            s+=c[t]
            if t-A>=0: s-=c[t-A]
            d[t]=s
        c=d
    return c
def tau_of(r,a):
    c=[1]+[0]*(r-1)
    for A in a:
        s=A%r; d=[0]*r
        for i,v in enumerate(c):
            if v:
                for j in range(s): d[(i+j)%r]+=v
        c=d
    return [c[t]-c[t-1] for t in range(r)]
def lowtr(r,a,b,D,tau,g):
    K=D+1-r*(b+1); G=lambda i: g[i] if i>=0 else 0
    m0=max(1,-((K-1)//2))
    for m in range(m0,min(r*b,m0+r)+1):
        if G(K+m)+tau[(-m)%r]<0: return False
    if K>=1 and 1-g[K]>tau[0]: return False
    return True
def summary(r,a):
    D=sum(x-1 for x in a); tau=tau_of(r,a)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
    L=4*r; A=trunc_prod(a,L+1)
    B=[A[j]-(A[j-1] if j else 0) for j in range(L)]
    g=[0]*L
    for i in range(L): g[i]=B[i]+(g[i-r] if i>=r else 0)
    return T6,tuple(lowtr(r,a,b,D,tau,g) for b in (T6-1,T6) if b>=1)
fo=open(f'emb2f_{seed}.jsonl','w'); found=0; pre=0
for t in range(tries):
    r,X,Y=random.choice(cand)
    mid=lambda s: 2<=s<=r-2
    m=sum(1 for q in X if mid(q%r))
    if m>4: continue
    W=[]
    for _ in range(4-m):
        s=random.randint(2,r-2); W.append(r*random.randint(0,3)+s)
    for _ in range(random.randint(0,10)):
        s=random.choice([1,r-1]); n=random.randint(0 if s==r-1 else 1, 4); W.append(r*n+s)
    a=sorted(list(X)+W); b=sorted(list(Y)+W)
    if len(a)>19 or max(a+b)>400 or 1 in a or 1 in b: continue
    sa=summary(r,a); sb=summary(r,b)
    if sa!=sb:
        pre+=1
        ua=U(r,a)[0]; ub=U(r,b)[0]
        if ua!=ub:
            found+=1; assert inv(r,a)==inv(r,b)
            fo.write(json.dumps(dict(r=r,a=a,b=b,Ua=ua,Ub=ub))+'\n'); fo.flush()
            print(r,a,ua[-2:],'|',b,ub[-2:],flush=True)
print('prefilter hits',pre,'found',found)
