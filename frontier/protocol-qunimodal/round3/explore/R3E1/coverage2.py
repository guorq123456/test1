"""Coverage of Theorem B (H1 version, condition (K) at t1 nearest r/4) and Theorem B* (shape-ratio version (K*)) on fit-box
data, with consistency checks (theorem applies => the theorem's witness window is negative, exact) and the number of
instances covered neither by B/B* nor by the pair-local inequality at some binding pair.
Families: small (survey2.gen r<=120), big (survey2.gen r>=1000), tuned (survey3.gen_tuned r in [3000,20000])."""
import random, sys, math
from winx import InstX
from box import in_box
import survey2, survey3
from hyp import check, check_star
fam=sys.argv[1]; seed=int(sys.argv[2]); cnt=int(sys.argv[3]); rng=random.Random(seed)
n=cK=cS=incK=incS=unc=pl=0
for it in range(cnt):
    if fam=="small": r,a=survey2.gen(rng,False)
    elif fam=="big": r,a=survey2.gen(rng,True)
    else: r,a=survey3.gen_tuned(rng)
    if not in_box(r,a) or any(x%r==0 for x in a): continue
    I=InstX(r,a); h=check(I); gs=check_star(I); n+=1
    G,ns,N=I.G,I.nstar,I.N
    gm=min(G,key=lambda g:abs(g-r/2)); w1=I.Q(N+4,gm)<0
    B=[g for g in G if ns.get(g)==N]; plany=any(I.Q(N+4,g)<0 for g in B)
    if h['K']:
        cK+=1
        if not w1: incK+=1; print("INCONSISTENT_K",r,a)
    if gs is not False:
        cS+=1
        if not I.Q(N+4,gs)<0: incS+=1; print("INCONSISTENT_KSTAR",r,a)
    if plany: pl+=1
    if not h['K'] and gs is False and not plany: unc+=1; print("UNCOVERED",r,a)
    print(fam,r,len(a),I.F,N,"eps=%.3g kappa=%.3g K=%d Kstar=%d W1=%d PLany=%d"%(h['eps'],h['kappa'],h['K'],gs is not False,w1,plany),flush=True)
print("SUMMARY",fam,"seed",seed,"n",n,"K",cK,"Kstar",cS,"K_or_Kstar_incons",incK+incS,"pairlocal_any",pl,"uncovered",unc)
