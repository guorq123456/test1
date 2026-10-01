# Independent (pure Python) re-computation on structured adversarial families inside the fit box:
#  F1 all-equal a=(x^k), F2 two values (x^i, y^j), F3 ones plus one or two large entries (1^m, x[, y]).
# For every instance in the sufficiency region b<=1+S: unimodality, contested min Delta (Neg>0 positions),
# exact ties; plus first failing b (slack) for multisets with no r|a_i. Cross-checks margins.c numbers.
import sys, collections
from itertools import combinations
def poly(r,a,b):  # same construction as uni_ref.py
    c=[1]
    for A in a:
        n=[0]*(len(c)+A-1)
        for i,v in enumerate(c):
            for j in range(A): n[i+j]+=v
        c=n
    n=[0]*(len(c)+r*(b-1))
    for i,v in enumerate(c):
        for y in range(b): n[i+r*y]+=v
    return n,c
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
def contested(r,A,b,c):
    D=len(A)-1; dA=[(A[m] if m<=D else 0)-(A[m-1] if m>=1 else 0) for m in range(D+2)]
    N=len(c)-1; res=[]
    for j in range(N//2):
        neg=sum(-dA[m] for t in range(b) for m in [j+1-r*t] if 0<=m<=D+1 and dA[m]<0)
        pos=sum(dA[m] for t in range(b) for m in [j+1-r*t] if 0<=m<=D+1 and dA[m]>0)
        assert pos-neg==c[j+1]-c[j]
        if neg>0: res.append((pos-neg,pos,neg,j))
    return res
fams=collections.defaultdict(set)
for k in range(1,9):
    for x in range(1,13): fams['F1_allequal'].add((x,)*k)
for x,y in combinations(range(1,13),2):
    for i in range(1,8):
        for j in range(1,9-i): fams['F2_twovalues'].add(tuple(sorted((x,)*i+(y,)*j)))
for m in range(0,8):
    for x in range(2,13):
        fams['F3_ones_plus_big'].add(tuple(sorted((1,)*m+(x,))))
        if m<=6:
            for y in range(x,13): fams['F3_ones_plus_big'].add(tuple(sorted((1,)*m+(x,y))))
for name in sorted(fams):
    for r in range(2,7):
        inst=fail=ties_bound=ndiv_bound=0; slack=collections.Counter(); minpos=None
        for a in sorted(fams[name]):
            S=sum(x//r for x in a); bound=1+S; div=any(x%r==0 for x in a)
            for b in range(1,bound+1):
                c,A=poly(r,a,b); inst+=1
                if not unimodal(c): fail+=1; print("COUNTEREXAMPLE",r,a,b)
                cs=contested(r,A,b,c)
                if b==bound and not div:
                    ndiv_bound+=1
                    if any(d==0 for d,_,_,_ in cs): ties_bound+=1
                for d,p,n,j in cs:
                    if d>0 and (minpos is None or d<minpos[0]): minpos=(d,a,b,j)
            if not div:
                f=None
                for b in range(bound+1,61):
                    if not unimodal(poly(r,a,b)[0]): f=b;break
                slack[None if f is None else f-bound]+=1
        print(f"{name} r={r} multisets={len(fams[name])} region_instances={inst} failures={fail} nondiv_at_b=bound={ndiv_bound} with_exact_tie={ties_bound} slack_hist={dict(slack)} smallest_positive_contested_Delta={minpos}")
