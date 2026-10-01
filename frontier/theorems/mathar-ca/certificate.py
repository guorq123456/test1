from transparent import evolve, f451, f193, state, NB
H = {451: evolve(f451, 26), 193: evolve(f193, 26)}
def pic(h, R, mark=None):
    out=[]
    for y in range(R, -R-1, -1):
        out.append(''.join(('#' if state(h,(x,y)) else '.') for x in range(-R, R+1)))
    return '\n'.join(out)
z=(3,0)
for code in (451,193):
    h=H[code][25]; c=state(h,z); s=sum(state(h,(z[0]+dx,z[1]+dy)) for dx,dy in NB)
    print('rule',code,'stage 25 at (3,0): c=',c,'s=',s,'-> index',c+2*s,'-> new',(code>>(c+2*s))&1, ' (stage 26 actual:',state(H[code][26],z),')')
    print('  neighbours (2,0),(4,0),(3,1),(3,-1):',[state(h,(3+dx,dy)) for dx,dy in ((-1,0),(1,0),(0,1),(0,-1))])
for t in range(16, 27):
    d = sorted(z for z in set(H[451][t][1])|set(H[193][t][1]) if state(H[451][t],z)!=state(H[193][t],z))
    print('stage',t,'#diff',len(d), 'first-quadrant (x>=0,y>=0) diffs:', [p for p in d if p[0]>=0 and p[1]>=0])
print('stage 16 common configuration, |x|,|y|<=16 (row y=16 at top):')
print(pic(H[193][16],16))
assert H[451][16]==H[193][16]
for code in (451,193):
    print('stage 25, rule',code,', |x|,|y|<=25'); print(pic(H[code][25],25))
    print('stage 26, rule',code,', |x|,|y|<=26'); print(pic(H[code][26],26))
