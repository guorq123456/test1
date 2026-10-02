# Explore U for tuples with exactly three middle residues: compare with [1,T6].
import random, sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
random.seed(2)
cnt=collections.Counter(); ex={}
for trial in range(4000):
    r=random.randint(4,10)
    mids=[random.randint(2,r-2) for _ in range(3)]
    n1=random.randint(0,4); nm=random.randint(0,4)
    a=[]
    for m in mids: a.append(m+r*random.randint(0,4))
    for _ in range(n1): a.append(1+r*random.randint(1,4))
    for _ in range(nm): a.append(r-1+r*random.randint(0,4))
    a=sorted(a)
    D,F,Gam,mu,T6=stats(r,a)
    U=Uset(r,a)
    if U==list(range(1,T6+1)): key='[1,T6]'
    elif U==list(range(1,len(U)+1)): key=f'interval [1,T6-{T6-len(U)}]'
    else:
        key='nonint'
    cnt[key]+=1
    if key not in ex or len(ex[key])<5: ex.setdefault(key,[]).append((r,a,U,T6,F))
for k,v in cnt.items(): print(k,v)
for k,v in ex.items():
    print(k)
    for e in v: print('  ',e)
