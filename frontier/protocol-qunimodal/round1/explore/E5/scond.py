# reformulation: P unimodal iff S(v)>=S(M-v) for all integers v with 2v<M, M=D+1-r(b-1)
# S(v)=sum_{j>=max(v,0)?..} f_j over j==v mod r, v<=j, 0<=j, 2j<D+1 ; f=Delta A
from load import *
import sys
def Apoly(a):
    c=[1]
    for x in a:
        n=[0]*(len(c)+x-1)
        for i,v in enumerate(c):
            for j in range(x): n[i+j]+=v
        c=n
    return c
def Sfun(a,r):
    A=Apoly(a); D=len(A)-1
    A2=A+[0]; f=[A2[j]-(A2[j-1] if j>0 else 0) for j in range(D+2)]
    def S(v):
        j=v if v>=0 else v%r
        s=0
        while 2*j<D+1:
            s+=f[j]; j+=r
        return s
    return S,D
def uni_via_S(a,r,b):
    S,D=Sfun(a,r); M=D+1-r*(b-1)
    lo=-r*(b-1)-r-2
    bad=[v for v in range(lo, (M+1)//2+1) if 2*v<M and S(v)<S(M-v)]
    return len(bad)==0, bad, M
if __name__=='__main__':
    import random; random.seed(2); mism=0; tot=0
    for r in range(2,7):
        D=load(r)
        for a,m in random.sample(D,150):
            for b in range(1,25):
                ok,_,_=uni_via_S(a,r,b); tot+=1
                if ok!=bool((m>>(b-1))&1): mism+=1
    print("tested",tot,"mismatch",mism)
