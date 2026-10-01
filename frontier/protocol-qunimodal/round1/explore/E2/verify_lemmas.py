# Numerical sanity checks (inside the fit box) of the proved lemmas:
#  F : tau_c = (2/r) sum_j sin(pi j/r) A_j sin(pi j (Dpi+1-2c)/r),  A_j = prod sin(pi j t_i/r)/sin(pi j/r)
#  C : 2c <= Dpi+1
#  S : 2 y* <= Dpi + 1 - 2r   (y* = max{u: d_u < tau_u})
#  D : k_eff<=3 => tau_{t_(2)-1} >= 1 (residues padded with 1's to length 3, sorted)
#  E3: r=3 => c-based bound equals 1+S+2*floor(n2/6)
import sys, math, itertools, pickle
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2/rules')
from E2_exact import _tau, _d
res=pickle.load(open('/tmp/claude-0/qu/explore/E2/scan.pkl','rb'))
bad={'F':0,'C':0,'S':0,'D':0,'E3':0}; n=0; nD=0; n3=0
for r,a,D,tt,ys,c,B1,O in res:
    a=list(a); n+=1
    t=[x%r for x in a]; Dpi=sum(x-1 for x in t)
    for cc in range(r):
        e=Dpi+1-2*cc
        val=0.0
        for j in range(1,r):
            A=1.0
            for ti in t: A*=math.sin(math.pi*j*ti/r)/math.sin(math.pi*j/r)
            val+=math.sin(math.pi*j/r)*A*math.sin(math.pi*j*e/r)
        val*=2/r
        if abs(val-tt[cc])>1e-6: bad['F']+=1
    if 2*c>Dpi+1: bad['C']+=1
    if 2*ys>Dpi+1-2*r: bad['S']+=1
    keff=sum(1 for x in a if x>=2)
    if keff<=3:
        nD+=1
        tp=sorted(t+[1]*(3-len(t))) if len(t)<3 else sorted(t)
        if len(tp)==3 and tt[tp[1]-1]<1: bad['D']+=1
    if r==3:
        n3+=1
        S=sum(x//r for x in a); n2=sum(1 for x in t if x==2)
        if 1+(D+1-2*c)//r != 1+S+2*(n2//6): bad['E3']+=1
print("records",n,"k_eff<=3 records",nD,"r=3 records",n3,"violations",bad)
