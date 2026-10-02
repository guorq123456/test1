# Test decomposition-based induction: B*(rho) <= max(B*(n-1), max_i B*(flip_i))   (flip_i: m_i -> r-m_i, n -> n-1)
# plus pair decomposition [m1][m2] = [r][m1+m2-r] + sum q^.[m1-m2+2i-1] when m1+m2>=r -> Thm E pieces (T6 of two-middle)
from base import *
from collections import Counter
import sys
def Bst(ms,n,r):
    return params(sorted(ms),n,r)[6]
def T6gen(r,a):
    # T6 for general tuple a (no part divisible by r assumed); residues only + D
    D=sum(x-1 for x in a)
    t=[0]*r
    # tau = residue sums of (1-q)prod[a]
    R=[1]
    for A in a:
        d=[0]*(len(R)+A-1)
        for i,v in enumerate(R):
            for j in range(A): d[i+j]+=v
        R=d
    for j in range(len(R)+1):
        t[j%r]+=(R[j] if j<len(R) else 0)-(R[j-1] if j>=1 else 0)
    mu=0
    for j in range(1,r):
        if t[j]>0: mu=j
    return 1+(D+1-2*mu)//r
R=int(sys.argv[1]); N=int(sys.argv[2])
c=Counter(); ex={}
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        ms=[m1,m2,m3]
        for n in range(1,N+1):
          B=Bst(ms,n,r)
          srcs={'mono':Bst(ms,n-1,r)}
          for i in range(3):
              f=ms[:]; f[i]=r-f[i]
              srcs['flip%d'%i]=Bst(f,n-1,r)
          best=max(srcs.values())
          key=('ok' if best>=B else 'short', B-best if best<B else 0)
          c[key]+=1
          if best<B and key not in ex: ex[key]=(r,ms,n,B,srcs)
print(sorted(c.items()))
for k,v in ex.items(): print(k,v)
