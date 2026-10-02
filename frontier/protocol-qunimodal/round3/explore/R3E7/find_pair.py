# search: residue multiset s, two instances a,a' with residues s, same a_min, stable(a) != stable(a') (exact window criterion)
import itertools
from core import *
found=0
for r in range(4,9):
  for k in range(3,11):
    for s in itertools.combinations_with_replacement(range(1,r),k):
      R=Res(r,s)
      if len(R.Uinf)==1: continue
      # zero patterns: choose for each distinct residue>=2 how many copies stay at residue value
      ds=sorted(set(x for x in s if x>=2))
      cnts={x:s.count(x) for x in ds}
      opts=[range(cnts[x]+1) for x in ds]
      res={}
      for choice in itertools.product(*opts):
          a=[]
          for x,c in zip(ds,choice): a+= [x]*c + [x+r]*(cnts[x]-c)
          a+= [1+r]*s.count(1)
          a=sorted(a)
          if not in_box(r,a): continue
          res.setdefault(min(a),{}).setdefault(R.stable(a),a)
      for m,v in res.items():
          if len(v)==2:
              found+=1
              if found<=5: print(r,s,"a_min",m,"stable:",v[True],"unstable:",v[False])
print("found",found)
