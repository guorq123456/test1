# Print F around the middle for a few sample Q to understand behavior of u near M/2
import numpy as np, sys
def Fser(Q,L):
    D=np.zeros(L+1,dtype=np.int64); D[:len(Q)]+=Q; D[1:len(Q)+1]-=Q
    F=D.copy()
    for i in range(3,L+1): F[i]+=F[i-3]
    return F,D
for a in [(11,11,11,11),(2,2,2,2,2,2,2,2),(4,5,7,8),(2,11)]:
    M=sum(x-1 for x in a)
    Q=np.array([1],dtype=np.int64)
    for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
    F,D=Fser(Q,M+6)
    print(a,'M=',M)
    print('  t :',list(range(M+4)))
    print('  Q :',list(Q))
    print('  F :',list(F[:M+4]))
