import pickle, collections
res=pickle.load(open('/tmp/claude-0/qu/explore/E2/scan.pkl','rb'))
st=collections.Counter(); obs=[]
for r,a,D,tt,ys,c,B1,O in res:
    k=len(a)
    st[(r,k,'n')]+=1
    if ys>=0: st[(r,k,'y>=0')]+=1
    if ys!=c-r: st[(r,k,'y!=c-r')]+=1
    if O: st[(r,k,'O')]+=1; obs.append((r,a,D,tt,ys,B1,O))
    S=sum(x//r for x in a)
    if B1<1+S: st[(r,k,'B1<1+S')]+=1
    if any(b<=1+S for b,_,_ in O): st[(r,k,'O<=1+S')]+=1
for r in range(2,7):
    print(r,[ (k,st[(r,k,'n')],st[(r,k,'y>=0')],st[(r,k,'y!=c-r')],st[(r,k,'O')],st[(r,k,'B1<1+S')],st[(r,k,'O<=1+S')]) for k in range(1,9)])
print("format (k, n, y*>=0, y*!=c-r, has pair-obstruction, B1<1+S, obstruction at b<=1+S)")
print(len(obs))
for o in obs[:30]: print(o)
