# For each (r,a) without r|a_i, compute set of b in 1..60 where unimodal; check down-set property; compare with 1+S
import sys, itertools
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import *
nondown=0; tot=0; agree=0; cnt_more=0; cnt_less=0
ex_more=[];ex_less=[];ex_nd=[]
for r in range(2,7):
    for k in range(1,5):
        for a in itertools.combinations_with_replacement(range(1,13),k):
            a=list(a)
            if any(x%r==0 for x in a): continue
            U=[b for b in range(1,61) if criterion(r,a,b)]
            tot+=1
            bm=max(U)
            if U!=list(range(1,bm+1)): nondown+=1; ex_nd.append((r,a,U))
            S=sum(x//r for x in a)
            if bm==1+S: agree+=1
            elif bm>1+S: cnt_more+=1; ex_more.append((r,a,bm,1+S))
            else: cnt_less+=1; ex_less.append((r,a,bm,1+S))
print("total",tot,"nondownset",nondown,"bmax==1+S",agree,"bmax>1+S",cnt_more,"bmax<1+S",cnt_less)
print("nondown ex",ex_nd[:10])
print("more ex",ex_more[:20])
print("less ex",ex_less[:20])
