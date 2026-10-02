# Hill-climb for discrepancies between actual low-order g and generic f in the LOW test (b in {T6-1,T6}),
# four-middle instances, k<=19, a_i<=400. Objective 0 <=> LOW_g(b) != LOW_f(b) for some b; then exact U is checked.
import sys, random, json
from math import comb
from core import U
sys.argv += []
seed=int(sys.argv[1]); R=int(sys.argv[2]); iters=int(sys.argv[3])
random.seed(seed)
def tau_of(r,a):
    c=[1]+[0]*(r-1)
    for A in a:
        s=A%r; d=[0]*r
        for i,v in enumerate(c):
            if v:
                for j in range(s): d[(i+j)%r]+=v
        c=d
    return [c[t]-c[t-1] for t in range(r)]
def trunc_g(r,a,L):
    c=[1]+[0]*(L-1)
    for A in a:
        d=[0]*L; s=0
        for t in range(L):
            s+=c[t]
            if t-A>=0: s-=c[t-A]
            d[t]=s
        c=d
    B=[c[j]-(c[j-1] if j else 0) for j in range(L)]
    g=[0]*L
    for i in range(L): g[i]=B[i]+(g[i-r] if i>=r else 0)
    return g
def fgen(r,kp,L):
    e=[comb(i+kp-2,i) if kp>=2 else int(i==0) for i in range(L)]
    f=[0]*L
    for i in range(L): f[i]=e[i]+(f[i-r] if i>=r else 0)
    return f
def margins(r,a):
    a=[x for x in a if x!=1]; kp=len(a)
    D=sum(x-1 for x in a); tau=tau_of(r,a)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
    L=4*r+4; g=trunc_g(r,a,L); f=fgen(r,kp,L)
    out=[]
    for b in (T6-1,T6):
        if b<1: continue
        K=D+1-r*(b+1); m0=max(1,-((K-1)//2))
        def mm(h):
            H=lambda i: h[i] if i>=0 else 0
            v=min(H(K+m)+tau[(-m)%r] for m in range(m0,min(r*b,m0+r)+1))
            if K>=1: v=min(v, tau[0]-(1-h[K]))
            return v
        out.append((mm(g),mm(f)))
    return out
def obj(r,a):
    best=10**9
    for mg,mf in margins(r,a):
        if (mg<0)!=(mf<0): return 0
        best=min(best, max(0,mg+1)+max(0,-mf), max(0,mf+1)+max(0,-mg))
    return best
def valid(r,a):
    return len(a)<=19 and max(a)<=400 and all(x%r for x in a) and sum(1 for x in a if 2<=x%r<=r-2)==4 and all(x%r in (1,r-1) or 2<=x%r<=r-2 for x in a)
def rand_inst(r):
    a=[r*random.choice([0,0,1,2])+random.randint(2,r-2) for _ in range(4)]
    a+=[r*random.randint(0,3)+r-1 for _ in range(random.randint(0,6))]+[r*random.randint(1,3)+1 for _ in range(random.randint(0,4))]
    return sorted(a)
def mutate(r,a):
    a=a[:]; t=random.randint(0,4); i=random.randrange(len(a))
    if t==0: a[i]=max(1,a[i]+r*random.choice([-1,1]))
    elif t==1 and 2<=a[i]%r<=r-2: a[i]=r*(a[i]//r)+random.randint(2,r-2)
    elif t==2: a.append(r*random.randint(0,3)+random.choice([1,r-1]))
    elif t==3 and not (2<=a[i]%r<=r-2): a.pop(i)
    else: a[i]=max(1,a[i]+random.choice([-1,1])*r*random.randint(1,3))
    return sorted(a)
fo=open(f'hill_gen_{seed}.jsonl','w'); found=0
for rr in range(R):
    r=random.randint(5,60)
    a=rand_inst(r)
    while not valid(r,a): a=rand_inst(r)
    cur=obj(r,a)
    for it in range(iters):
        b=mutate(r,a)
        if not valid(r,b): continue
        o=obj(r,b)
        if o<=cur: a,cur=b,o
        if cur==0: break
    if cur==0:
        u,T6,_=U(r,a)
        import rule_gen as RG, rule_simple as RS
        eg=sum(RG.predict(r,a,x)!=(x in u) for x in range(1,T6+3)); es=sum(RS.predict(r,a,x)!=(x in u) for x in range(1,T6+3))
        found+=1; fo.write(json.dumps(dict(r=r,a=a,U=u,T6=T6,err_gen=eg,err_simple=es))+'\n'); fo.flush()
        print('disc',r,a,'U',u[-3:],'T6',T6,'err_gen',eg,'err_simple',es,flush=True)
print('restarts',R,'objective-0 found',found)
