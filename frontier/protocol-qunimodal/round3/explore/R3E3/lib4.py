# Exact tools (python big ints). FIT BOX guard included.
def middle_count(r,a): return sum(1 for x in a if 2<=x%r<=r-2)
def in_box(r,a):
    k=len(a)
    if r>=1000: return True
    if r>120 or k>140 or max(a)>400: return False
    res=[x%r for x in a]
    nm=sum(1 for s in res if 2<=s<=r-2)
    if k>=20 and nm in (4,5) and all(s in (1,r-1) for s in res if not 2<=s<=r-2): return False
    if k>=55 and sum(1 for s in res if s==r-1)>50: return False
    if k>=60 and len(set(a))==2 and all(2<=s<=r-2 for s in res): return False
    return True
def polyA(a):
    c=[1]
    for A in a:
        if A<=1: continue
        n=len(c)+A-1; d=[0]*n; s=0
        for t in range(n):
            if t<len(c): s+=c[t]
            if 0<=t-A<len(c): s-=c[t-A]
            d[t]=s
        c=d
    return c
def dseq(c,r,L):
    # d = c*(1-q)/(1-q^r) coefficients 0..L-1
    e=[0]*(L+1)
    for i in range(min(len(c),L+1)): e[i]+=c[i]
    for i in range(min(len(c)+1,L+1)):
        if 1<=i<=len(c): e[i]-=c[i-1]
    d=[0]*L
    for i in range(L): d[i]=e[i]+(d[i-r] if i>=r else 0)
    return d
def U(r,a,bmax=None):
    assert in_box(r,a), "outside fit box"
    if any(x%r==0 for x in a): return None
    c=polyA(a); D=len(c)-1
    if bmax is None: bmax=D//r+3
    L=D+r*bmax+5
    d=dseq(c,r,L)
    res=[]
    for b in range(1,bmax+1):
        N=D+r*(b-1); ok=True
        for n in range(1,N//2+1):
            if d[n]<(d[n-r*b] if n-r*b>=0 else 0): ok=False;break
        if ok: res.append(b)
    return res
