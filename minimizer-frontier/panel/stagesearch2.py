# faster staged-rule search with cached edge features; 3 feature stages each followed by majority, then centre, then rc fallback
from stages import *
from fastex import fexcess
import itertools, pickle
POOL=['pers','min','sum','centre','alt','altmin','persL','Zsum','Tmin','persmax','depth','ntr','max','absd','cd','Zmax']
def rcw(b): return b[::-1].translate(str.maketrans('01','10'))
CACHE={}
def cache(nu):
    if nu in CACHE: return CACHE[nu]
    data=[]
    for W in range(1<<nu):
        b=format(W,f'0{nu}b'); E=edges(b)
        if not E: data.append(('base',b.count('1')%2,int(rcw(b),2))); continue
        par=np.array([e['i']%2 for e in E]); X={n:np.array([FE[n](b,e) for e in E],dtype=float) for n in POOL}
        data.append(('e',par,X,int(rcw(b),2)))
    CACHE[nu]=data; return data
def decide_c(d,stages):
    par,X=d[1],d[2]; sel=np.ones(len(par),bool)
    for st in stages:
        if st=='maj':
            o=par[sel].sum(); ev=sel.sum()-o
            if o!=ev: return int(o>ev)
        else:
            n,sg=st; v=sg*X[n]; v=np.where(sel,v,-1e9); sel=v==v.max()
            ps=set(par[sel])
            if len(ps)==1: return ps.pop()
    return None
def build_h(nu,stages):
    data=cache(nu); h=np.full(1<<nu,-1,dtype=np.int64)
    for W,d in enumerate(data):
        if h[W]>=0: continue
        if d[0]=='base': h[W]=d[1]; continue
        v=decide_c(d,stages); r=d[3]
        if v is None: v=0
        h[W]=v; h[r]=1-v
    return h
def prof(stages,nus): return [fexcess(build_h(nu,stages),nu) for nu in nus]
if __name__=='__main__':
    keys=[(n,s) for n in POOL for s in (1,-1)]
    res=[]
    for k1 in keys:
        for k2 in keys:
            st=[k1,'maj',k2,'maj',('centre',1)]
            p=prof(st,(5,7,9))
            if p[0]==0 and p[1]==0: res.append((p,st))
    print('2-stage candidates with 0 at 5,7:',len(res),flush=True)
    res2=[]
    for p,st in res:
        q=prof(st,(9,11)); res2.append((q,st))
    res2.sort(key=lambda r:(r[0][0],r[0][1]))
    for q,st in res2[:15]: print(q,st,flush=True)
    pickle.dump(res2,open('stage2_res.pkl','wb'))
