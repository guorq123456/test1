# Near-miss ranking: for the 300 highest-gap resolved survey instances (+ r2 KI-fail instances) compute the
# failure margin (log ratio; S2 fails iff >=0) and margin in level units (margin/kappa).
import sys,json; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import margin
L=[json.loads(l) for l in open('survey1.jsonl')]
L=[x for x in L if x['Nstar']>=3 and x['gap']>0]
L.sort(key=lambda x:-x['gap']); L=L[:300]
for f in ['inst_ki_fail_r8595.txt','inst_ki_fail_r12552.txt','inst_ki_fail_r15167_Fodd.txt','inst_ki_fail.txt']:
    v=list(map(int,open('/tmp/claude-0/qu/synth/r2/'+f).read().split())); L.append(dict(fam='r2:'+f,r=v[1],a=v[2:]))
res=[]
for x in L:
    m,info=margin(x['r'],x['a'])
    if m is None or 'kappa' not in info: continue
    res.append((m/info['kappa'],m,info['kappa'],x['fam'],x['r'],len(x['a']),info['Nstar'],info['beta'],info['gap'],info['Cworst'],x['a']))
res.sort(key=lambda t:-t[0])
print('n',len(res),'S2 fails',sum(1 for t in res if t[7]>=t[6]+4))
for t in res[:10]: print('lev %.3f m %.2f kap %.2f'%t[:3],t[3:10],t[10][:6])
json.dump([list(t[:10])+[t[10]] for t in res[:10]],open('nearmiss_top.json','w'))
