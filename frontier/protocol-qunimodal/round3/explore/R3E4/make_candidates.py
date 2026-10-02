# Builds candidates.tsv: every search approach/config tried, number of instances evaluated, S2 failures found
# (the "error count" of the refutation attempt = number of instances where S2 failed; 0 means the candidate
# construction failed to refute), best beta-N*, best gap (S2 failure needs gap>=4, beta-N*>=4).
import json,glob,collections,re
rows=[]
L=[json.loads(l) for l in open('survey1.jsonl')]
by=collections.defaultdict(list)
for x in L: by[x['fam']].append(x)
for f,v in sorted(by.items()):
    rows.append(('survey1:'+f,'random r in {1000..12000}',len(v),sum(not x['S2'] for x in v),max(x['beta']-x['Nstar'] for x in v),max(x['gap'] for x in v)))
def runs(fn,pat):
    out={}
    for l in open(fn):
        out[' '.join(l.split()[:5])]=int(re.search(r'iters (\d+)',l).group(1))
    return out
for prefix,fn in [('hc','hc_runs.txt'),('hc2','hc2_runs.txt'),('hc3','hc3_runs.txt'),('hc4','hc4_runs.txt'),('hc5','hc5_runs.txt')]:
    its=runs(fn,None)
    for g in sorted(glob.glob(prefix+'_*.jsonl')):
        J=[json.loads(l) for l in open(g)]
        fails=sum(1 for j in J if j.get('S2FAIL'))
        J=[j for j in J if not j.get('S2FAIL')]
        key=' '.join(g[len(prefix)+1:-6].split('_'))
        n=next((v for k,v in its.items() if k.replace(' ','_').startswith(g[len(prefix)+1:-6].split('_')[0]+'_'+g[len(prefix)+1:-6].split('_')[1]+'_'+g[len(prefix)+1:-6].split('_')[2])),-1)
        rows.append((prefix+':'+key,'hill-climb',n,fails,max((j['beta']-j['Nstar'] for j in J),default=-1),max((j.get('gap',0) for j in J),default=0)))
D=[json.loads(l) for l in open('design1.jsonl')]
rows.append(('design1:2x(r/2)+small-width+lifted+-1','structured grid',len(D),sum(1 for x in D if x['beta']>=x['Nstar']+4),max(x['beta']-x['Nstar'] for x in D),max(x['gap'] for x in D)))
for f in ['inst_ki_fail_r8595','inst_ki_fail_r12552','inst_ki_fail_r15167_Fodd','inst_ki_fail']:
    rows.append(('r2-reanalysis:'+f,'given',1,0,2 if f!='inst_ki_fail' else 0,0))
with open('candidates.tsv','w') as o:
    o.write('candidate\tkind\tinstances_evaluated\tS2_failures_found(error_count)\tbest_beta_minus_Nstar\tbest_gap\n')
    for r in rows: o.write('\t'.join(map(str,r))+'\n')
print(len(rows),'candidate rows; total instances',sum(max(r[2],0) for r in rows))
