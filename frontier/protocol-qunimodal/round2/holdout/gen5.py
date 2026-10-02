# Round-4 holdout (for round-2 conjectures). Window: b in [max(1,B0-5), T6+2] (T6 = proven upper bound on max unimodal b),
# plus 5 random b in [1, D//r+6]. Avoids the window artifact of round 3.
import random, json, sys
from multiprocessing import Pool
sys.path.insert(0,'/root/.qu_hidden'); from gt_big import profile, poly_a
rnd=random.Random(int(sys.argv[1])); out=sys.argv[2]; S=json.loads(sys.argv[3])
def T6(r,a):
    c=poly_a(a); G=[0]*r
    for i,v in enumerate(c): G[i%r]+=v
    mu=r-1
    while mu>0 and G[mu-1]>=G[mu]: mu-=1
    D=sum(x-1 for x in a); return 1+(D+1-2*mu)//r
def mk(cfg):
    r=rnd.choice(cfg['r']); k=rnd.randint(*cfg['k']); lo,hi=cfg['a']; kind=cfg.get('kind','coprime')
    def pick(res=None):
        while True:
            x=rnd.randint(lo,hi)
            if x%r==0: continue
            if res is not None and x%r not in res: continue
            return x
    mid=set(range(2,r-1)); pm={1,r-1}
    if kind=='coprime': a=[pick() for _ in range(k)]
    elif kind=='three_middle': a=[pick(mid) for _ in range(3)]+[pick(pm) for _ in range(k-3)]
    elif kind=='equal_middle': a=[pick(mid)]*k
    elif kind=='small_parts': a=[rnd.randint(2,r-1) for _ in range(k-3)]+[pick() for _ in range(3)]; a=[x for x in a if x%r]
    elif kind=='half': a=[pick({r//2,(r+1)//2}) for _ in range(k)]
    return r,sorted(a)
tuples=[(s,)+mk(cfg) for s,cfg in S.items() for _ in range(cfg['n'])]
def work(t):
    s,r,a=t; D=sum(x-1 for x in a); B0=1+sum(x//r for x in a); t6=T6(r,a); Bmax=D//r+6
    rr=random.Random(hash((r,tuple(a))))
    bs=sorted(set(list(range(max(1,B0-5),min(Bmax,t6+2)+1))+[rr.randint(1,Bmax) for _ in range(5)]))
    return {'stratum':s,'r':r,'a':a,'bs':bs,'T6':t6,'unimodal':profile(r,a,bs)}
with Pool(3) as P: res=P.map(work,tuples,chunksize=2)
from collections import Counter
st=Counter()
with open(out,'w') as f:
    for o in res:
        f.write(json.dumps(o)+'\n'); st[(o['stratum'],'i')]+=len(o['bs']); st[(o['stratum'],'n')]+=o['unimodal'].count(False)
for s in S: print(f"{s:16s} inst {st[(s,'i')]:6d} non-unimodal {st[(s,'n')]:6d}")
