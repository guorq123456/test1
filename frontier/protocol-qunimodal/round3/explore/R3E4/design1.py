# Designed family (sharp tau profile): two parts with residue ~r/2 (triangle-wave Gamma), m parts with small
# residue s or r-s (sharpness-preserving), plus lifted residue +-1 parts for depth. Reports N*, beta, gap, margin, kappa.
import sys,json,random; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import margin
random.seed(3); out=open('design1.jsonl','w'); n=0; fails=0
for r in [2000,5000,10000]:
  for m in [2,3,4]:
    for s in [2,3,10,r//20]:
      for npm in [0,5,20]:
        for lift in [1,2]:
          a=[r//2+1+lift*r, r//2-1+lift*r]+[ (s if random.random()<0.5 else r-s)+lift*r for _ in range(m)]+[random.choice([1,-1])+(lift+1)*r for _ in range(npm)]
          if any(x%r==0 for x in a): continue
          mg,x=margin(r,a)
          if mg is None: continue
          n+=1; fails+= (not x['S2'])
          out.write(json.dumps(dict(r=r,m=m,s=s,npm=npm,lift=lift,Nstar=x['Nstar'],beta=x['beta'],gap=x['gap'],margin=mg,kappa=x.get('kappa'),a=sorted(a)))+'\n')
print('instances',n,'S2 fails',fails)
import collections
L=[json.loads(l) for l in open('design1.jsonl')]
L.sort(key=lambda x:-x['margin'])
for x in L[:6]: print({k:x[k] for k in ['r','m','s','npm','lift','Nstar','beta','gap','margin','kappa']})
