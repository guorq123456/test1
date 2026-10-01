# check (box, r<=6): for residue triples 1<=s1<=s2<=s3<=r-1 with s2>=2,
#   Gamma_{t}-Gamma_{t-1} = s1 - max(0,s1+s3-r) > 0 at t=s2-1, hence mu >= s2-1 and sigma+1-2mu < r
import sys; sys.path.insert(0,'rules')
from common import gamma
bad=0; n=0
for r in range(2,7):
    for s1 in range(1,r):
        for s2 in range(s1,r):
            for s3 in range(s2,r):
                a=[s1,s2,s3]; G=gamma(r,a); sig=s1+s2+s3-3
                mu=r-1
                while mu>0 and G[mu-1]>=G[mu]: mu-=1
                n+=1
                if s2>=2:
                    t=s2-1; d=G[t]-G[t-1]
                    if d!=s1-max(0,s1+s3-r) or d<=0: bad+=1; print("diff mismatch",r,a,d)
                    if mu<t: bad+=1; print("mu<t",r,a)
                if not (sig+1-2*mu<r): bad+=1; print("mA>0",r,a)
print("triples",n,"bad",bad)
