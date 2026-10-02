# Neighborhood generator: for every equal-family instance with shape 'gap' (from fam_equal.out),
# emit all one-element replacements a -> (x^(k-1), y), y in 1..100, r∤y, y!=x, #middle>=3. (family N1)
import json,sys
mode=sys.argv[1] if len(sys.argv)>1 else 'gap'
rows=[json.loads(l) for l in open('/tmp/claude-0/qu/explore2/R2E4/fam_equal.out')]
for (r,x,k,holds,shape,par,Bs,F,T6,bey,cl) in rows:
    if mode=='gap' and shape!='gap': continue
    if mode=='wide' and not (Bs-F>=9): continue
    for y in range(1,101):
        if y%r==0 or y==x: continue
        a=sorted([x]*(k-1)+[y])
        if sum(1 for v in a if 2<=v%r<=r-2)<3: continue
        if len(a)>40 and len(set(a))>1: continue   # fit box: k<=40 unless all equal
        print(r,len(a),*a)
