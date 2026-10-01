# monotonicity in b of unimodality, and critical B*
from load import *
for r in range(2,7):
    D=load(r); nonmono=0; full=0; ex=[]
    for a,m in D:
        S=uniset(m); B=max(S)
        if S!=list(range(1,B+1)): nonmono+=1; ex.append((a,S)) 
        if B==60: full+=1
    print(r,len(D),"nonmonotone",nonmono,"B*=60:",full, ex[:3])
