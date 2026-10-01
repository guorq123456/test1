import sys
seq = {}
for line in open(sys.argv[1]):
    i,v = line.split(); seq[int(i)] = int(v)
N = max(seq)
# e_n by recurrence
e = [0,5]
while len(e) < N+3: e.append(10*e[-1]-e[-2]+4)
bad = [n for n in range(1,N+1) if seq[n] != e[n+1]]
print("terms", N, "mismatches vs e_{n+1}:", bad[:10])
def readb(fn):
    d={}
    for line in open(fn):
        line=line.strip()
        if not line or line.startswith('#'): continue
        i,v=line.split()[:2]; d[int(i)]=int(v)
    return d
b228 = readb("b228016.txt"); b087 = readb("b087125.txt")
print("A228016 b-file range", min(b228), max(b228), "mismatch vs computed:", [n for n in b228 if seq.get(n)!=b228[n]])
print("A087125 b-file range", min(b087), max(b087), "mismatch vs e_n:", [n for n in b087 if b087[n]!=e[n]])
print("A087125(n+1) vs computed A228016(n) for n<=999:", [n for n in range(1,1000) if b087[n+1]!=seq[n]])
# data lines
S="54,539,5340,52865,523314,5180279,51279480,507614525,5024865774,49741043219,492385566420,4874114620985,48248760643434,477613491813359,4727886157490160,46801248083088245,463284594673392294,4586044698650834699,45397162391834954700"
d=[int(x) for x in S.split(',')]
print("A228016 data (", len(d), "terms) match:", d==[seq[n] for n in range(1,len(d)+1)])
