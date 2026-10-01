# Stage-2 search (relative-b mode): key = (r, d=b-1-F, has0, S) with S ranging over subsets of residue-only features.
import numpy as np, pickle, itertools, sys, time
import fsearch_rel as FR
from multiprocessing import Pool
codes2,_=pickle.load(open('/tmp/claude-0/qu/explore/E3/codes2.pkl','rb'))
FR.codes=codes2
NAMES=[k for k in codes2 if not k.startswith('_') and k not in ('has0','res_ms_nt')]
def ev(S): return FR.evaluate(('has0',)+tuple(S))
if __name__=='__main__':
    maxsize=int(sys.argv[1]); out=sys.argv[2]; found=[]; allres=[]; t0=time.time()
    print('control res_ms_nt:',ev(('res_ms_nt',)),flush=True)
    with Pool(4) as P:
        for s in range(0,maxsize+1):
            cand=[S for S in itertools.combinations(NAMES,s) if not any(set(F)<=set(S) for F in found)]
            res=P.map(ev,cand,chunksize=4); allres+=res
            new=[x for x in res if x[2]==0]; found+=[x[0][1:] for x in new]
            print(f'size {s}: evaluated {len(cand)}, determining {len(new)}, time {time.time()-t0:.0f}s',flush=True)
    pickle.dump(allres,open(out,'wb'))
    allres.sort(key=lambda x:(x[3],x[1]))
    for x in allres[:30]: print(x)
