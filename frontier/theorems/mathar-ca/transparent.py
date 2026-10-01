# Third, deliberately naive implementation: infinite plane stored as (background bit, set of cells
# whose state differs from the background).  Rules written as Boolean formulas decoded by hand:
#   193 = 2^0+2^6+2^7       : new = 1  iff (c=0 and s=0) or s=3
#   451 = 2^0+2^1+2^6+2^7+2^8: new = 1 iff s=0 or s=3 or (c=0 and s=4)
# (index v = c+2s;  v=0 <-> (0,0), v=1 <-> (1,0), v=6 <-> (0,3), v=7 <-> (1,3), v=8 <-> (0,4)).
def f193(c,s): return int((c==0 and s==0) or s==3)
def f451(c,s): return int(s==0 or s==3 or (c==0 and s==4))
NB = ((1,0),(-1,0),(0,1),(0,-1))
def evolve(f, T):
    bg, D = 0, {(0,0)}            # stage 0: single ON cell, background OFF
    hist = [(bg, frozenset(D))]
    for t in range(T):
        st = lambda z: bg ^ (z in D)
        cand = set(D) | {(x+dx,y+dy) for (x,y) in D for dx,dy in NB}
        nbg = f(bg, 4*bg)
        nD = set()
        for (x,y) in cand:
            c = st((x,y)); s = sum(st((x+dx,y+dy)) for dx,dy in NB)
            if f(c,s) != nbg: nD.add((x,y))
        # cells outside cand have c=bg and all neighbours bg, so they take nbg: consistent.
        bg, D = nbg, nD
        hist.append((bg, frozenset(D)))
    return hist
def state(h, z): bg, D = h; return bg ^ (z in D)
def right(h, n): return ''.join(str(state(h,(x,0))) for x in range(n+1))
if __name__ == '__main__':
    T = 40
    H = {451: evolve(f451, T), 193: evolve(f193, T)}
    from repro import bfile
    for A, code in [('282297',451),('279721',193)]:
        b = bfile(A)
        print('A'+A, 'transparent sim matches b-file for n<=%d:'%T, all(int(right(H[code][n],n))==b[n] for n in range(T+1)))
    for A, code in [('282295',451),('279720',193)]:
        b = bfile(A)
        print('A'+A, 'transparent sim (left readout) matches b-file for n<=%d:'%T,
              all(int(''.join(str(state(H[code][n],(x,0))) for x in range(-n,1)))==b[n] for n in range(T+1)))
    for n in range(T+1):
        same_axis = right(H[451][n],n)==right(H[193][n],n)
        full = {z for z in set(H[451][n][1])|set(H[193][n][1])} 
        ndiff = sum(1 for z in full if state(H[451][n],z)!=state(H[193][n],z)) if H[451][n][0]==H[193][n][0] else None
        print(n, 'bg', H[451][n][0], H[193][n][0], 'x-axis equal' if same_axis else 'x-axis DIFFER', 'cells differing:', ndiff)
