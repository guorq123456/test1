# check S2-shape of E_inf (flat, r<=30,k<=60) and of n=0 sets (data, data2): E=[1,M] or [1,M]\{M-1}, M even; also E_odd vs E_even gap
from flat import flat_fast
import glob
from collections import Counter
def shape(E):
    if not E: return 'empty'
    M=max(E); miss=[x for x in range(1,M+1) if x not in E]
    if M%2: return 'odd-max'
    if not miss: return 'interval'
    if miss==[M-1]: return 'hole'
    return 'other'
cnt=Counter(); gaps=Counter()
for r in range(4,31):
    for s in range(2,r-1):
        for k in range(3,61):
            E=flat_fast(r,s,k); cnt[shape(E)]+=1
            ev=[e for e in E if e%2==0]; od=[e for e in E if e%2==1]
            if ev or od: gaps[(max(ev) if ev else 0)-(max(od) if od else -1)]+=1
print('flat E_inf shapes:',dict(cnt)); print('E_even-E_odd distribution:',dict(gaps))
cnt0=Counter()
for f in glob.glob('data/U_r*.txt')+glob.glob('data2/U_r*.txt'):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=x[6:]
        if n!=0: continue
        E=[b-1-F for b in U if b-1-F>=1]
        cnt0[shape(E)]+=1
print('n=0 shapes:',dict(cnt0))
