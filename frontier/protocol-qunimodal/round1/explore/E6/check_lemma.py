# Numerical check of proof_r2_tie.txt inside the box: r=2, all a_i odd (k<=8, a_i<=11), D>=2, b=1+sum floor(a_i/2):
# c_{D-1}==c_{D-2}, and dA_{D-1}<0 when k'>=2 entries are >=3.
from itertools import combinations_with_replacement
import sys; sys.path.insert(0,'/tmp/claude-0/qu/tools'); from uni_ref import poly
n=ok=cont=0
for k in range(1,9):
    for a in combinations_with_replacement([1,3,5,7,9,11],k):
        D=sum(x-1 for x in a)
        if D<2: continue
        b=1+sum(x//2 for x in a); c=poly(2,list(a),b); n+=1; ok+= (c[D-1]==c[D-2])
print("instances",n,"tie_at_D-2",ok)
