from itertools import product
# Lemma 3: TL triples
tl=[t for t in product((-1,0,1),repeat=3) if t[1]-t[0] <= t[2]-t[1] <= 0]
print('TL patterns',len(tl),tl)
def is_TL(d,k):
    # d length k+1: d(2..k) equal e, p=d1-d0, q=e-d1, p<=q<=0
    e=d[2]
    if any(d[j]!=e for j in range(2,k+1)): return False
    p=d[1]-d[0]; q=e-d[1]; return p<=q<=0
def is_BR(d,k):
    e=d[0]
    if any(d[j]!=e for j in range(0,k-1)): return False
    u=d[k-1]-e; v=d[k]-d[k-1]; return 0<=u<=v
A={0:[[3,1],[5,3]],1:[[1,1],[2,3]]}
def f_formula(W):
    Wp=W[2:]
    if len(set(Wp))>1: return 1+W[0]
    return A[Wp[0]][W[0]][W[1]]
for k in range(2,13):
    words=list(product((0,1),repeat=k+1))
    f={};g={}
    for W in words:
        f[W]=sum(1 for Rr in words if is_TL([W[j]-Rr[j] for j in range(k+1)],k))
        g[W]=sum(1 for Rr in words if is_BR([Rr[j]-W[j] for j in range(k+1)],k))
    badf=sum(1 for W in words if f[W]!=f_formula(W))
    badg=sum(1 for W in words if g[W]!=f_formula(tuple(1-W[k-j] for j in range(k+1))))
    S=sum(f[W]*g[W] for W in words if len(set(W))>1)
    Sclaim={2:36,3:49}.get(k,9*2**(k-1)+12)
    c0=tuple([0]*(k+1)); c1=tuple([1]*(k+1))
    print(k,'f mism',badf,'g mism',badg,'S_k',S,'claim',Sclaim,S==Sclaim,'f,g const',f[c0],f[c1],g[c0],g[c1])
    if k>=6: break_early=True
