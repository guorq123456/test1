# Aggregate all search outputs into counts (instances, gaps, S2 violations) per approach.
import json,glob,re,collections
res=collections.OrderedDict()
# 1 exhaustive equal family (python big-int)
rows=[json.loads(l) for l in open('fam_equal.out')]
res['equal_all']=(len(rows),sum(r[4]=='gap' for r in rows),sum((not r[3]) or r[9] for r in rows))
# 2 exhaustive multiset sweeps (C int128)
n=g=v=sk=0; jobs=0; pats=collections.Counter()
for f in glob.glob('sweeps/*.txt'):
    t=open(f).read()
    m=re.search(r'inst=(\d+) gap=(\d+) viol=(\d+) beyondT6=(\d+) lowfail=(\d+) short=(\d+) skipped=(\d+)',t)
    if not m: continue
    jobs+=1; n+=int(m[1]); g+=int(m[2]); v+=int(m[3])+int(m[4]); sk+=int(m[7])
    for p in t.split('PATTERNS')[1].split():
        a,b=p.rsplit(':',1); pats[a]+=int(b)
res['sweeps']=(n,g,v); res['sweeps_jobs']=jobs; res['sweeps_skipped_overflow']=sk
# 3 one-change nbhd of equal gaps
L=open('nb_gap.out').read().strip().split('\n'); res['nb1_equalgap']=(len(L),sum(1 for l in L if l.split('|')[1].split()[3]=='1'),sum('VIOL' in l for l in L))
# 4 two-value exhaustive m+n<=14
t=[open(f).read().split() for f in glob.glob('two_*.sum')]; res['two_value']=(sum(int(x[2]) for x in t),sum(int(x[4]) for x in t),sum(int(x[6]) for x in t))
# 5 random families
for f in sorted(glob.glob('rand_*_1.sum')):
    x=open(f).read().split(); res[x[0]]=(int(x[2]),int(x[4]),int(x[8]))
x=open('nb2.sum').read().split(); res['nb2_twochange']=(int(x[2]),int(x[4]),int(x[6]))
x=open('ones.sum').read().split(); res['ones']=(int(x[2]),int(x[4]),int(x[6]))
# 6 hill climbs
for name,pat in [('hill_A',"hill/h_*_A.json"),('hill_B',"hill/h_*_B.json"),('hill3_monot',"hill3/*.json")]:
    ev=0;vi=0
    for f in glob.glob(pat):
        t=open(f).read(); vi+=t.count('VIOL'); ev+=json.loads(t.strip().split('\n')[-1])['evals']
    res[name]=(ev,None,vi)
tot=sum(v[0] for k,v in res.items() if isinstance(v,tuple)); totv=sum(v[2] for k,v in res.items() if isinstance(v,tuple))
for k,v in res.items(): print(k,v)
print('TOTAL evaluations',tot,'violations',totv)
print('sweep U-patterns on (F,T6] (top 25):',pats.most_common(25))
# descent-count diagnostics
for f in ['nn_nbgap.json','nn_two.json']+['nn_rand.jsonl']:
    for l in open(f):
        d=json.loads(l); print('nneg',d['fams'],d['n'],'M2breaks',d['M2_breaks'],'P1breaks',d['P1_breaks'],'min ii-slack',d['best_ii_slack'])
