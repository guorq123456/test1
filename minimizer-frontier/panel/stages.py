# staged rule: T = all rising edges; for each stage key: T = argmax_key(T); if majority parity of T is strict -> answer.
from greedy import *
FE['centre']=lambda b,e: -abs(e['i']-(len(b)-2)/2)
FE['Tmin']=lambda b,e:F(e,'Tmin'); FE['Zmin']=lambda b,e:F(e,'Zmin'); FE['Tsum']=lambda b,e:F(e,'Tsum')
FE['Tmax']=lambda b,e:F(e,'Tmax'); FE['Zabsd']=lambda b,e:F(e,'Zabsd')
FE['one']=lambda b,e:0
def decide(b,stages,majority=True):
    E=edges(b)
    if not E: return b.count('1')%2
    T=E
    for st in stages:
        if st!='maj':
            n,sg=st; ks=[sg*FE[n](b,e) for e in T]; best=max(ks); T=[e for e,k in zip(T,ks) if k==best]
            ps={e['i']%2 for e in T}
            if len(ps)==1: return ps.pop()
        else:
            o=sum(e['i']%2 for e in T); ev=len(T)-o
            if o!=ev: return int(o>ev)
    return None
def units_st(nu,stages):
    U={}
    for W in range(1<<nu):
        v=decide(format(W,f'0{nu}b'),stages)
        if v is not None: U[W]=v
    return U
def feas(stages,nus=(5,7,9,11,13)):
    out=[]
    for nu in nus:
        U=units_st(nu,stages); ok=bool(check(nu,U)); out.append(len(U))
        if not ok: return False,out
    return True,out
if __name__=='__main__':
    base=[('pers',1),'maj']
    for n in FE:
        for sg in (1,-1):
            for tail in ([],['maj']):
                st=base+[(n,sg)]+tail
                ok,out=feas(st)
                if ok: print(st,out,flush=True)
