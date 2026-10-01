# Stage-3 codes: stage-2 residue features + small-factor features + low coefficients of A(q)=prod[a_i]_q.
import numpy as np, pickle
from load import load
recs=load()
c1,masks=pickle.load(open('codes.pkl','rb')); c2,_=pickle.load(open('codes2.pkl','rb'))
out={k:v for k,v in c2.items()}
for k in ['cap_ms','small_ms','mina_nt']: out[k]=c1[k]
def low(a,L):
    c=[1]+[0]*(L-1)
    for x in a:
        n=[0]*L
        for i in range(L):
            s=0
            for j in range(min(x,i+1)): s+=c[i-j]
            n[i]=s
        c=n
    return tuple(c)
for name,Lf in [('Alow_r',lambda r:r),('Alow_2r',lambda r:2*r)]:
    d={}; arr=np.empty(len(recs),dtype=np.int64)
    for i,(r,a,m) in enumerate(recs):
        arr[i]=d.setdefault((r,low([x for x in a if x>1],Lf(r))),len(d))
    out[name]=arr; print(name,len(d),flush=True)
pickle.dump((out,masks),open('codes3.pkl','wb'))
