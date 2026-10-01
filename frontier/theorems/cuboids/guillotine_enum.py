"""guillotine_enum.py -- computes A386884(n) (strict=1) or A384311(n) (strict=0) by enumerating ALL
hierarchical guillotine decompositions of the n-cube into 4 boxes with integer cut positions.
Relies only on Theorem 1 of proof.md (every tiling of a box by <=4 boxes has a guillotine plane,
hence, recursively, is a hierarchical guillotine decomposition) -- not on Theorem 2 or the counting.
Usage: python3 guillotine_enum.py NMIN NMAX strict"""
import sys
from functools import lru_cache
from structure_count import closed, oeis_terms

def run(n, strict):
    def ok_leaf(b):
        return (b[0] < b[1] < b[2]) if strict else True
    @lru_cache(maxsize=None)
    def dec(box, k):
        # box: sorted tuple of side lengths; returns frozenset of sorted k-tuples of sorted shapes
        if k == 1:
            return frozenset([(box,)]) if ok_leaf(box) else frozenset()
        out = set()
        for d in range(3):
            if d > 0 and box[d] == box[d - 1]:
                continue          # same side length: same family of cuts
            L = box[d]
            for h in range(1, L):
                b1 = list(box); b1[d] = h; b1 = tuple(sorted(b1))
                b2 = list(box); b2[d] = L - h; b2 = tuple(sorted(b2))
                for k1 in range(1, k):
                    A = dec(b1, k1)
                    if not A: continue
                    B = dec(b2, k - k1)
                    for a in A:
                        for b in B:
                            out.add(tuple(sorted(a + b)))
        return frozenset(out)
    res = dec((n, n, n), 4)
    return sum(1 for c in res if len(set(c)) == 4)

if __name__ == '__main__':
    n0, n1, strict = map(int, sys.argv[1:4])
    db = oeis_terms('A386884' if strict else 'A384311')
    for n in range(n0, n1 + 1):
        c = run(n, strict)
        ref = closed(n) if strict else None
        stored = db[n - 1] if n - 1 < len(db) else None
        print(n, c, 'formula:', ref, 'stored:', stored,
              'OK' if (ref is None or c == ref) and (stored is None or c == stored) else 'MISMATCH', flush=True)
