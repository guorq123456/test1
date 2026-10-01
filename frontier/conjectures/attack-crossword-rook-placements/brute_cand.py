import itertools, sys
def std(s):
    r = sorted(s); return tuple(r.index(x)+1 for x in s)
def skew_merged(w):
    for c in itertools.combinations(w, 4):
        if std(c) in ((3,4,1,2), (2,1,4,3)): return False
    return True
def dels(w):
    n = len(w)
    yield std(w[1:]); yield std(w[:-1])
    yield std(tuple(x for x in w if x != 1)); yield std(tuple(x for x in w if x != n))
for N in range(4, int(sys.argv[1])+1):
    cand = [w for w in itertools.permutations(range(1, N+1))
            if not skew_merged(w) and all(skew_merged(d) for d in dels(w))]
    print(N, len(cand))
    if N == 9:
        out = sorted(" ".join(map(str, w)) for w in cand)
        open("brute_cand9.txt", "w").write("\n".join(out) + "\n")
