# Stage-3 search (relative-b mode): key=(r,d,has0,S), S over subsets (size<=3) of residue + small-factor + low-coefficient features.
import pickle, itertools, sys, time
import fsearch_rel as FR
from multiprocessing import Pool
codes3,_=pickle.load(open('/tmp/claude-0/qu/explore/E3/codes3.pkl','rb'))
FR.codes=codes3
NAMES=[k for k in codes3 if not k.startswith('_') and k not in ('has0','res_ms_nt')]
def ev(S): return FR.evaluate(('has0',)+tuple(S))
if __name__=='__main__':
    maxsize=int(sys.argv[1]); out=sys.argv[2]; found=[]; allres=[]; t0=time.time()
    print('library',NAMES,flush=True)
    print('controls:',ev(('res_ms_nt','cap_ms')),ev(('res_ms_nt','Alow_r')),flush=True)
    with Pool(4) as P:
        for s in range(0,maxsize+1):
            cand=[S for S in itertools.combinations(NAMES,s) if not any(set(F)<=set(S) for F in found)]
            res=P.map(ev,cand,chunksize=4); allres+=res
            new=[x for x in res if x[2]==0]; found+=[x[0][1:] for x in new]
            print(f'size {s}: evaluated {len(cand)}, determining {len(new)}, time {time.time()-t0:.0f}s',flush=True)
    pickle.dump(allres,open(out,'wb'))
    det=sorted([x for x in allres if x[2]==0],key=lambda x:x[1])
    print('determining sets, coarsest first:')
    for x in det[:30]: print(x)
    print('best non-determining:')
    for x in sorted([x for x in allres if x[2]>0],key=lambda x:(x[3],x[1]))[:15]: print(x)
