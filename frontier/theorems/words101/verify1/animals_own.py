# directed site animals on square lattice rooted at (0,0), steps (1,0),(0,1)
import sys
M = int(sys.argv[1])
level = {frozenset([(0,0)])}
res=[1]
for n in range(2,M+1):
    nxt=set()
    for A in level:
        for (x,y) in A:
            for c in ((x+1,y),(x,y+1)):
                if c not in A:
                    nxt.add(A|{c})
    level=nxt
    res.append(len(level))
    print(n,len(level),flush=True)
print(res)
