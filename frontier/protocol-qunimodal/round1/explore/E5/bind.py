# which (B) constraints bind: at failing b where (A) holds, list j=M-r-v and whether T(v)>0, F value, f_j
from load import *
from predF import Fvec
from trunc import lowf
from collections import Counter
for r in range(2,7):
    C=Counter(); ex={}
    for a,mask in load(r):
        F,sig=Fvec(r,a); f=lowf(a,r); D=sum(x-1 for x in a); Q=sum(x//r for x in a)
        for b in range(1,61):
            if (mask>>(b-1))&1: continue
            M=D+1-r*(b-1); m=b-1-Q
            Aok=all(F[v%r]>=0 for v in range(M-r+1,(M+1)//2+1) if 2*v<M)
            if not Aok: continue
            for v in range(M-2*r+1,M-r+1):
                if 2*v>=M: continue
                j=M-r-v; Tv=f[v-r] if v>=r else 0
                if F[v%r]+f[j]-Tv<0:
                    key=(m,j,Tv>0,F[v%r],f[j],Tv)
                    C[key]+=1; ex.setdefault(key,(a,b))
    print("r",r)
    for k_,c in sorted(C.items()): print("   m,j,T>0,F,f_j,T(v):",k_,c,"ex",ex[k_])
