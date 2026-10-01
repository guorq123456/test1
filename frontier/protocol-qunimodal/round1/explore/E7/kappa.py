# kappa(r,E) = floor((S+1-2j*)/r), E = multiset of residues a_i mod r that are >=2, S = sum(e-1).
# Check (1) kappa computed from actual tuple equals kappa computed from base tuple a=E (residue-only dependence),
# (2) list kappa for all residue patterns of size<=3 (k<=3) for r<=6.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p
def kap(r,a):
    p=_p(a); D=len(p)-1; S=[sum(p[t::r]) for t in range(r)]
    js=max(j for j in range(r) if S[j]>S[(j-1)%r])
    F=sum(v//r for v in a)
    return (D+1-2*js)//r - F, js
base={}; bad=0; n=0
rows=[]
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); rows.append((r,a))
for r,a in rows:
    if all(v<r for v in a): base[(r,a)]=kap(r,a)
for r,a in rows:
    E=tuple(sorted(v%r for v in a if v%r>=2))
    n+=1
    if kap(r,a)!=base[(r,E)]: bad+=1
print("tuples",n,"residue-only dependence failures (kappa,j*):",bad)
small=collections.Counter((r,base[(r,E)][0]) for (r,E) in base if len(E)<=3)
print("kappa over all residue patterns with <=3 entries (r<=6):",dict(small))
print("kappa distribution over all base patterns (<=8 entries):",dict(collections.Counter((r,v[0]) for (r,E),v in base.items())))
