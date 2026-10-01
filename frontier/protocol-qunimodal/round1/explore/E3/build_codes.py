# Compute integer codes of every feature in features.FEATS for every (r,a) record in the box.
import numpy as np, pickle
from load import load
from features import FEATS
recs=load()
n=len(recs)
codes={}
for name,f in FEATS.items():
    d={}; arr=np.empty(n,dtype=np.int64)
    for i,(r,a,m) in enumerate(recs):
        v=f(r,a); arr[i]=d.setdefault(v,len(d))
    codes[name]=arr; print(name,len(d),flush=True)
codes['_r']=np.array([r for r,a,m in recs],dtype=np.int64)
codes['_full']=np.array([hash((r,tuple(x for x in a if x>1))) for r,a,m in recs],dtype=np.int64)
masks=np.array([m for r,a,m in recs],dtype=np.uint64)
pickle.dump((codes,masks),open('codes.pkl','wb'))
