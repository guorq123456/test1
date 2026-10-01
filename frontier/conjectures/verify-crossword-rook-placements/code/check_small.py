from rp import *
import itertools, random
bad = 0
for n in range(1, 7):
    for p in itertools.permutations(range(1, n+1)):
        w = list(p)
        a = brute(w); b = grid_dp(w); c = perm_generic(biadj(w))
        if not (a == b == c): bad += 1; print("MISMATCH", w, a, b, c)
print("S1..S6 checked, mismatches:", bad)
random.seed(1)
for t in range(300):
    n = random.randint(7, 9)
    w = random.sample(range(1, n+1), n)
    a = brute(w); b = grid_dp(w); c = perm_generic(biadj(w))
    if not (a == b == c): bad += 1; print("MISMATCH", w, a, b, c)
print("random 7..9 checked, mismatches:", bad)
