# Analyze sample: U shapes, and whether X=|U|-1-F is a function of (r, residue multiset), (r,res,F), etc.
import pickle,collections,sys
rows=[]
for f in sys.argv[1:]: rows+=pickle.load(open(f,'rb'))
shape=collections.Counter(); byres=collections.defaultdict(set); byresF=collections.defaultdict(set)
nonint=[]
for r,a,U,T6,F,mu in rows:
    isint= list(U)==list(range(1,len(U)+1))
    if not isint: nonint.append((r,a,U,T6,F)); continue
    X=len(U)-1-F; E6=T6-1-F
    shape[(E6,E6-X)]+=1
    res=tuple(sorted(x%r for x in a if x%r!=1 or x>1))
    byres[(r,res)].add(X); byresF[(r,res,F)].add(X)
print("nonintervals",len(nonint), nonint[:5])
print("(E6,delta)",sorted(shape.items()))
print("res groups",len(byres),"nonconst",sum(1 for v in byres.values() if len(v)>1))
print("resF groups",len(byresF),"nonconst",sum(1 for v in byresF.values() if len(v)>1))
for k,v in list(byres.items()):
    if len(v)>1: print(k,v)
