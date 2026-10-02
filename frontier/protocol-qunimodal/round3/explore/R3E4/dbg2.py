import sys; sys.path.insert(0,'.'); sys.path.insert(0,'/tmp/claude-0/qu/tools')
from fpair import analyze, delta_float, tau_float
from gt_big import poly_a
import numpy as np
r=8; a=[1,9,9,29]
D=sum(x-1 for x in a); X=(D+1)//2; F=sum(x//r for x in a)
d,ls=delta_float(a,X)
A=poly_a(a); de=[A[0]]+[A[i]-A[i-1] for i in range(1,len(A))]+[-A[-1]]
print(np.max(np.abs(d*np.exp(ls)-np.array(de[:X+1]))))
t=tau_float(r,a,ls)*np.exp(ls); tt=[sum(de[x] for x in range(len(de)) if x%r==u) for u in range(r)]
print(np.max(np.abs(t-tt)))
print(D,F)
for C in range(1,r):
    if (C-(D+1))%2: continue
    Zs=[];kk=0
    while True:
        Z=(kk//2)*2*r+(C if kk%2==0 else 2*r-C)
        if Z>D+1: break
        Zs.append(Z);kk+=1
    y=[de[(D+1-Z)//2] for Z in Zs]
    An=[];s=0
    for i,v in enumerate(y): s+=v*(-1)**i; An.append(s)
    print(C,y,An,tt[((D+1-C)//2)%r])
