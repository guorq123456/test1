# pattern of unimodal levels m=b-1-Q in [-(Q), 7] ; report patterns for m>=0
from load import *
from collections import Counter
for r in range(2,7):
    C=Counter()
    for a,mask in load(r):
        Q=sum(x//r for x in a)
        pat=''.join('1' if (mask>>(Q+m))&1 else '0' for m in range(0,8))
        neg=all((mask>>(b-1))&1 for b in range(1,Q+1))
        C[(neg,pat)]+=1
    print(r,sorted(C.items()))
