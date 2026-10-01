# For r=3, no 3|a_i, fit box (k<=8, a_i<=12, b<=60):
# (1) confirm unimodal set is always an initial segment [1..B]
# (2) test candidate formulas for B and report error counts (number of (a,b) pairs misclassified, b=1..60)
import itertools, collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
D=[(tuple(map(int,a.split(','))),bs) for a,bs,B,t in rows]
def stats(a):
    T=sum(x//3 for x in a); n1=sum(1 for x in a if x%3==1); n2=sum(1 for x in a if x%3==2)
    M=sum(x-1 for x in a)
    return T,n1,n2,M
cands={
 'C0_conj: 1+T': lambda a: 1+stats(a)[0],
 'C1: 1+T+2[n2>=6]': lambda a: 1+stats(a)[0]+2*(stats(a)[2]>=6),
 'C2: 1+T+2*floor(n2/6)': lambda a: 1+stats(a)[0]+2*(stats(a)[2]//6),
 'C3: 1+(M-(n2 mod 6))/3': lambda a: 1+(stats(a)[3]-stats(a)[2]%6)//3,
 'C4: 1+floor(M/3)': lambda a: 1+stats(a)[3]//3,
 'C5: 1+T+floor(n2/3)': lambda a: 1+stats(a)[0]+stats(a)[2]//3,
 'C6: 1+T+[n2>=6]': lambda a: 1+stats(a)[0]+(stats(a)[2]>=6),
 'C7: 1+T+2[#(a_i=2)>=6]': lambda a: 1+stats(a)[0]+2*(sum(1 for x in a if x==2)>=6),
 'C8: 1+T+2[#(a_i in{2,5})>=6]': lambda a: 1+stats(a)[0]+2*(sum(1 for x in a if x in(2,5))>=6),
 'C9: 1+T+2[k>=6 and n1==0]': lambda a: 1+stats(a)[0]+2*(len(a)>=6 and stats(a)[1]==0),
 'C10: 1+T+2[n2-n1>=4]': lambda a: 1+stats(a)[0]+2*(stats(a)[2]-stats(a)[1]>=4),
}
thr=all(('1' not in bs[bs.find('0'):]) if '0' in bs else True for a,bs in D)
print('all instances threshold-type:',thr, ' multisets:',len(D),' (a,b) pairs:',60*len(D))
res={}
for name,f in cands.items():
    err=0
    for a,bs in D:
        B=f(a)
        for b in range(1,61):
            if (b<=B)!=(bs[b-1]=='1'): err+=1
    res[name]=err
    print(f"{name:40s} errors={err}")
