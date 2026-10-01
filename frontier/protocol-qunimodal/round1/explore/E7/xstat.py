# Statistics of X (first descent of L) : X-rF vs S, shift invariance of X, X relative to D.
import collections, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import X_of
U=[]
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); U.append((r,a))
XX={}
for r,a in U:
    X,D,L=X_of(r,a); XX[(r,a)]=(X,D)
# shift invariance of X
bad=0;tot=0;badc=collections.Counter()
for (r,a),(X,D) in XX.items():
    for i in range(len(a)):
        a2=tuple(sorted(a[:i]+(a[i]+r,)+a[i+1:]))
        if (r,a2) in XX:
            tot+=1
            if XX[(r,a2)][0]!=X+r: bad+=1; badc[(r,a[i])]+=1
print("X shift test",tot,"bad",bad,dict(badc))
# relation 2X+1-D  (case A threshold: unimodal iff r(b-1) <= 2X+1-D)
t=collections.Counter()
for (r,a),(X,D) in XX.items():
    t[(r,2*X+1-D)]+=1
for k in sorted(t): print(k,t[k])
