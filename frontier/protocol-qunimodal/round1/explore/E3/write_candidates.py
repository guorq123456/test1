# Write candidates.tsv: every candidate tried (feature subsets in all 4 searches, the two aggregate keys, the two rules)
# with its fit-box error count = majority-vote instance errors over all 37,790,700 box instances
# (0 <=> the key determines unimodality on the box) and number of inconsistent keys.
import pickle, sys
sys.argv=['x']
exec(open('/tmp/claude-0/qu/explore/E3/fsearch.py').read().split("if __name__")[0])
rows=[]
def add(mode,res):
    for S,ng,inc,maj in res:
        rows.append((mode,'+'.join(S) if S else '(none)',ng,inc,maj))
add('raw: key=(r,b,S)',pickle.load(open('fsearch3.pkl','rb')))
add('relative: key=(r,d=b-1-F,S)',pickle.load(open('fsearch_rel3.pkl','rb')))
add('stage2 relative: key=(r,d,S)',pickle.load(open('fsearch2_4.pkl','rb')))
add('stage3 relative: key=(r,d,S)',pickle.load(open('fsearch3s.pkl','rb')))
add('raw aggregate key (with a_i=1)',[evaluate(('k','res_ms','F','D'))])
add('raw aggregate key (a_i=1 removed)',[evaluate(('kn','res_ms_nt','F','D'))])
rows.append(('rule','rule_fine.py (table on (r,S,Rb), d)','32206 classes','-',0))
rows.append(('rule','rule_coarse.py (table on (r,R), d)','2001 classes','-',24))
with open('candidates.tsv','w') as fh:
    fh.write('# mode\tcandidate\t#classes\tinconsistent_keys\tfitbox_errors(majority-vote instances of 37790700)\n')
    for r in rows: fh.write('\t'.join(map(str,r))+'\n')
print('total candidates',len(rows))
from collections import Counter
print(Counter(r[0] for r in rows))
print('determining (0 errors):',sum(1 for r in rows if r[4]==0))
