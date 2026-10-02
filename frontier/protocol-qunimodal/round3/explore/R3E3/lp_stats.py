# r=4: L' margin at n*(C) over instances in fit box. Prints worst cases.
import random, sys
from pairs import pair_data
from lib4 import in_box
r=4
def check(a):
    res=[]
    for p in pair_data(r,a):
        n=p['nstar']
        if n is None: continue
        y=p['y']; x=p['x']
        lhs=y(n+1)-y(n+2); rhs=y(n+4)
        res.append((lhs-rhs, lhs, rhs, x(n+1), p['C'], n, abs(p['Ainf'])))
    return res
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)
worst=[]; tot=0; fails=0
for it in range(4000):
    k=random.randint(4,40)
    mode=random.random()
    a=[]
    for _ in range(k):
        if mode<0.3: a.append(random.choice([2,3,5,6,7,9,10,11]))
        elif mode<0.6: a.append(random.choice([2,6,10,3,7,1,5]))
        else: a.append(random.choice([x for x in range(2,60) if x%4]))
    a.sort()
    if sum(1 for v in a if v%4==2)<3 or not in_box(r,a): continue
    tot+=1
    for t in check(a):
        if t[0]<0: fails+=1; print("FAIL",a,t)
        worst.append((t[2] and t[1]/t[2] or 1e9, t, a))
worst.sort(key=lambda z:z[0])
print("instances",tot,"Lprime fails",fails)
for w in worst[:15]: print(w)
