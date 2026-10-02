# Independent exact verification:
#  (1) brute force: P_b = A(q)*[b]_{q^r} via python-flint exact integer polynomials, unimodality of the full coefficient list;
#  (2) exact class-pair criterion (Thm 3.1/4.2 of synthesis r2) with Python big ints -> N*, beta, U.
import sys, flint
def polyA(a):
    ps=[flint.fmpz_poly([1]*x) for x in a if x>=1]
    while len(ps)>1:
        ps=[ps[i]*ps[i+1] if i+1<len(ps) else ps[i] for i in range(0,len(ps),2)]
    return ps[0]
def brute(r,a,bs,A=None):
    if A is None: A=polyA(a)
    out=[]
    for b in bs:
        Bp=flint.fmpz_poly([1 if (i%r==0) else 0 for i in range(r*(b-1)+1)])
        c=[int(v) for v in (A*Bp).coeffs()]
        i=0;N=len(c)-1
        while i<N and c[i]<=c[i+1]: i+=1
        while i<N and c[i]>=c[i+1]: i+=1
        out.append(i==N)
    return out
def pairs_exact(r,a,A=None):
    if any(x%r==0 for x in a): return None
    if A is None: A=polyA(a)
    al=[int(v) for v in A.coeffs()]; D=len(al)-1
    F=sum(x//r for x in a)
    dl=[al[0]]+[al[i]-al[i-1] for i in range(1,D+1)]+[-al[D]]
    Nst=None; beta=None; per=[]
    for C in range(1,r):
        if (C-(D+1))%2: continue
        y=[];kk=0
        while True:
            Z=(kk//2)*2*r+(C if kk%2==0 else 2*r-C)
            if Z>D+1: break
            y.append(dl[(D+1-Z)//2]); kk+=1
        y+= [0]*8
        As=[];s=0
        for n,v in enumerate(y): s+= v if n%2==0 else -v; As.append(s)
        an=[(As[n] if n%2==0 else -As[n]) for n in range(len(y))]
        ns=next((n for n in range(len(y)) if an[n]<0),None)
        if ns is None: continue
        b=ns+2
        while b<len(y):
            if an[b-2]+y[b]<0: break
            b+=2
        bC=b-2
        per.append((C,ns,bC))
        Nst=ns if Nst is None else min(Nst,ns); beta=bC if beta is None else min(beta,bC)
    return dict(D=D,F=F,Nstar=Nst,beta=beta,per=per)
if __name__=='__main__':
    r=int(sys.argv[1]); a=list(map(int,sys.argv[2:]))
    A=polyA(a); res=pairs_exact(r,a,A)
    per=res.pop('per')
    print('pairs:',res)
    N,B=res['Nstar'],res['beta']
    bs=list(range(1,B+5))
    print('brute U:',[b for b,u in zip(bs,brute(r,a,bs,A)) if u])
    print('pair  U:',[b for b in bs if b<=N or (b>=N+2 and b<=B and (b-N)%2==0)])
