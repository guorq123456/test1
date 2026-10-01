# Hand-checkable certificate: common stage-23 configuration on the diamond |x-3|+|y|<=3,
# then the two rules applied for three steps, restricted to shrinking diamonds.
from transparent import evolve, f451, f193, state, NB
H = {451: evolve(f451, 26), 193: evolve(f193, 26)}
assert H[451][23] == H[193][23]          # configurations coincide at stage 23
X0=3
def window(vals, r):
    lines=[]
    for y in range(3, -4, -1):
        lines.append(' '.join((str(vals[(x,y)]) if abs(x-X0)+abs(y)<=r else ' ') for x in range(X0-3, X0+4)))
    return '\n'.join(lines)
base = {(x,y): state(H[193][23],(x,y)) for x in range(X0-3,X0+4) for y in range(-3,4) if abs(x-X0)+abs(y)<=3}
print('stage 23 (common), x =',X0-3,'..',X0+3,' (left to right), y = 3..-3 (top to bottom):')
print(window(base,3))
for code,f in ((451,f451),(193,f193)):
    cur = dict(base)
    for k,t in enumerate((24,25,26)):
        r = 2-k
        new = {}
        for (x,y) in cur:
            if abs(x-X0)+abs(y) <= r:
                c = cur[(x,y)]; s = sum(cur[(x+dx,y+dy)] for dx,dy in NB)
                new[(x,y)] = f(c,s)
                assert new[(x,y)] == state(H[code][t],(x,y))
        cur = new
        print(f'rule {code}, stage {t}:'); print(window(cur, r))
