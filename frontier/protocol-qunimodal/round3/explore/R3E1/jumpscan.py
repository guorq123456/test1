"""Near-jump scan (r>=1000): a_i = s + d_i (fixed offsets d_i in [-2,2]), s scanned through an N* jump.
Per s: N*, #binding pairs, #binding pairs failing pair-local KI, S2, middle-pair witness W1, Theorem B (K) applicability."""
import sys, random
from winx import InstX
from hyp import check
r=int(sys.argv[1]); k=int(sys.argv[2]); s_lo=int(sys.argv[3]); s_hi=int(sys.argv[4]); step=int(sys.argv[5])
rng=random.Random(1); d=[rng.randint(-2,2) for _ in range(k)]
for s in range(s_lo,s_hi+1,step):
    a=sorted(s+x for x in d)
    I=InstX(r,a); h=check(I); G,ns,N=I.G,I.nstar,I.N
    q={g:I.Q(N+4,g) for g in G}
    B=[g for g in G if ns.get(g)==N]
    gm=min(G,key=lambda g:abs(g-r/2))
    print("s",s,"N*",N,"nbind",len(B),"bind_KIfail",sum(1 for g in B if q[g]>=0),"S2",any(v<0 for v in q.values()),
          "W1",q[gm]<0,"eps=%.2e kappa=%.2f K=%s"%(h['eps'],h['kappa'],h['K']),flush=True)
