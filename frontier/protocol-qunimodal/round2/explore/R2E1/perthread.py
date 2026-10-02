# Per-thread S2-type properties: for each thread, OK set over beta in [1-F, ...].
import sys, itertools, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
C=Counter(); ex={}
def check(r,a):
    T=Thr(r,a)
    bmax=(T.D+1)//r+4
    for th in T.threads:
        S=[b for b in range(1,bmax+1) if T.ok_thread(th,b-T.F)]
        Sset=set(S)
        for b in S:
            beta=b-T.F
            if beta%2==0 and b+1<=bmax and b+1 not in Sset:
                C['i_fail']+=1; ex.setdefault('i_fail',(r,a,th,S,T.F))
            if b-2>=1 and b-2 not in Sset:
                C['A_fail']+=1; ex.setdefault('A_fail',(r,a,th,S,T.F))
            if beta%2==1 and b-3>=1 and b-3 not in Sset:
                C['C_fail']+=1; ex.setdefault('C_fail',(r,a,th,S,T.F))
        C['threads']+=1
for r in range(3,9):
    vals=[x for x in range(2,2*r+3) if x%r]
    for k in range(1,6):
        for a in itertools.combinations_with_replacement(vals,k):
            check(r,list(a))
print(C)
for k,v in ex.items(): print(k,v)
