# Empirical minima of u_t=F_t-F_{t-1} and v_t=F_t-F_{t-2} over lower-half ranges, by (n2 mod 6, t mod 3).
# Ranges: R1: 0<=t<M/2-2 (Local range); R2: 0<=t<=M/2.  Grouped by m=#nontrivial factors (1,2,>=3).
import numpy as np, collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F
mins={}
for a,bs,B,t in rows:
    a=tuple(map(int,a.split(','))); M=sum(x-1 for x in a); n2=sum(1 for x in a if x%3==2)
    m=sum(1 for x in a if x>1); g=min(m,3)
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    F=Fser(Q,M+10); Fv=lambda y: 0 if y<0 else int(F[y])
    for tt in range(0,M+1):
        for rng,ok in (('R1',2*tt<M-4),('R2',2*tt<=M)):
            if not ok: continue
            for nm,val in (('u',Fv(tt)-Fv(tt-1)),('v',Fv(tt)-Fv(tt-2))):
                key=(rng,g,n2%6,nm,tt%3)
                mins[key]=min(mins.get(key,10**9),val)
for rng in ('R1','R2'):
  for g in (1,2,3):
    print(f'--- range {rng}, m={"%d"%g if g<3 else ">=3"}')
    for n in range(6):
        s=[]
        for nm in ('u','v'):
            s.append(nm+':'+','.join(str(mins.get((rng,g,n,nm,c),'-')) for c in range(3)))
        print('  n2%6=',n,'  '.join(s))
