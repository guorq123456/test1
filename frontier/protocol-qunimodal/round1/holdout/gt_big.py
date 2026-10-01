# Exact big-integer ground truth with O(deg) multiplications. profile(r,a,bs) -> list of bools
def poly_a(a):
    c=[1]
    for A in a:
        n=len(c)+A-1; d=[0]*n; s=0
        for t in range(n):
            if t<len(c): s+=c[t]
            if 0<=t-A<len(c): s-=c[t-A]
            d[t]=s
        c=d
    return c
def times_b(c,r,b):
    n=len(c)+r*(b-1); d=[0]*n; L=len(c)
    for t in range(n):
        v=(d[t-r] if t>=r else 0)+(c[t] if t<L else 0)-(c[t-r*b] if 0<=t-r*b<L else 0)
        d[t]=v
    return d
def unimodal(d):
    i=0;N=len(d)-1
    while i<N and d[i]<=d[i+1]: i+=1
    while i<N and d[i]>=d[i+1]: i+=1
    return i==N
def profile(r,a,bs):
    c=poly_a(a); return [unimodal(times_b(c,r,b)) for b in bs]
