# Test: is delta=(1-q)A unimodal (weakly) on [0,(D+1)/2] for A=prod [a_i]_q ?
import sys, itertools, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import poly_a
def is_unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
if __name__=="__main__":
    cnt=0;bad=[]
    for k in range(1,7):
        for a in itertools.combinations_with_replacement(range(2,16),k):
            A=poly_a(list(a)); D=len(A)-1
            dl=[A[j]-(A[j-1] if j>0 else 0) for j in range(0,(D+1)//2+1)]
            cnt+=1
            if not is_unimodal(dl): bad.append(a)
    print("exhaustive k<=6 a<=15:",cnt,"nonunimodal",len(bad)); print(bad[:20])
