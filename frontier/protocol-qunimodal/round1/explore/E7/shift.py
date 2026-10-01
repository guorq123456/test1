# Test "shift invariance": unimodal(r,a,b) == unimodal(r, a with one a_i -> a_i+r, b+1), all pairs inside the box.
import collections
U={}
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    U[(r,a)]=m
tot=0; bad=0; badex=[]; badc=collections.Counter()
for (r,a),m in U.items():
    for i in range(len(a)):
        if i>0 and a[i]==a[i-1]: continue
        a2=tuple(sorted(a[:i]+(a[i]+r,)+a[i+1:]))
        if (r,a2) not in U: continue
        m2=U[(r,a2)]
        for b in range(1,60):
            tot+=1
            u1=(m>>(b-1))&1; u2=(m2>>b)&1
            if u1!=u2:
                bad+=1; badc[r]+=1
                if len(badex)<20: badex.append((r,a,b,u1,a2,b+1,u2))
print("pairs tested",tot,"disagreements",bad,dict(badc))
for e in badex: print(e)
print("--- breakdown of disagreements by shifted value a_i ---")
cc=collections.Counter()
for (r,a),m in U.items():
    for i in range(len(a)):
        if i>0 and a[i]==a[i-1]: continue
        a2=tuple(sorted(a[:i]+(a[i]+r,)+a[i+1:]))
        if (r,a2) not in U: continue
        m2=U[(r,a2)]
        for b in range(1,60):
            if ((m>>(b-1))&1)!=((m2>>b)&1): cc[(r,a[i],'u1=%d'%((m>>(b-1))&1))]+=1
print(cc)
