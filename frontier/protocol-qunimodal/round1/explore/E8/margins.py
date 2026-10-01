# For each multiset in the fit box: compute margin m(x,z)=F_z-F_x+p_x over admissible pairs
# (x<z, 2z<M-4, x+z = K, K = M-W-5 for W=0,3,...,W*), W*=M-(n2 mod 6).
# Report the distribution of the minimal margin and where zero margins occur (x,z small?).
import numpy as np, collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F
minm=collections.Counter(); zero_pairs=collections.Counter(); zero_by_rel=collections.Counter()
for a,bs,B,t in rows:
    a=tuple(map(int,a.split(','))); M=sum(x-1 for x in a); n2=sum(1 for x in a if x%3==2)
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    F=Fser(Q,M+10)
    p=lambda y: int(F[M+3+((y-(M+3))%3)])
    Fv=lambda y: 0 if y<0 else int(F[y])
    Wst=M-n2%6
    mm=None
    for W in range(0,Wst+1,3):
        K=M-W-5
        for z in range(-20,M):
            if not 2*z<M-4: break
            x=K-z
            if x>=z: continue
            m=Fv(z)-Fv(x)+p(x)
            if mm is None or m<mm: mm=m
            if m==0:
                zero_by_rel[('x<0' if x<0 else 'x>=0', 'z<0' if z<0 else ('z<=2' if z<=2 else 'z>2'))]+=1
    minm[mm]+=1
print('distribution of min margin over multisets (None = no admissible pair):',sorted(minm.items(),key=lambda t:(t[0] is None, t[0] if t[0] is not None else 0)))
print('zero-margin pairs by location:',dict(zero_by_rel))
