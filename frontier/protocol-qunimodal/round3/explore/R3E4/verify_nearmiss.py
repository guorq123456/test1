# Exact verification (python-flint big ints) of two near-miss instances: exact pair criterion + brute force U.
import sys,json; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from exact_verify import polyA, pairs_exact, brute
from fpv import fast
top=json.load(open('nearmiss_top.json'))
L=[json.loads(l) for l in open('survey1.jsonl')]
lift=max((x for x in L if x['fam']=='lift' and x['Nstar']>=5 and x['r']>=3000),key=lambda x:x['gap'])
cases=[(top[1][4],top[1][10]),(lift['r'],lift['a'])]
for r,a in cases:
    A=polyA(a); pe=pairs_exact(r,a,A); pe.pop('per'); f=fast(r,a)
    N,B=pe['Nstar'],pe['beta']; bs=list(range(max(1,N-2),B+6))
    bu=brute(r,a,bs,A)
    print('r',r,'k',len(a),'exact pairs',pe,'float',(f['Nstar'],f['beta'],round(f['gap'],4)))
    print('  brute unimodal b:',[b for b,u in zip(bs,bu) if u],'tested',bs)
    print('  a=',a)
