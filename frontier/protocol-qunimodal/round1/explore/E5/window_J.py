# variants: window criterion restricted to pairs with M-x < r+J  (J=0: pure residue pairs only = A-bound condition)
# plus other simple closed-form candidates; instance-level error counts over full fit box.
from load import load
import sys
sys.path.insert(0,'rules')
from common import gamma, low_f
from collections import defaultdict
err=defaultdict(int); tot=0
for r in range(2,7):
    for a,mask in load(r):
        G=gamma(r,a); f=low_f(r,a,r); D=sum(x-1 for x in a); Q=sum(x//r for x in a); sig=D-r*Q
        e=lambda y: G[y%r]-(f[y-r] if y>=r else 0)
        for b in range(1,61):
            truth=bool((mask>>(b-1))&1); tot+=1
            M=D+1-r*(b-1)
            for J in range(0,r+1):
                ok=True; x=M-(r+J)+1
                while 2*x<M:
                    if e(x)<e(M-x): ok=False;break
                    x+=1
                if ok!=truth: err[('windowJ',r,J)]+=1
            # generic closed form for all r
            g = b <= 1+Q+max(0,2*((sig+3-r)//(2*r)))
            if g!=truth: err[('generic_all_r',r)]+=1
            if (b<=1+D//r)!=truth: err[('b<=1+floor(D/r)',r)]+=1
            if (b<=(D+1)//r+1)!=truth: err[('b<=1+floor((D+1)/r)',r)]+=1
for k in sorted(err): print(k,err[k])
print("total instances",tot)
