# r=3: check (in box) that for n2>=6, b0 = S-1+ceil((n2+1)/3) satisfies b0>1+S and P unimodal (Theorem R3(b)),
# and that the full unimodal b-set equals {1..1+S+2*floor(n2/6)} (Theorem R3(a) + conjectural K>0 part).
tot=ok0=okset=0; n_lt6=0; ok_lt6=0
for L in open('/tmp/claude-0/qu/explore/E2/gt.txt'):
    x=L.split(); r,k=int(x[0]),int(x[1])
    if r!=3: continue
    a=list(map(int,x[2:2+k])); m=int(x[2+k],16)
    if any(v%3==0 for v in a): continue
    S=sum(v//3 for v in a); n2=sum(1 for v in a if v%3==2)
    U=[b for b in range(1,61) if (m>>(b-1))&1]
    bm=1+S+2*(n2//6)
    if U==list(range(1,bm+1)): okset+=1
    tot+=1
    if n2>=6:
        b0=S-1+(-(-(n2+1)//3))
        if b0>1+S and b0 in U: ok0+=1
        n_lt6+=1
print("r=3 (r,a) records",tot,"b-set == {1..1+S+2floor(n2/6)}:",okset,"| n2>=6 records",n_lt6,"with b0>1+S unimodal:",ok0)
