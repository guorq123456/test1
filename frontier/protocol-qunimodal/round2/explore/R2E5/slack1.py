# n=1: compare window values Phi_g (g for a=r+s) with Phi_c (flat) per m; report sign disagreements and min slack ratio
import sys
from flat import tau_of, cser
from core import gseries
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a
from fractions import Fraction
dis=0; tot=0; worst=None; nontriv=0
for r in range(4,int(sys.argv[1])+1):
    for s in range(2,r-1):
        a=r+s
        for k in range(3,61):
            tau=tau_of(r,s,k); A=poly_a([a]*k)
            Kmax=k*(s-1)+1-3*r
            L=max(Kmax,0)+2*r+5
            g=gseries(A,r,L); c=cser(r,k,L)
            gg=lambda j: g[j] if j>=0 else 0
            cc=lambda j: c[j] if j>=0 else 0
            for e in range(1,(k*(s-1))//r+3):
                K=k*(s-1)+1-r*(2+e); m0=(K-1)//2
                for m in range(m0,m0-r,-1):
                    pc=tau[m%r]+cc(K-m)-cc(m); pg=tau[m%r]+gg(K-m)-gg(m)
                    tot+=1
                    if pc!=pg: nontriv+=1
                    if (pc>=0)!=(pg>=0): dis+=1
                    if pc>=0 and pc!=pg:
                        ratio=Fraction(pc,pc-pg) if pc>pg else None
                        if ratio is not None and (worst is None or ratio<worst[0]): worst=(ratio,r,s,k,e,m,pc,pg)
print('window values',tot,'with g!=c',nontriv,'per-m sign disagreements',dis)
print('min ratio Phi_c/(Phi_c-Phi_g) among Phi_c>=0:',float(worst[0]),worst[1:6])
