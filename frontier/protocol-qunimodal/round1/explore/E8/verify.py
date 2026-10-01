# Cross-check data.tsv against ground truth /tmp/claude-0/qu/tools/uni on a random sample (all within fit box)
import random, subprocess
rows=[l.rstrip('\n').split('\t') for l in open('data.tsv')]
random.seed(1)
qs=[]; exp=[]
for _ in range(20000):
    a,bs,B,t=random.choice(rows); b=random.randint(1,60)
    al=a.split(','); qs.append(f"3 {len(al)} {' '.join(al)} {b}"); exp.append(bs[b-1])
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(qs)+'\n',capture_output=True,text=True).stdout.split()
print('checked',len(qs),'mismatches',sum(1 for x,y in zip(out,exp) if x!=y))
