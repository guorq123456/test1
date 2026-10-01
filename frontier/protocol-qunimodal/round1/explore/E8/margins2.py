# List multisets having zero-margin pairs with x>=0 and z>2 (interior tight pairs), summarize by nontrivial part
import numpy as np, collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F
seen=collections.defaultdict(list)
for a,bs,B,t in rows:
    a=tuple(map(int,a.split(','))); M=sum(x-1 for x in a); n2=sum(1 for x in a if x%3==2)
    nt=tuple(x for x in a if x>1)
    if 1 in a: continue
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    F=Fser(Q,M+10)
    p=lambda y: int(F[M+3+((y-(M+3))%3)])
    Fv=lambda y: 0 if y<0 else int(F[y])
    Wst=M-n2%6
    for W in range(0,Wst+1,3):
        K=M-W-5
        for z in range(3,M):
            if not 2*z<M-4: break
            x=K-z
            if x>=z or x<0: continue
            if Fv(z)-Fv(x)+p(x)==0: seen[nt].append((W,x,z))
for nt in sorted(seen,key=lambda t:(len(t),t))[:60]: print(nt, seen[nt][:6])
print('number of multisets (no 1s) with interior tight pairs:',len(seen))
print('by number of factors:',collections.Counter(len(t) for t in seen))
