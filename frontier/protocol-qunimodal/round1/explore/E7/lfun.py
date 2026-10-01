# L_n = coefficients of p(q)/(1-q^r) (partial residue sums). X = first n with L_n > L_{n+1}.
# Identity: c_n = L_n - L_{n-rb}. Check: case A (floor(N/2)-1 <= R+r-2): unimodal <=> floor(N/2) <= X.
import collections
def pcoef(a):
    c=[1]
    for A in a:
        n=[0]*(len(c)+A-1)
        for i,v in enumerate(c):
            for j in range(A): n[i+j]+=v
        c=n
    return c
def Lseq(p,r,upto):
    L=[0]*(upto+1)
    for n in range(upto+1):
        L[n]=(p[n] if n<len(p) else 0)+(L[n-r] if n>=r else 0)
    return L
def X_of(r,a):
    p=pcoef(a); D=len(p)-1
    L=Lseq(p,r,D+2*r+2)
    for n in range(len(L)-1):
        if L[n]>L[n+1]: return n,D,L
    return None,D,L
if __name__=='__main__':
    U={}
    for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
        x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
        U[(r,a)]=m
    caseA=0; caseAbad=0; caseB=collections.Counter(); xs=collections.Counter()
    for (r,a),m in U.items():
        X,D,L=X_of(r,a)
        F=sum(v//r for v in a); S=D-r*F
        xs[(r,X-r*F-S)] +=0
        for b in range(1,61):
            R=r*(b-1); N=D+R; h=N//2
            u=(m>>(b-1))&1
            if h-1<=R+r-2:
                caseA+=1
                if u!=(h<=X): caseAbad+=1
            else:
                caseB[u]+=1
    print("caseA instances",caseA,"mismatch",caseAbad,"; caseB instances by unimodal flag",dict(caseB))
