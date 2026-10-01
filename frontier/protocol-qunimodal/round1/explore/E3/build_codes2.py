# Codes for stage-2 features, merged into codes2.pkl together with selected stage-1 features.
import numpy as np, pickle
from load import load
from features2 import FEATS2
recs=load()
codes,masks=pickle.load(open('codes.pkl','rb'))
keep=['has0','kn','nnzres','sumres','sumsqres','maxres','minres_nz','nbig','Dmodr','res_ms_nt']
out={k:codes[k] for k in keep}; out['_r']=codes['_r']
for name,f in FEATS2.items():
    d={}; arr=np.empty(len(recs),dtype=np.int64)
    for i,(r,a,m) in enumerate(recs):
        arr[i]=d.setdefault(f(r,a),len(d))
    out[name]=arr; print(name,len(d),flush=True)
pickle.dump((out,masks),open('codes2.pkl','wb'))
