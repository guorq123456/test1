# Systematic search over feature subsets: does key (r, b, features in S) determine unimodality on the whole box?
# For each subset records: #groups (r,S) , #inconsistent keys (with b), majority-vote error instances.
import numpy as np, pickle, itertools, sys, time
from multiprocessing import Pool
codes,masks=pickle.load(open('/tmp/claude-0/qu/explore/E3/codes.pkl','rb'))
NAMES=[k for k in codes if not k.startswith('_')]
n=len(masks)
U=((masks[:,None]>>np.arange(60,dtype=np.uint64)[None,:])&np.uint64(1)).astype(np.uint8)
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
    ms=masks[order]
    o=np.bitwise_or.reduceat(ms,starts); a=np.bitwise_and.reduceat(ms,starts)
    cb=o&~a
    inc=int(np.unpackbits(cb.view(np.uint8)).sum())
    if inc==0: maj=0
    else:
        sz=np.diff(np.r_[starts,n])
        bad=np.flatnonzero(cb!=0)
        gid=np.repeat(np.arange(len(starts)),sz)
        sel=np.isin(gid,bad)
        rows=order[sel]; g2=gid[sel]
        st2=np.flatnonzero(np.r_[True,g2[1:]!=g2[:-1]])
        cnt=np.add.reduceat(U[rows],st2,axis=0,dtype=np.int32)
        sz2=sz[bad][:,None]
        maj=int(np.minimum(cnt,sz2-cnt).sum())
    return (tuple(S),len(starts),inc,maj)
if __name__=='__main__':
    maxsize=int(sys.argv[1]); out=sys.argv[2]
    found=[]  # minimal determining sets
    allres=[]
    t0=time.time()
    with Pool(4) as P:
        for s in range(0,maxsize+1):
            cand=[S for S in itertools.combinations(NAMES,s) if not any(set(F)<=set(S) for F in found)]
            res=P.map(evaluate,cand,chunksize=8)
            allres+=res
            new=[x for x in res if x[2]==0]
            found+=[x[0] for x in new]
            print(f'size {s}: evaluated {len(cand)} (supersets of determining sets skipped), determining {len(new)}, time {time.time()-t0:.0f}s',flush=True)
    pickle.dump(allres,open(out,'wb'))
    allres.sort(key=lambda x:(x[2],x[3],x[1]))
    print('best 40 by (inconsistent keys, majority errors, #groups):')
    for x in allres[:40]: print(x)
