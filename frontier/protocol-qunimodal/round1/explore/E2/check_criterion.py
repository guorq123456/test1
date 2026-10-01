# Verify the exact reduction criterion and the Fourier tau formula against ground truth on a box sample
import sys, itertools, random
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import *
random.seed(1)
bad=0; tot=0; badtau=0
for r in range(2,7):
    for k in range(1,5):
        for a in itertools.combinations_with_replacement(range(1,13),k):
            a=list(a)
            if tau(r,a)!=tau_fourier(r,a): badtau+=1
            for b in range(1,61):
                if k>=3 and random.random()>0.15: continue
                tot+=1
                if criterion(r,a,b)!=truth(r,a,b): bad+=1; print("MISMATCH",r,a,b)
print("tested",tot,"mismatches",bad,"tau fourier mismatches",badtau)
