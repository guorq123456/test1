# Empirical: min over lower-half pairs 0<=x<z, 2z<M-4 of F_z-F_x, grouped by (n2 mod 6, M mod 3, x mod 3, z mod 3),
# separately for "m>=3 nontrivial factors" vs fewer. Also show p and the residue constraint x+z = M+1 mod 3.
import numpy as np, collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F
mn=collections.defaultdict(lambda:10**9)
for a,bs,B,t in rows:
    a=tuple(map(int,a.split(','))); M=sum(x-1 for x in a); n2=sum(1 for x in a if x%3==2)
    m=sum(1 for x in a if x>1)
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    F=Fser(Q,M+10)
    for z in range(0,M):
        if not 2*z<M-4: break
        for x in range(0,z):
            key=(m>=3,n2%6,x%3,z%3)
            v=int(F[z]-F[x])
            if v<mn[key]: mn[key]=v
for g in (False,True):
    print('m>=3' if g else 'm<=2')
    for n in range(6):
        M3=n%3
        p={0:(1,-1,0),1:(1,0,-1),2:(0,1,-1),3:(-1,1,0),4:(-1,0,1),5:(0,-1,1)}[n]
        line=[]
        for xr in range(3):
            for zr in range(3):
                k=(g,n,xr,zr)
                if k in mn:
                    adm=((xr+zr)%3==(M3+1)%3)
                    line.append(f"x{xr}z{zr}:{mn[k]}{'*' if adm else ''}(p_x={p[xr]})" if adm else f"x{xr}z{zr}:{mn[k]}")
        print(' n2%6=',n,' '.join(line))
