# class-pair quantities (synthesis Thm 3.1/4.2) for general r, exact python ints
from lib4 import polyA, in_box
def pair_data(r,a):
    assert in_box(r,a)
    c=polyA(a); D=len(c)-1
    F=sum(x//r for x in a)
    cc=c+[0]; dl=[cc[x]-(cc[x-1] if x>=1 else 0) for x in range(D+2)]
    out=[]
    for C in range(1,r):
        if (C-(D+1))%2: continue
        Zs=[];n=0
        while True:
            Z=C+2*r*(n//2) if n%2==0 else 2*r*((n+1)//2)-C
            if Z>D+1: break
            Zs.append(Z); n+=1
        xs=[(D+1-Z)//2 for Z in Zs]; ys=[dl[x] for x in xs]
        Ainf=sum((-1)**i*y for i,y in enumerate(ys))
        A=0; an=[]
        for i,y in enumerate(ys): A+=(-1)**i*y; an.append((-1)**i*A)
        L=len(ys)
        def a_(n,an=an,L=L,Ainf=Ainf):
            if n<0: return 0
            if n<L: return an[n]
            return (-1)**n*Ainf
        def y_(n,ys=ys,L=L): return ys[n] if 0<=n<L else 0
        def x_(n,C=C,D=D):
            Z=C+2*r*(n//2) if n%2==0 else 2*r*((n+1)//2)-C
            return (D+1-Z)//2
        nstar=None
        if Ainf!=0:
            n=0
            while a_(n)>=0: n+=1
            nstar=n
        out.append(dict(C=C,ys=ys,xs=xs,Ainf=Ainf,nstar=nstar,a=a_,y=y_,x=x_,F=F,D=D))
    return out
def S2_from_pairs(r,a):
    P=[p for p in pair_data(r,a) if p['nstar'] is not None]
    Nst=min(p['nstar'] for p in P)
    def G(p,b): return p['a'](b-2)+p['y'](b)
    beta=[]
    for p in P:
        b=(p['F']+1)%2 or 2
        if b==0: b=2
        # first b == F+1 mod 2, b>=1
        b=1 if (p['F']+1)%2==1 else 2
        while G(p,b)>=0: b+=2
        beta.append(b-2)
    return Nst,min(beta)
