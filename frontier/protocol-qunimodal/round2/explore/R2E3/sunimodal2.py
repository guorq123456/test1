import sys, random
sys.path.insert(0,'.')
from sunimodal import s_of, unimod
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); bad=0
for it in range(N):
    k=random.randint(2,14); amax=random.choice([5,10,30,100])
    a=sorted(random.randint(1,amax) for _ in range(k))
    if not unimod(s_of(a)):
        bad+=1; print("NONUNIMODAL",a)
eq=0
for A in range(2,30):
    for k in range(1,61 if A<10 else 25):
        if not unimod(s_of([A]*k)): eq+=1; print("NONUNI equal",A,k)
print("random tested",N,"bad",bad,"; equal-a bad",eq)
