# test rule_allequal_middle.predict against (1) all generated data, (2) random gt_big instances; fit box only
import glob,random,sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from rule_allequal_middle import predict, domain
err=0;tot=0
for f in glob.glob('data/U_r*.txt')+glob.glob('data2/U_r*.txt'):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=set(x[6:])
        a=[n*r+s]*k
        assert domain(r,a)
        for b in range(1,T6+3):
            tot+=1
            if predict(r,a,b)!=(b in U): err+=1
print('data check: (instance,b) pairs',tot,'errors',err)
random.seed(7); err2=0;tot2=0
for t in range(400):
    r=random.randint(4,30); s=random.randint(2,r-2); n=random.randint(0,(100-s)//r); k=random.randint(3,40)
    a=[n*r+s]*k; F=k*n
    bs=list(range(max(1,F-2),F+(k*(s-1))//r+4))
    pr=profile(r,a,bs)
    for b,v in zip(bs,pr):
        tot2+=1
        if predict(r,a,b)!=v: err2+=1; print('ERR',r,a[0],k,b,v)
print('random gt_big check: pairs',tot2,'errors',err2)
