"""Theorem B hypotheses (eps, c, kappa, (K)) on the three known pair-local failure instances."""
from winx import InstX
from hyp import check
for f in ["r8595","r12552","r15167_Fodd"]:
    v=open("/tmp/claude-0/qu/synth/r2/inst_ki_fail_%s.txt"%f).read().split()
    I=InstX(int(v[1]),sorted(map(int,v[2:]))); h=check(I)
    G,ns,N=I.G,I.nstar,I.N; r=I.r
    gm=min(G,key=lambda g:abs(g-r/2))
    print(f,"N*",N,"eps=%.3e c=%.6f kappa=%.3f K=%s"%(h['eps'],h['c'],h['kappa'],h['K']),"middle-pair witness Q<0:",I.Q(N+4,gm)<0,flush=True)
