"""Brute-force count of directed animals (A005773 definition) on the square lattice:
finite sets S of cells containing the root (0,0) such that every cell of S is reachable
from the root by unit North/East steps staying inside S.
Growth: every animal of size k+1 arises from an animal of size k by adding one cell
that is a N- or E-neighbour of a cell already in the animal (remove from a (k+1)-animal any
cell having no N/E neighbour in it: what remains is still an animal).  Dedup with a set."""
import sys
K = int(sys.argv[1]) if len(sys.argv) > 1 else 12
SH = 32
def enc(x, y): return x * SH + y
level = {frozenset([enc(0, 0)])}
print(1, len(level))
for k in range(2, K + 1):
    nxt = set()
    for S in level:
        for c in S:
            for d in (SH, 1):  # East (x+1), North (y+1)
                c2 = c + d
                if c2 not in S:
                    nxt.add(S | {c2})
    level = nxt
    print(k, len(level), flush=True)
