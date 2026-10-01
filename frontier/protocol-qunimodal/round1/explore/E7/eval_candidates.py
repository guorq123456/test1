# Instance-level error counts in the fit box for threshold-type candidates, using scan masks (truth).
# Only tuples with no r|a_i and entries 2..12 can err for these rules (r|a_i: all rules predict unimodal = truth,
# a_i=1 entries are trivial). Reported: distinct-P errors and box-weighted errors (weight 9-k' for k'>=1).
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p
import rule_r3
rows=[]
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    rows.append((r,a,m))
def weight(a): return 8 if len(a)==0 else 9-len(a)
def count(pred_threshold_fn, name, rset=range(2,7)):
    e=collections.Counter(); ew=collections.Counter()
    for r,a,m in rows:
        if r not in rset: continue
        th=pred_threshold_fn(r,a)   # predicted: unimodal iff b<=th
        for b in range(1,61):
            if (b<=th)!=bool((m>>(b-1))&1): e[r]+=1; ew[r]+=weight(a)
    print(name, 'errors by r (distinct/boxweighted):', {r:(e[r],ew[r]) for r in rset}, 'total', sum(e.values()), sum(ew.values()))
    return sum(e.values()), sum(ew.values())
res={}
# C1: conjecture iff
res['CONJ_IFF']=count(lambda r,a: 1+sum(v//r for v in a), 'CONJ_IFF b<=1+F')
# C_tail: proven upper bound Bup=1+floor((D+1-2j*)/r)
def bup(r,a):
    p=_p(a); D=len(p)-1; S=[sum(p[t::r]) for t in range(r)]
    js=max(j for j in range(r) if S[j]>S[(j-1)%r]); return 1+(D+1-2*js)//r
res['TAIL']=count(bup,'TAIL b<=1+floor((D+1-2j*)/r)')
res['TAIL_r<=3']=count(bup,'TAIL on domain r<=3',rset=[2,3])
res['R3']=count(lambda r,a: 1+sum(v//3 for v in a)+2*(sum(1 for v in a if v%3==2)//6),'R3 closed form',rset=[3])
# C_simple_D: proven-necessary weak bound b<=1+floor((D+1)/r)
res['DBOUND']=count(lambda r,a: 1+(sum(v-1 for v in a)+1)//r,'DBOUND b<=1+floor((D+1)/r)')
# C_Sonly: best possible lookup (r,S)->threshold offset T, predict b<=1+F+T, T chosen by majority (fitted)
tab=collections.defaultdict(collections.Counter)
for r,a,m in rows:
    B=0
    while B<60 and (m>>B)&1: B+=1
    tab[(r,sum(v%r-1 for v in a))][B-sum(v//r for v in a)]+=1
best={k:c.most_common(1)[0][0] for k,c in tab.items()}
print("S-only lookup table entries (free params):",len(best))
res['SONLY']=count(lambda r,a: sum(v//r for v in a)+best[(r,sum(v%r-1 for v in a))],'SONLY best lookup (r,S)->B-F')
