# Analyse box_*.csv (and big_*.txt converted): error counts of closed forms A,B; alternative candidates:
#  P: eventually periodic increments of E (period<=Pmax) along each family;  F1: E=2floor((ck-kappa ln k+beta)/2), beta fitted per family;
#  F2: same with beta fitted per (family, parity of S1).
import sys, math, glob, collections
from family import theory
def odd_top(X): return max(1,2*math.floor((X-1)/2)+1)
def even_top(X): return max(0,2*math.floor(X/2))
rows=[]
for fn in sys.argv[1:]:
    for line in open(fn):
        t=line.strip().split(',')
        r=int(t[0]); block=tuple(map(int,t[1].split('-'))); k=int(t[2]); S1=int(t[3]); eo=int(t[4]); ee=int(t[5])
        XoA,XeA,XoB,XeB=map(float,t[6:10])
        rows.append((r,block,k,S1,eo,ee,XoA,XeA,XoB,XeB))
fam=collections.OrderedDict()
for row in rows: fam.setdefault((row[0],row[1]),[]).append(row)
N=len(rows); eA=eB=0; eAk=collections.Counter(); eBk=collections.Counter(); distB=[]
for row in rows:
    r,block,k,S1,eo,ee,XoA,XeA,XoB,XeB=row
    a=(odd_top(XoA)!=eo)+(even_top(XeA)!=ee); b=(odd_top(XoB)!=eo)+(even_top(XeB)!=ee)
    eA+=a>0; eB+=b>0
    kb='k<=12' if k<=12 else ('13-40' if k<=40 else ('41-90' if k<=90 else '91-140+'))
    if a: eAk[kb]+=1
    if b:
        eBk[kb]+=1
        dd=min(abs(XoB-round((XoB-1)/2)*2-1), abs(XeB-round(XeB/2)*2))
        distB.append((k,round(dd,4)))
kc=collections.Counter('k<=12' if r[2]<=12 else ('13-40' if r[2]<=40 else ('41-90' if r[2]<=90 else '91-140+')) for r in rows)
print('points',N,'families',len(fam),'A-wrong points',eA,'B-wrong points',eB)
print('points by k',dict(kc)); print('A errors by k',dict(eAk)); print('B errors by k',dict(eBk))
print('B errors (k, distance of X to its threshold integer):',distB[:40])
# Candidate P: eventually periodic increments along each family; for each P<=Pmax find least m0 s.t. increments periodic from m0
Pmax=12; nfail=0; tested=0; best=[]
for key,rs in fam.items():
    E=[x[4]-1 for x in rs]
    if len(E)<30: continue
    tested+=1
    d=[E[i+1]-E[i] for i in range(len(E)-1)]
    bestm0=None
    for P in range(1,Pmax+1):
        m0=0
        for i in range(len(d)-P):
            if d[i]!=d[i+P]: m0=i+1
        # periodic from m0 on; demand at least 2 full periods of support in second half
        if m0<=len(d)//2 and len(d)-m0>=3*P:
            bestm0=(P,m0);break
    best.append((key,len(E),bestm0))
    if bestm0 is None: nfail+=1
print('Candidate P (eventually periodic increments, P<=%d, onset in first half): families tested'%Pmax,tested,'not fitted',nfail)
print(' examples fitted:',[b for b in best if b[2] is not None][:8])
# Candidates F1/F2
e1=e2=0; tot=0
for key,rs in fam.items():
    r,block=key; th=theory(r,list(block)); c,ka=th['c'],th['kappa']
    pts=[(x[2],x[3],x[4]-1) for x in rs]
    f=[c*k-ka*math.log(k) for k,_,_ in pts]
    def errs(beta,sel):
        return sum(1 for (k,S1,E),fv in zip(pts,f) if sel(S1) and 2*math.floor((fv+beta)/2)!=E)
    grid=[i/200 for i in range(-1600,1601)]
    b1=min(grid,key=lambda b:errs(b,lambda S:True)); e1+=errs(b1,lambda S:True)
    for par in (0,1):
        sel=lambda S,par=par:S%2==par
        bp=min(grid,key=lambda b:errs(b,sel)); e2+=errs(bp,sel)
    tot+=len(pts)
print('Candidate F1 (one fitted beta per family): errors',e1,'of',tot,'; F2 (beta per family and S1 parity):',e2)
