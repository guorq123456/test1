import sys; sys.path.insert(0,'.')
from fpair import analyze, delta_float, tau_float
import numpy as np
sys.path.insert(0,'/tmp/claude-0/qu/tools'); from gt_big import profile, poly_a
r=7; a=[3,5,9,10]
res=analyze(r,a); print(res)
print(profile(r,a,range(1,12)))
D=sum(x-1 for x in a); X=(D+1)//2
d,ls=delta_float(a,X); A=poly_a(a); de=[A[0]]+[A[i]-A[i-1] for i in range(1,len(A))]+[-A[-1]]
print(d*np.exp(ls)); print(de[:X+1])
t=tau_float(r,a,ls)*np.exp(ls); print(t); print([sum(de[x] for x in range(len(de)) if x%r==u) for u in range(r)])
