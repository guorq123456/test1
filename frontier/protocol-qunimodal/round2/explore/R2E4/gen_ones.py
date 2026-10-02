# family ONES: many a_i=1 plus 3..8 larger entries (random, <=100, r∤a), k<=40. ([1]_q=1, so ones are inert.)
import random,sys
rng=random.Random(int(sys.argv[1])); n=int(sys.argv[2]); c=0
while c<n:
    r=rng.randint(4,30); L=rng.randint(3,8); big=[rng.randint(2,100) for _ in range(L)]
    if any(v%r==0 for v in big) or sum(1 for v in big if 2<=v%r<=r-2)<3: continue
    m=rng.randint(0,40-L); a=sorted([1]*m+big); print(r,len(a),*a); c+=1
