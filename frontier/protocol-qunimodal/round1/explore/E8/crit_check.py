# Verify the derived exact criterion (Lemma: unimodal <=> no "bad pair") against data.tsv on the fit box.
# F = Q/(1+q+q^2) power series; p_y = periodic tail of F (y >= M-1).
# Bad pair: integers x<z, 0<=... z < M/2-2, F_z - F_x + p_x < 0 with F_x=0 for x<0 (and F_z=0 for z<0).
# Criterion: P unimodal for W=3(b-1) iff no bad pair with x+z = K := M-W-5.
import numpy as np, itertools
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F
mism=0; tot=0; minK_bad_vs=[]
for a,bs,B,t in rows:
    a=tuple(map(int,a.split(','))); M=sum(x-1 for x in a)
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    L=M+200
    F=Fser(Q,L)
    p=lambda y: F[M+3+((y-(M+3))%3)]  # periodic tail value at residue y
    Fv=lambda y: 0 if y<0 else F[y]
    bad=set()
    # z ranges over integers with z < M/2-2 ; x<z ; x+z=K ; K from -200..M-5
    for K in range(-200,M-4):
        for z in range(-200, M):
            if not (2*z < M-4): break
            x=K-z
            if x>=z: continue
            if Fv(z)-Fv(x)+p(x)<0: bad.add(K); break
    for b in range(1,61):
        W=3*(b-1); K=M-W-5
        pred = K not in bad
        tot+=1
        if pred != (bs[b-1]=='1'): mism+=1
print('pairs checked',tot,'criterion mismatches',mism)
