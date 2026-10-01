# Emit every instance of the sufficiency region b <= 1+sum floor(a_i/r) in the fit box
# (r given on argv, 1<=k<=8, 1<=a_i<=12 as sorted multisets, 1<=b<=min(60,1+S)),
# one line "r k a1..ak b" per instance, for the ground-truth checker /tmp/claude-0/qu/tools/uni.
import sys
from itertools import combinations_with_replacement
r=int(sys.argv[1]); out=[]; w=sys.stdout.write
for k in range(1,9):
    for a in combinations_with_replacement(range(1,13),k):
        S=sum(x//r for x in a); pre=f"{r} {k} "+" ".join(map(str,a))+" "
        w("".join(pre+f"{b}\n" for b in range(1,min(60,1+S)+1)))
