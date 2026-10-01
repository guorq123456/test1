from satscore import *
def altseg(b,i):
    """maximal alternating segment containing i,i+1: (L,R,len, truncL, truncR)"""
    L=i
    while L>0 and b[L-1]!=b[L]: L-=1
    R=i+1
    while R<len(b)-1 and b[R+1]!=b[R]: R+=1
    return L,R,R-L+1,L==0,R==len(b)-1
def persist(b,i):
    """valley at the rising edge i (walk min at position i+1 in heights). returns (left rise, right rise, truncL, truncR)"""
    hts=[0]
    for ch in b: hts.append(hts[-1]+(1 if ch=='1' else -1))
    p=i+1; v=hts[p]
    # left: max height before reaching strictly lower
    mx=v; q=p; tl=True
    while q>0:
        q-=1
        if hts[q]<v: tl=False; break
        mx=max(mx,hts[q])
    lr=mx-v
    mx=v; q=p; tr=True
    while q<len(hts)-1:
        q+=1
        if hts[q]<v: tr=False; break
        mx=max(mx,hts[q])
    rr=mx-v
    return lr,rr,tl,tr
def G(b,e,name):
    i=e['i']
    if name=='alt': return altseg(b,i)[2]
    if name=='altZ':
        L,R,n,tl,tr=altseg(b,i); return n if not (tl or tr) else 0
    if name=='altT':
        L,R,n,tl,tr=altseg(b,i); return n+100*(tl+tr)
    if name=='altmin':  # min of alternating extent left/right of the edge
        L,R,n,tl,tr=altseg(b,i); return min(i-L,R-i-1)
    if name=='pers':
        lr,rr,tl,tr=persist(b,i); return min(lr,rr)
    if name=='persL': lr,rr,tl,tr=persist(b,i); return lr+rr
    return F(e,name)
if __name__=='__main__':
    cands=['alt','altZ','altT','altmin','pers','persL','sum','Zsum','Tsum']
    for nm in cands:
        for sg in (1,-1):
            for prim in ('min','none'):
                if prim=='min': key=lambda b,e,nm=nm,sg=sg:(F(e,'min'),sg*G(b,e,nm))
                else: key=lambda b,e,nm=nm,sg=sg:sg*G(b,e,nm)
                out=[]
                for nu in (7,9,11,13):
                    U={}
                    for W in range(1<<nu):
                        b=format(W,f'0{nu}b'); E=edges(b)
                        if not E: U[W]=b.count('1')%2; continue
                        ks=[key(b,e) for e in E]; best=max(ks)
                        ps={e['i']%2 for e,k in zip(E,ks) if k==best}
                        if len(ps)==1: U[W]=ps.pop()
                    sols=check(nu,U); out.append((len(U),bool(sols)))
                    if not sols: break
                print(prim,nm,sg,out,flush=True)
