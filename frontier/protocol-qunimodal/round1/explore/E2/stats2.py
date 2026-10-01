import pickle, collections
res=pickle.load(open('/tmp/claude-0/qu/explore/E2/scan.pkl','rb'))
dist=collections.Counter()
for r,a,D,tt,ys,c,B1,O in res:
    if ys>=0: dist[(r,ys)]+=1
print(sorted(dist.items()))
# check whether extra=B1-1-S
ex=collections.Counter()
for r,a,D,tt,ys,c,B1,O in res:
    S=sum(x//r for x in a); ex[(r,B1-1-S, ys>=0)]+=1
print(sorted(ex.items()))
