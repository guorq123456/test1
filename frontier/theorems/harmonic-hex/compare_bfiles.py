# Compare A228016 (data + b-file) with A087125(n+1) and with the recurrence e_n = 10 e_{n-1} - e_{n-2} + 4
import re, subprocess
def bfile(fn):
    d={}
    for line in open(fn):
        line=line.strip()
        if not line or line.startswith('#'): continue
        n,v=line.split()[:2]; d[int(n)]=int(v)
    return d
A=bfile('b228016.txt'); B=bfile('b087125.txt')
e=[0,5]
while len(e)<1100: e.append(10*e[-1]-e[-2]+4)
assert all(B[n]==e[n] for n in B), "A087125 b-file != recurrence"
assert all(A[n]==e[n+1] for n in A), "A228016 b-file != A087125(n+1)"
print("A087125 b-file n=0..%d matches e_n; A228016 b-file n=1..%d matches e_{n+1}"%(max(B),max(A)))
# stored data lines
txt=subprocess.run(['git','-C','/tmp/claude-0/oeis/oeisdata','show','HEAD:seq/A228/A228016.seq'],capture_output=True,text=True).stdout
data=[int(x) for x in ''.join(l[11:] for l in txt.splitlines() if l[:2] in('%S','%T','%U')).split(',') if x]
assert data==e[2:2+len(data)]; print("A228016 %%S/T/U data (%d terms) matches"%len(data))
