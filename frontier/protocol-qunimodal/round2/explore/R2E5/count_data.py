# counts of computed instances (full Thm-A scans, validated by validate.py) by source and n
import glob
from collections import Counter
C=Counter()
for f in glob.glob('data*/U_r*.txt'):
    src=f.split('/')[0]
    for line in open(f):
        n=int(line.split()[2]); C[(src,'n=0' if n==0 else 'n>=1')]+=1
for k in sorted(C): print(k,C[k])
print('total',sum(C.values()),' n>=1 total',sum(v for k,v in C.items() if k[1]=='n>=1'))
