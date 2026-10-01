from feats import *
def persist2(b,i,strict=True):
    hts=[0]
    for ch in b: hts.append(hts[-1]+(1 if ch=='1' else -1))
    p=i+1; v=hts[p]
    def go(step):
        mx=v; q=p; tr=True
        while 0<=q+step<len(hts):
            q+=step
            if (hts[q]<v if strict else (hts[q]<=v and abs(q-p)>0 and hts[q]<=v)): tr=False; break
            mx=max(mx,hts[q])
        return mx-v,tr
    (lr,tl),(rr,tr)=go(-1),go(1)
    return lr,rr,tl,tr
FE={}
FE['min']=lambda b,e:F(e,'min')
FE['sum']=lambda b,e:F(e,'sum')
FE['Zsum']=lambda b,e:F(e,'Zsum')
FE['Zmax']=lambda b,e:F(e,'Zmax')
FE['max']=lambda b,e:F(e,'max')
FE['pers']=lambda b,e:G(b,e,'pers')
FE['persL']=lambda b,e:G(b,e,'persL')
FE['persle']=lambda b,e:min(persist2(b,e['i'],False)[:2])
FE['persmax']=lambda b,e:max(persist(b,e['i'])[:2])
FE['persZ']=lambda b,e:(lambda r: min(r[0],r[1]) if not(r[2] or r[3]) else -1)(persist(b,e['i']))
FE['persT']=lambda b,e:(lambda r: min(r[0] if not r[2] else 99, r[1] if not r[3] else 99))(persist(b,e['i']))
FE['ntr']=lambda b,e:(lambda r: r[2]+r[3])(persist(b,e['i']))
FE['depth']=lambda b,e:-(lambda hts:hts[e['i']+1])([0]+list(np.cumsum([1 if c=='1' else -1 for c in b])))
FE['alt']=lambda b,e:G(b,e,'alt')
FE['altmin']=lambda b,e:G(b,e,'altmin')
FE['cd']=lambda b,e:F(e,'cd')
FE['prod']=lambda b,e:F(e,'prod')
FE['absd']=lambda b,e:F(e,'absd')
def units_for(nu,chain):
    U={}
    for W in range(1<<nu):
        b=format(W,f'0{nu}b'); E=edges(b)
        if not E: U[W]=b.count('1')%2; continue
        ks=[tuple(sg*FE[n](b,e) for n,sg in chain) for e in E]; best=max(ks)
        ps={e['i']%2 for e,k in zip(E,ks) if k==best}
        if len(ps)==1: U[W]=ps.pop()
    return U
def feasible(chain,nus=(7,9,11,13)):
    out=[]
    for nu in nus:
        U=units_for(nu,chain); ok=bool(check(nu,U)); out.append(len(U))
        if not ok: return False,out
    return True,out
if __name__=='__main__':
    chain=[]
    while True:
        best=None
        for n in FE:
            for sg in (1,-1):
                if (n,sg) in chain or (n,-sg) in chain: continue
                ok,out=feasible(chain+[(n,sg)])
                if ok:
                    print('  ok',chain+[(n,sg)],out,flush=True)
                    if best is None or out[-1]>best[1][-1]: best=((n,sg),out)
        if best is None or (chain and best[1][-1]<=last): break
        chain.append(best[0]); last=best[1][-1]; print('CHAIN',chain,best[1],flush=True)
