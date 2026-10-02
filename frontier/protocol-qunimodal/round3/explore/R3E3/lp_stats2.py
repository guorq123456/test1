import random, sys, collections
from pairs import pair_data
from lib4 import in_box
r=4
random.seed(int(sys.argv[1]))
H=collections.Counter(); worst=[]
tot=0
for it in range(3000):
    k=random.randint(4,60); mode=random.random(); a=[]
    for _ in range(k):
        if mode<0.25: a.append(random.choice([2,3,5,6,7,9,10,11]))
        elif mode<0.5: a.append(random.choice([2,6,10,3,7,5]))
        elif mode<0.75: a.append(random.choice([2,2,2,6,6,3]))
        else: a.append(random.choice([x for x in range(2,80) if x%4]))
    a.sort()
    if sum(1 for v in a if v%4==2)<3 or not in_box(r,a): continue
    tot+=1
    for p in pair_data(r,a):
        n=p['nstar']
        if n is None: continue
        y=p['y']; x=p['x']; xx=x(n+1); H[min(xx,30)]+=1
        if y(n+4)>0: worst.append(((y(n+1)-y(n+2))/y(n+4), xx, a))
print(tot, sorted(H.items()))
worst.sort(key=lambda z:z[0])
for w in worst[:10]: print(w)
