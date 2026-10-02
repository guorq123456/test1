# rule_gen / rule_simple on four-middle instances with r in [1000,1400] (allowed region (ii)), exact Python ints.
import sys, random
from core import U
import rule_gen as RG, rule_simple as RS
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
err={'gen':0,'simple':0}; inst=0; act=0
for it in range(N):
    r=random.randint(1000,1400)
    mids=[r*random.choice([0,0,1])+random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,4); nm=random.randint(0,8-n1)
    a=sorted(mids+[r*random.randint(1,2)+1 for _ in range(n1)]+[r*random.choice([0,1])+r-1 for _ in range(nm)])
    inst+=1; u,T6,_=U(r,a)
    if u!=list(range(1,T6+1)): act+=1
    for b in range(1,T6+3):
        t=(b in u)
        if RG.predict(r,a,b)!=t: err['gen']+=1
        if RS.predict(r,a,b)!=t: err['simple']+=1
print('inst',inst,'U!=[1,T6]',act,'errors',err)
