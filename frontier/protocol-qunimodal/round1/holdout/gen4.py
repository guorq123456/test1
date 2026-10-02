# Round-2 holdout: farther and structurally different than round-1 fit box + round-1 holdout.
# b-window: all b in [max(1,B0-5), min(Bmax, B0+30)] plus 5 random b in [1,Bmax], B0 = 1+sum floor(a_i/r), Bmax = D//r+6
import random, json, sys
from multiprocessing import Pool
sys.path.insert(0,'/root/.qu_hidden'); from gt_big import profile
rnd=random.Random(int(sys.argv[1])); out=sys.argv[2]; S=json.loads(sys.argv[3])
def mk(cfg):
    r=rnd.choice(cfg['r']); k=rnd.randint(*cfg['k']); lo,hi=cfg['a']; kind=cfg.get('kind','coprime')
    def pick(res=None):
        while True:
            x=rnd.randint(lo,hi)
            if x%r==0: continue
            if res is not None and x%r not in res: continue
            return x
    if kind=='coprime': a=[pick() for _ in range(k)]
    elif kind=='pm1': a=[pick({1,r-1}) for _ in range(k)]
    elif kind=='half': a=[pick({r//2, (r+1)//2}) for _ in range(k)]
    elif kind=='equal': a=[pick()]*k
    elif kind=='two': u,v=pick(),pick(); a=[rnd.choice((u,v)) for _ in range(k)]
    elif kind=='onebig': a=[pick() for _ in range(k-1)]+[rnd.randint(10*r, 20*r)|1]
    return r,sorted(a)
tuples=[]
for s,cfg in S.items():
    for _ in range(cfg['n']): tuples.append((s,)+mk(cfg))
def work(t):
    s,r,a=t; D=sum(x-1 for x in a); B0=1+sum(x//r for x in a); Bmax=D//r+6
    bs=sorted(set(list(range(max(1,B0-5),min(Bmax,B0+30)+1))+[random.Random(hash((r,tuple(a)))).randint(1,Bmax) for _ in range(5)]))
    return {'stratum':s,'r':r,'a':a,'bs':bs,'unimodal':profile(r,a,bs)}
with Pool(3) as P: res=P.map(work,tuples,chunksize=4)
from collections import Counter
st=Counter()
with open(out,'w') as f:
    for o in res:
        f.write(json.dumps(o)+'\n'); st[(o['stratum'],'i')]+=len(o['bs']); st[(o['stratum'],'n')]+=o['unimodal'].count(False)
for s in S: print(f"{s:14s} inst {st[(s,'i')]:6d} non-unimodal {st[(s,'n')]:6d}")
