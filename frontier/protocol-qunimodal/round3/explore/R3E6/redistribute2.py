# Test hypothesis H_res: for four-middle instances with no part equal to 1, U depends only on
# (r, residue multiset, F). Redistribute quotients n_i (a_i = r n_i + s_i) keeping residues, F, and no a_i = 1.
# Uses rule_simple (0 errors so far) as a prefilter on U at b in {T6-1,T6}; confirms differences with exact U.
import sys, random, json
from core import U
import rule_simple as RS, rule_low as RL
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); rlo,rhi=int(sys.argv[3]),int(sys.argv[4])
fo=open(f'red2_{sys.argv[1]}.jsonl','w'); found=0; groups=0
for it in range(N):
    r=random.randint(rlo,rhi)
    mids=[random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,6); nm=random.randint(0,12-n1)
    res=mids+[1]*n1+[r-1]*nm
    k=len(res); caps=[(400-s)//r for s in res]; lows=[1 if s==1 else 0 for s in res]
    F=sum(lows)+random.randint(0,25)
    if F>sum(caps): continue
    def draw():
        n=lows[:]; rem=F-sum(n)
        while rem>0:
            i=random.randrange(k)
            if n[i]<caps[i]: n[i]+=1; rem-=1
        return sorted(r*n[i]+res[i] for i in range(k))
    seen={}
    for t in range(12):
        a=draw()
        if not RL.domain(r,a): break
        D,tau,mu,T6,g=RL._data(r,a)
        key=(T6,)+tuple(RS.predict(r,a,b) for b in (T6-1,T6))
        seen.setdefault(key,a)
    groups+=1
    if len(seen)>1:
        vs=list(seen.values()); us=[U(r,a)[0] for a in vs]
        if len(set(map(tuple,us)))>1:
            found+=1; fo.write(json.dumps(dict(r=r,F=F,variants=list(zip(vs,us))))+'\n'); fo.flush()
            print(r,F,[(a,u[-2:]) for a,u in zip(vs,us)],flush=True)
print('groups',groups,'found',found)
