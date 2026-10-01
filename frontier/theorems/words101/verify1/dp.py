# Own DP for A225034 straight from the definition.
# Build words left to right; state = (#ones i, #zeros j, suffix class)
# suffix class: 0 = empty word or ends in 0 not preceded by "1" (i.e. no dangerous suffix),
#               1 = ends in 1, 2 = ends in "10".
import sys
N = int(sys.argv[1]) if len(sys.argv)>1 else 1200
# W[i][j] = number of 101-avoiding words with i ones, j zeros (j<=N)
# iterate over i (ones) then j (zeros) in increasing total length order: process cell (i,j) after (i-1,j),(i,j-1)
s0 = [[0]*(N+1) for _ in range(N+1)]
s1 = [[0]*(N+1) for _ in range(N+1)]
s2 = [[0]*(N+1) for _ in range(N+1)]
s0[0][0] = 1
for i in range(N+1):
    r0, r1, r2 = s0[i], s1[i], s2[i]
    p0 = s0[i-1] if i>0 else None
    p1 = s1[i-1] if i>0 else None
    for j in range(N+1):
        if i==0 and j==0: continue
        # last letter 0: from (i,j-1)
        if j>0:
            # append 0: state0 -> 0, state1 -> 2, state2 -> 0
            r0[j] += r0[j-1] + r2[j-1]
            r2[j] += r1[j-1]
        # last letter 1: from (i-1,j)
        if i>0:
            # append 1: state0 -> 1, state1 -> 1, state2 -> forbidden
            r1[j] += p0[j] + p1[j]
a = []
for n in range(N+1):
    a.append(sum(s0[n][m]+s1[n][m]+s2[n][m] for m in range(n+1)))
with open('a_dp.txt','w') as f:
    for n,v in enumerate(a): f.write(f"{n} {v}\n")
print(a[:16])
