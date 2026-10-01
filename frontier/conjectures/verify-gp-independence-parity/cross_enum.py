import subprocess
from dp_bigint import run
cnt=0
for k in range(1,10):
    res = run(k, 21)
    for n in range(2*k+1, 22):
        out = subprocess.run(['./enum',str(n),str(k)],capture_output=True,text=True).stdout.split()
        c = list(map(int,out[2].split(',')))
        assert c == res[n], (n,k)
        cnt+=1
print('match', cnt)
