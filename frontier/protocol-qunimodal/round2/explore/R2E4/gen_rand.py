# random structured-family instance generator (lines "r k a..."). usage: gen_rand.py family seed n
import sys,random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E4')
from sampler import gen
from core import in_box,nmiddle
fam=sys.argv[1]; rng=random.Random(int(sys.argv[2])); n=int(sys.argv[3]); c=0
while c<n:
    r,a=gen(fam,rng)
    if not in_box(r,a) or any(x%r==0 for x in a) or nmiddle(r,a)<3: continue
    print(r,len(a),*a); c+=1
