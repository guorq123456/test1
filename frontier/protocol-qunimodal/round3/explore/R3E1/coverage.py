"""Coverage of the conditional cross-pair theorem on fit-box data, and consistency check (K holds => middle-pair witness
Q_{N*+4}(t1)<0, t1 nearest r/4).  Families: 'small' (survey2.gen r<=120), 'big' (survey2.gen r>=1000), 'tuned' (survey3)."""
import random, sys, math
from winx import InstX
from box import in_box
import survey2, survey3
from hyp import check
fam=sys.argv[1]; seed=int(sys.argv[2]); cnt=int(sys.argv[3]); rng=random.Random(seed)
n=cov=incons=0; eps_ok=kap_ok=0; unc=0
for it in range(cnt):
    if fam=="small": r,a=survey2.gen(rng,False)
    elif fam=="big": r,a=survey2.gen(rng,True)
    else: r,a=survey3.gen_tuned(rng)
    if not in_box(r,a) or any(x%r==0 for x in a): continue
    I=InstX(r,a); h=check(I); n+=1
    G,ns,N=I.G,I.nstar,I.N
    gm=min(G,key=lambda g:abs(g-r/2)); w1=I.Q(N+4,gm)<0
    B=[g for g in G if ns.get(g)==N]; w6=I.Q(N+4,min(B))<0; plany=any(I.Q(N+4,g)<0 for g in B)
    if not h['K'] and not plany: unc+=1
    if h['eps']<1: eps_ok+=1
    if h['kappa']>=2.0: kap_ok+=1
    if h['K']:
        cov+=1
        if not w1: incons+=1; print("INCONSISTENT",r,a,h)
    print(fam,r,len(a),I.F,N,"eps=%.3g kappa=%.3g K=%d W1=%d W6=%d PLany=%d"%(h['eps'],h['kappa'],h['K'],w1,w6,plany),flush=True)
print("SUMMARY",fam,"n",n,"eps<1",eps_ok,"kappa>=2",kap_ok,"K(theorem applies)",cov,"inconsistent",incons,"uncovered(neither K nor pair-local at a binding pair)",unc)
