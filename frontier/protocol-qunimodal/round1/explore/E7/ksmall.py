# For small k' (number of a_i>=2, none divisible by r), compare the proven upper bound Bup=1+floor((D+1-2j*)/r)
# with the conjectured 1+F, i.e. how often the proven necessary condition already yields Conjecture-5.4 necessity.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p
c=collections.Counter()
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k])
    p=_p(a); D=len(p)-1; S=[sum(p[t::r]) for t in range(r)]
    js=max(j for j in range(r) if S[j]>S[(j-1)%r]); Bup=1+(D+1-2*js)//r
    F=sum(v//r for v in a)
    c[(k if k<=4 else '5+', r, Bup-1-F)]+=1
for kk in sorted(c, key=str): print(kk,c[kk])
