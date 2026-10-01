# Error count of rule_r3.predict on the fit box (r=3, 3 does not divide a_i, k<=8, a_i<=12, b<=60) against data.tsv,
# plus a 20000-pair random cross-check against the ground-truth binary /tmp/claude-0/qu/tools/uni.
import sys, random, subprocess
sys.path.insert(0,'/tmp/claude-0/qu/explore/E8')
from rule_r3 import predict, domain
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
err=0; n=0
for a,bs,B,t in rows:
    a=sorted(map(int,a.split(','))); assert domain(3,a)
    for b in range(1,61):
        n+=1; err+= (predict(3,a,b) != (bs[b-1]=='1'))
print('pairs',n,'errors',err)
random.seed(7); qs=[]; pr=[]
vals=[v for v in range(1,13) if v%3]
for _ in range(20000):
    k=random.randint(1,8); a=sorted(random.choice(vals) for _ in range(k)); b=random.randint(1,60)
    qs.append(f"3 {k} {' '.join(map(str,a))} {b}"); pr.append(predict(3,a,b))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(qs)+'\n',capture_output=True,text=True).stdout.split()
print('ground-truth random pairs',len(qs),'errors',sum(1 for o,p in zip(out,pr) if (o=='1')!=p))
