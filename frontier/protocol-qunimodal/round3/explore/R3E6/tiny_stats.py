# How often is the correction active (U != [1,T6]) in the tiny-part sampler, and how often does
# the actual g differ from generic f on the window used by LOW at b in {T6-1,T6}?
import random
from core import U
import rule_low as RL, rule_gen as RG
random.seed(7); act=0; inst=0; gdiff=0
for it in range(500):
    r=random.randint(10,60)
    nt=random.randint(1,4)
    mids=[random.randint(2,8) for _ in range(nt)]+[r*random.randint(0,(400-r)//r)+random.randint(2,r-2) for _ in range(4-nt)]
    n1=random.randint(0,6); nm=random.randint(0,14-n1)
    ext=[r*random.randint(1,(400-1)//r)+1 for _ in range(n1)]+[r*random.choice([0,0,1,random.randint(0,(400-r+1)//r)])+r-1 for _ in range(nm)]
    a=sorted(mids+ext)
    if any(x%r==0 for x in a) or sum(1 for x in a if 2<=x%r<=r-2)!=4 or max(a)>400: continue
    inst+=1; u,T6,_=U(r,a)
    if u!=list(range(1,T6+1)): act+=1
    D,tau,mu,T6b,g=RL._data(r,a); f=RG._f(r,len([x for x in a if x!=1]),5*r)
    if g[:3*r]!=f[:3*r]: gdiff+=1
print('inst',inst,'U!=[1,T6]',act,'g!=f on [0,3r)',gdiff)
