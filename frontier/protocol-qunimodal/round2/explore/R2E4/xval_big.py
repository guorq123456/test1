# cross-validate s2big against fam_equal.out (python big-int results) and against tools/uni on random small instances
import json,subprocess,random,sys
sys.path.insert(0,'.')
rows=[json.loads(l) for l in open('fam_equal.out')]
random.seed(5); samp=random.sample(rows,4000)
inp=''.join(f"{r} {k} {' '.join([str(a)]*k)}\n" for (r,a,k,*_) in samp)
out=subprocess.run(['./s2big'],input=inp,capture_output=True,text=True).stdout.strip().split('\n')
bad=0
for row,o in zip(samp,out):
    F,T6,Bs,shape,par=map(int,o.split('|')[1].split()[:5])
    sh={'interval':0,'gap':1,'bad':2}[row[4]]
    if (F,T6,Bs,shape)!=(row[7],row[8],row[6],sh): bad+=1
print('equal-family sample',len(samp),'mismatch',bad)
# vs uni on random small instances: membership of each b in pattern
lines=[];exp=[]
insts=[]
for _ in range(3000):
    r=random.randint(4,12); k=random.randint(3,8); a=sorted(random.choice([v for v in range(1,25) if v%r]) for _ in range(k)); insts.append((r,a))
out=subprocess.run(['./s2big'],input=''.join(f"{r} {len(a)} {' '.join(map(str,a))}\n" for r,a in insts),capture_output=True,text=True).stdout.strip().split('\n')
for (r,a),o in zip(insts,out):
    F,T6,Bs,shape,par=map(int,o.split('|')[1].split()[:5]); pat=o.split('|')[1].split()[5]
    for j,ch in enumerate(pat):
        b=F+1+j; lines.append(f"{r} {len(a)} {' '.join(map(str,a))} {b}"); exp.append(ch)
u=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
print('vs uni: cases',len(exp),'mismatch',sum(1 for e,x in zip(exp,u) if e!=x))
