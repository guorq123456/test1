# Compare observed excess = gap-2 (index units) with the heuristic sinusoid/geometric model
# excess_model = 2*min_w [ (ln(pi(1-e^-k)/k) - ln sin(pi w))/k + w/2 ]  (k = kappa at binding pair)
import json,numpy as np,sys
def model(k):
    w=np.linspace(1e-4,1-1e-4,20001)
    return 2*np.min((np.log(np.pi*(1-np.exp(-k))/k)-np.log(np.sin(np.pi*w)))/k+w/2)
L=[json.loads(l) for l in open('survey1.jsonl')]
L=[x for x in L if x['Nstar']>=5 and 'kappa' in x and x['gap']>0 and x['r']>=3000]
obs=np.array([x['gap']-2 for x in L]); mod=np.array([model(x['kappa']) for x in L])
print(len(L),'corr',np.corrcoef(obs,mod)[0,1],'obs mean',obs.mean(),'model mean',mod.mean(),'obs max',obs.max())
for x,o,m in sorted(zip(L,obs,mod),key=lambda t:-t[1])[:8]: print(x['fam'],x['r'],x['k'],x['Nstar'],round(x['kappa'],2),round(o,3),round(m,3))
for kk in [1,2,3,4,5,6,8]: print('kappa',kk,'model excess',round(model(kk),3))
