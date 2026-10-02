# Counterexample to O_rho (hence to "TP,E,O hold for every rho"):
# r=57, rho = rho' + 37 ones, k=52.  Independent checks:
#  (1) P_2(rho) = A_rho(q)(1+q^57) is NOT unimodal  (gt_big exact ground truth)  => ND_rho(K_1) false (Lemma 3)
#  (2) ND_rho(K_1) false by direct evaluation; K_1 = sigma+1-3r
#  (3) mu*_inf(k=52) computed from f = 1/((1-q)^51 (1-q^57)) and tau; check K_1 >= 2 mu*_inf + 3r
import sys; sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from reslev import *
r=57; rp=[6,7,9,15,18,20,22,23,25,26,27,28,30,33,37]; m=37
rho=sorted([1]*m+rp); k=len(rho); assert inbox(r,rho)
R=Res(r,rho); sigma=R.D
print('k',k,'sigma',sigma,'F',R.F)
print('(1) gt_big unimodal for b=1,2,3:',profile(r,rho,[1,2,3]))
K1=sigma+1-3*r
print('(2) K_1 =',K1,' ND_rho(K_1) =',R.ND(K1))
bad=[x for x in range(-((r-K1)//2), (K1+1)//2) if 2*x<K1 and R.Q(K1-x)<R.dd(x)]
print('    failing x:',bad[:5],'... count',len(bad))
mi=mustar_inf(r,k,R.tau)
f=fcoef(r,k,3*r)
print('(3) mu*_inf =',mi,' tau at -16 mod r:',R.tau[(-16)%r],' f_u vs tau_u for u=-16..3:',[(u,(f[u] if u>=0 else 0),R.tau[u%r]) for u in range(-16,4)])
print('    2mu*_inf+3r =',2*mi+3*r,' <= K_1 =',K1,':',2*mi+3*r<=K1)
c=certificate(r,rho); print('certificate:',c)
# with fewer ones (m=36) O holds:
c36=certificate(r,sorted([1]*36+rp)); print('m=36 certificate:',{x:c36[x] for x in ('TP','E','O','mu')})
