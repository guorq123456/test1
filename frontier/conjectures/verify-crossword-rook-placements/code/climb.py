import subprocess, sys
def evalmany(n, ws):
    inp = str(n)+'\n' + '\n'.join(' '.join(map(str,w)) for w in ws) + '\n'
    out = subprocess.run(['./batch'], input=inp, capture_output=True, text=True).stdout.split()
    return list(map(int, out))
def neighbors(w):
    n=len(w); res=set()
    for i in range(n):
        for j in range(i+1,n):
            v=list(w); v[i],v[j]=v[j],v[i]; res.add(tuple(v))
    for i in range(n):
        for j in range(n):
            if i==j: continue
            v=list(w); x=v.pop(i); v.insert(j,x); res.add(tuple(v))
    # value-swaps (swap values a and a+1..)
    return list(res)
n=int(sys.argv[1]); w=tuple(int(x) for x in sys.argv[2:])
cur=evalmany(n,[w])[0]; print('start',cur,w,flush=True)
for it in range(30):
    nb=neighbors(w); vals=evalmany(n,nb)
    best=max(range(len(nb)), key=lambda k: vals[k])
    if vals[best] <= cur: print('local max', cur, w); break
    w=nb[best]; cur=vals[best]; print(it, cur, ' '.join(map(str,w)), flush=True)
