# Exhaustive test for small r: four middle parts with values < 3r, plus 0..E extra parts with residue 1 or r-1
# (values in [2,3r)). Tests rule files; counts errors and U-shape types.
import sys, itertools, importlib.util
from collections import Counter
from core import U
r=int(sys.argv[1]); E=int(sys.argv[2]); rules=sys.argv[3:]
mods=[]
for f in rules:
    spec=importlib.util.spec_from_file_location(f,f); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); mods.append((f,m))
midv=[x for x in range(2,3*r) if 2<=x%r<=r-2]
extv=[x for x in range(2,3*r) if x%r in (1,r-1)]
err=Counter(); inst=0; shapes=Counter(); bad={}
for M in itertools.combinations_with_replacement(midv,4):
    for e in range(E+1):
        for X in itertools.combinations_with_replacement(extv,e):
            a=sorted(M+X); inst+=1
            u,T6,_=U(r,a)
            sh=tuple(sorted(set(range(1,T6+1))-set(u))); shapes[tuple(x-T6 for x in sh)]+=1
            for f,m in mods:
                for b in range(1,T6+3):
                    if m.predict(r,a,b)!=(b in u):
                        err[f]+=1; bad.setdefault(f,(a,u,T6))
print('r',r,'E',E,'inst',inst,'errors',dict(err),'missing-from-[1,T6] shapes',dict(shapes)); print(bad)
