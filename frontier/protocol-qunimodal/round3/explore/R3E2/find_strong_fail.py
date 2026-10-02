# search residue multisets rho' (parts in [2,r-1]) failing the strong certificate (mu_neg)
import itertools,sys
from reslev import *
out=[]
for r in range(4,9):
    for kp in range(2,13):
        cnt=0
        for rho in itertools.combinations_with_replacement(range(2,r),kp):
            c=certificate(r,list(rho),strong=True)
            if not (c['TP'] and c['E'] and c['O']):
                out.append((r,rho,c)); cnt+=1
        if cnt: print(r,kp,cnt,out[-1][1],out[-1][2],flush=True)
        if cnt>0 and kp>=8: break
