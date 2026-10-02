# For each failure instance, randomly redistribute quotients n_i (a_i = r n_i + s_i) keeping
# residues (and multiset) and F fixed; report whether U changes (witness pairs for non-Gamma-determinism).
import json, random, sys, glob
from core import U
random.seed(5)
wit=open('witness_pairs.jsonl','w')
for fn in sorted(glob.glob('fail_*.jsonl')):
    for l in open(fn):
        d=json.loads(l); r=d['r']; a=d['a']; F=d['F']
        res=[x%r for x in a]; k=len(a)
        seen={tuple(d['U'])}
        Us={tuple(d['U']):a}
        for t in range(40):
            # random composition of F into k parts with caps; residue-1 parts need n>=1? (a=1 trivial is fine too)
            caps=[(400-s)//r for s in res]
            n=[0]*k
            rem=F
            idx=list(range(k))
            while rem>0:
                i=random.choice(idx)
                if n[i]<caps[i]: n[i]+=1; rem-=1
            b=sorted(r*n[i]+res[i] for i in range(k))
            u=tuple(U(r,b)[0])
            if u not in Us: Us[u]=b
        if len(Us)>1:
            print(r,'F',F,{str(list(u)[-3:])+'/'+str(len(u)):v for u,v in Us.items()})
            wit.write(json.dumps(dict(r=r,F=F,variants=[[list(u),v] for u,v in Us.items()]))+'\n')
        else:
            print(r,'F',F,'stable',d['U'][-3:])
