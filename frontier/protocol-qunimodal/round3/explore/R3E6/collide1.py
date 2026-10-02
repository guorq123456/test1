# Pairs X={1,y,z}, Y={x,u,v} (all of Y >= 2, all <=400) with equal sum and product
# (y z = x u v, 1+y+z = x+u+v). Residue condition is checked later per r. Output coll1_all.txt
from math import isqrt
def divs(n):
    out=[]; i=1
    while i*i<=n:
        if n%i==0:
            out.append(i)
            if i*i!=n: out.append(n//i)
        i+=1
    return out
out=open('/tmp/claude-0/qu/explore3/R3E6/coll1_all.txt','w'); n=0
for y in range(2,401):
    for z in range(y,401):
        P=y*z; S=1+y+z
        for x in divs(P):
            if x<2 or x*x*x>P: continue
            Q=P//x; T=S-x
            disc=T*T-4*Q
            if disc<0: continue
            sq=isqrt(disc)
            if sq*sq!=disc or (T+sq)%2: continue
            u=(T-sq)//2; v=(T+sq)//2
            if u>=x and v<=400:
                out.write(f"{y} {z} {x} {u} {v}\n"); n+=1
print(n)
