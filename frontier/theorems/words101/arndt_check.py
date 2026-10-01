# Check J. Arndt's comment in A225034: weakly increasing words with no up-step equal to 1.
from itertools import combinations_with_replacement as cwr
a = [int(l) for l in open("/tmp/claude-0/deep/words101/a225034_dp.txt")]
def cnt(L, K):
    return sum(1 for w in cwr(range(K), L) if all(w[i+1]-w[i] != 1 for i in range(L-1)))
for n in range(0, 12):
    print(n, a[n], "len n, n+2 letters:", cnt(n, n+2), " len n+1, n+2 letters:", cnt(n+1, n+2))
