# Variant of fsearch.py: b enters the key only through d = b-1-F (F = sum floor(a_i/r)), so F itself
# may be dropped. Key = (r, d, features in S). Conflict at (group,d): some member with d in-box unimodal, another in-box not.
import numpy as np, pickle, itertools, sys, time
from multiprocessing import Pool
codes,masks=pickle.load(open('/tmp/claude-0/qu/explore/E3/codes.pkl','rb'))
from load import load
recs=load()
NAMES=[k for k in codes if not k.startswith('_')]
n=len(masks)
OFF=48; W=108
Fv=np.array([sum(x//r for x in a) for r,a,m in recs],dtype=np.int64)
Ubits=((masks[:,None]>>np.arange(60,dtype=np.uint64)[None,:])&np.uint64(1)).astype(np.uint8)  # by b-1
Urel=np.zeros((n,W),dtype=np.uint8); Def=np.zeros((n,W),dtype=np.uint8)
cols=(np.arange(60)[None,:]-Fv[:,None]+OFF)   # index of d=b-1-F
rows=np.repeat(np.arange(n),60)
Urel[rows,cols.ravel()]=Ubits.ravel(); Def[rows,cols.ravel()]=1
def pack(M):
    lo=np.packbits(M[:,:64],axis=1,bitorder='little').view(np.uint64).ravel()
    hi=np.packbits(np.pad(M[:,64:],((0,0),(0,128-W))),axis=1,bitorder='little').view(np.uint64).ravel()
    return lo,hi
U1=pack(Urel&Def); U0=pack((1-Urel)&Def)
def key_of(S):
    key=codes['_r'].copy()
    for f in S:
        c=codes[f]; key=key*(int(c.max())+1)+c
        if key.max()>2**40: _,key=np.unique(key,return_inverse=True); key=key.astype(np.int64)
    return key
def evaluate(S):
    key=key_of(S)
    order=np.argsort(key,kind='stable'); ks=key[order]
    starts=np.flatnonzero(np.r_[True,ks[1:]!=ks[:-1]])
    inc=0; badmask=np.zeros(len(starts),bool)
    for w in range(2):
        o1=np.bitwise_or.reduceat(U1[w][order],starts); o0=np.bitwise_or.reduceat(U0[w][order],starts)
        cb=o1&o0; inc+=int(np.unpackbits(cb.view(np.uint8)).sum()); badmask|=cb!=0
    if inc==0: return (tuple(S),len(starts),0,0)
    sz=np.diff(np.r_[starts,n]); bad=np.flatnonzero(badmask)
    gid=np.repeat(np.arange(len(starts)),sz); sel=np.isin(gid,bad)
    rws=order[sel]; g2=gid[sel]; st2=np.flatnonzero(np.r_[True,g2[1:]!=g2[:-1]])
    c1=np.add.reduceat((Urel[rws]&Def[rws]),st2,axis=0,dtype=np.int32)
    c0=np.add.reduceat(((1-Urel[rws])&Def[rws]),st2,axis=0,dtype=np.int32)
    return (tuple(S),len(starts),inc,int(np.minimum(c1,c0).sum()))
if __name__=='__main__':
    maxsize=int(sys.argv[1]); out=sys.argv[2]
    found=[]; allres=[]; t0=time.time()
    with Pool(4) as P:
        for s in range(0,maxsize+1):
            cand=[S for S in itertools.combinations(NAMES,s) if not any(set(F)<=set(S) for F in found)]
            res=P.map(evaluate,cand,chunksize=8); allres+=res
            new=[x for x in res if x[2]==0]; found+=[x[0] for x in new]
            print(f'size {s}: evaluated {len(cand)}, determining {len(new)}, time {time.time()-t0:.0f}s',flush=True)
    pickle.dump(allres,open(out,'wb'))
    allres.sort(key=lambda x:(x[2],x[3],x[1]))
    print('best 40 by (inconsistent keys, majority errors, #groups):')
    for x in allres[:40]: print(x)
