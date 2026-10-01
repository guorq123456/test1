# How strongly is translation invariance (dependence on F only through d=b-1-F) exercised by the box?
# For each coarse class (r,R) (R=residues of a_i>1, no zero residue): distinct F values among members.
from load import load
from collections import defaultdict, Counter
recs=load(); Fv=defaultdict(set); Sv=defaultdict(set)
for r,a,m in recs:
    a2=[x for x in a if x>1]
    if any(x%r==0 for x in a2): continue
    R=tuple(sorted(x%r for x in a2)); Fv[(r,R)].add(sum(x//r for x in a2)); Sv[(r,R)].add(tuple(x for x in a2 if x<r))
for r in range(2,7):
    ks=[k for k in Fv if k[0]==r]
    print(f'r={r}: classes {len(ks)}, with >=2 F values {sum(1 for k in ks if len(Fv[k])>=2)}, max #F values {max(len(Fv[k]) for k in ks)}, max F {max(max(Fv[k]) for k in ks)}, classes with >=2 small/big splits {sum(1 for k in ks if len(Sv[k])>=2)}')
