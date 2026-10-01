import numpy as np
N=60
H0=2*N+1; W=2*H0+1
def evolve(code):
    a=np.zeros((W,W),dtype=np.int64); a[H0,H0]=1
    st=[(a.copy(),H0)]
    for t in range(1,N+1):
        H=H0-t
        b=np.zeros_like(a)
        sl=slice(H0-H,H0+H+1)
        c=a[sl,sl]
        s=a[H0-H-1:H0+H,sl]+a[H0-H+1:H0+H+2,sl]+a[sl,H0-H-1:H0+H]+a[sl,H0-H+1:H0+H+2]
        v=c+2*s
        b[sl,sl]=(code>>v)&1
        a=b
        st.append((a.copy(),H))
    return st
S451=evolve(451); S193=evolve(193)
# index: arr[y+H0, x+H0]
yy,xx=np.mgrid[-H0:H0+1,-H0:H0+1]
diam=np.abs(xx)+np.abs(yy)
counts=[]
ok_bg=True; ok_d4=True
for t in range(N+1):
    A,H=S451[t]; B,_=S193[t]
    m=(np.abs(xx)<=H)&(np.abs(yy)<=H)
    # Lemma 1: outside diamond radius t, equals t mod 2 (within exact box)
    for X in (A,B):
        out=m&(diam>t)
        if not np.all(X[out]==t%2): ok_bg=False
        sub=X[H0-H:H0+H+1,H0-H:H0+H+1]
        for T in (sub[::-1,:],sub[:,::-1],sub.T):
            if not np.array_equal(T,sub): ok_d4=False
    counts.append(int(np.sum((A!=B)&m)))
print('Lemma1 background ok', ok_bg, 'D4 ok', ok_d4)
print('diff counts stage 0..40:', counts[:41])
claimed={0:0,1:1,17:4,21:12,22:8,23:0,24:16,25:28,26:60,27:132,28:140,29:100,30:217}
for t in range(2,17): claimed[t]=0
for t in (18,19,20): claimed[t]=0
print('table matches:', all(counts[t]==claimed[t] for t in claimed))
# stage 16 picture
pic="""................#................
................#................
................#................
...............###...............
..............#####..............
.............#######.............
............#########............
...........####.#.####...........
..........####.....####..........
.........#####.....#####.........
........######.....######........
.......#######.....#######.......
......########.....########......
.....#########.....#########.....
....####......#.#.#......####....
...####........###........####...
########......#####......########
...####........###........####...
....####......#.#.#......####....
.....#########.....#########.....
......########.....########......
.......#######.....#######.......
........######.....######........
.........#####.....#####.........
..........####.....####..........
...........####.#.####...........
............#########............
.............#######.............
..............#####..............
...............###...............
................#................
................#................
................#................""".split()
A,_=S451[16]; B,_=S193[16]
print('stage16 identical', np.array_equal(A,B))
mine=[''.join('#' if A[y+H0,x+H0] else '.' for x in range(-16,17)) for y in range(16,-17,-1)]
print('stage16 picture matches', mine==pic)
# isolated ON / surrounded OFF cells in common configs (stages where configs equal)
def special(X,H):
    sl=slice(H0-H+1,H0+H)
    c=X[sl,sl]; s=X[H0-H:H0+H-1,sl]+X[H0-H+2:H0+H+1,sl]+X[sl,H0-H:H0+H-1]+X[sl,H0-H+2:H0+H+1]
    iso=np.argwhere((c==1)&(s==0)); sur=np.argwhere((c==0)&(s==4))
    off=H0-H+1
    f=lambda L:[(int(p[1]+off-H0),int(p[0]+off-H0)) for p in L]
    return f(iso),f(sur)
for t in range(2,24):
    A,H=S451[t]; B,_=S193[t]
    m=(np.abs(xx)<=H)&(np.abs(yy)<=H)
    if np.array_equal(A[m],B[m]):
        iso,sur=special(A,H)
        if iso or sur: print('stage',t,'common config: isolated ON',iso,'surrounded OFF',sur)
# certificate cells
A23,_=S451[23]; B23,_=S193[23]
print('stage23 identical', np.array_equal(A23,B23))
rows={3:[(3,)],}
D=[(x,y) for x in range(0,7) for y in range(-3,4) if abs(x-3)+abs(y)<=3]
print('stage23 diamond:', {p:int(A23[p[1]+H0,p[0]+H0]) for p in D})
for t in (24,25,26):
    A,_=S451[t]; B,_=S193[t]
    r=26-t
    cells=[(x,y) for x in range(3-r,4+r) for y in range(-r,r+1) if abs(x-3)+abs(y)<=r]
    print('stage',t,'451:',{p:int(A[p[1]+H0,p[0]+H0]) for p in cells})
    print('stage',t,'193:',{p:int(B[p[1]+H0,p[0]+H0]) for p in cells})
# stage 26 x-axis
A,_=S451[26];B,_=S193[26]
print(''.join(str(A[H0,H0+x]) for x in range(27)), ''.join(str(B[H0,H0+x]) for x in range(27)))
# diff cells stage 17
A,_=S451[17];B,_=S193[17]
print('stage17 diff cells', [(int(p[1]-H0),int(p[0]-H0)) for p in np.argwhere(A!=B)])
# rule 449 side check
S449=evolve(449)
d449_193=[t for t in range(2,N+1) if not np.array_equal(S449[t][0][H0,H0:H0+t+1],S193[t][0][H0,H0:H0+t+1])]
d449_451=[t for t in range(2,N+1) if not np.array_equal(S449[t][0][H0,H0:H0+t+1],S451[t][0][H0,H0:H0+t+1])]
print('449 vs 193 first diff n>=2', d449_193[:3], ' 449 vs 451 first diff', d449_451[:3])
