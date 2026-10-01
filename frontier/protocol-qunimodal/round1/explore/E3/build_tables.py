# Build lookup tables E for the rules from box data:
#  fine table:   (r, S=small factors 1<a_i<r sorted, Rb=residues of a_i>r sorted) -> sorted list of d>=1 with P unimodal, d=b-1-F
#  coarse table: (r, R=residues of all a_i>1 sorted) -> union of such d over members (majority vote per d)
# Only records with no a_i divisible by r. Checks consistency and translation-invariance support.
from load import load
from collections import defaultdict, Counter
import json
recs=load()
fine=defaultdict(lambda: defaultdict(set)); coarse=defaultdict(lambda: defaultdict(list))
Fvals=defaultdict(set)
for r,a,m in recs:
    a2=[x for x in a if x>1]
    if any(x%r==0 for x in a2): continue
    S=tuple(x for x in a2 if x<r); Rb=tuple(sorted(x%r for x in a2 if x>r)); R=tuple(sorted(x%r for x in a2))
    F=sum(x//r for x in a2)
    Fvals[(r,S,Rb)].add(F)
    for b in range(1,61):
        d=b-1-F; u=(m>>(b-1))&1
        fine[(r,S,Rb)][d].add(u); coarse[(r,R)][d].append(u)
incons=sum(1 for k,v in fine.items() for d,s in v.items() if len(s)>1)
neg=sum(1 for k,v in fine.items() for d,s in v.items() if d<=0 and s!={1})
big=sum(1 for k,v in fine.items() for d,s in v.items() if d>=5 and 1 in s)
print('fine classes',len(fine),' inconsistent (class,d):',incons,' d<=0 not-unimodal:',neg,' d>=5 unimodal:',big)
print('fine classes with >=2 distinct F values in box:',sum(1 for v in Fvals.values() if len(v)>=2))
Ef={f"{r}|{','.join(map(str,S))}|{','.join(map(str,Rb))}":sorted(d for d,s in v.items() if d>=1 and 1 in s) for (r,S,Rb),v in fine.items()}
Ec={}; cerr=0
for (r,R),v in coarse.items():
    E=[]
    for d,L in v.items():
        if d>=1:
            if 2*sum(L)>len(L): E.append(d)
            cerr+=min(sum(L),len(L)-sum(L))
    Ec[f"{r}|{','.join(map(str,R))}"]=sorted(E)
print('coarse classes',len(Ec),' majority errors (d>=1):',cerr)
print('fine nonempty',sum(1 for v in Ef.values() if v),' coarse nonempty',sum(1 for v in Ec.values() if v))
print('fine E value distribution',Counter(tuple(v) for v in Ef.values()))
print('coarse E value distribution',Counter(tuple(v) for v in Ec.values()))
json.dump({k:v for k,v in Ef.items() if v},open('table_fine.json','w'))
json.dump({k:v for k,v in Ec.items() if v},open('table_coarse.json','w'))
