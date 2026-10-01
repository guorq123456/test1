# Recompute the fit-box error count of EVERY candidate tried on this path and write candidates.tsv.
# Fit box used: r=3, no a_i divisible by 3, k=1..8, a_i<=12, b=1..60  (12869 multisets, 772140 (a,b) pairs).
# Error count = number of (a,b) pairs where the candidate's unimodality prediction differs from truth (data.tsv).
# Two kinds of candidates:
#  (F) explicit formulas for the critical b  B(a): predict unimodal iff b<=B(a)
#  (S) statistic sets: best achievable error of ANY threshold rule that is a function of the statistic tuple
#      (per class choose the single threshold minimizing errors).
import collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
D=[(tuple(map(int,a.split(','))),bs) for a,bs,B,t in rows]
def cnt(a,f): return sum(1 for x in a if f(x))
T=lambda a: sum(x//3 for x in a)
M=lambda a: sum(x-1 for x in a)
n1=lambda a: cnt(a,lambda x:x%3==1)
n2=lambda a: cnt(a,lambda x:x%3==2)
F={
 'F00 conj 1+T': lambda a:1+T(a),
 'F01 1+T+2[n2>=6]': lambda a:1+T(a)+2*(n2(a)>=6),
 'F02 1+T+2*floor(n2/6)  [PROPOSED]': lambda a:1+T(a)+2*(n2(a)//6),
 'F03 1+(M-(n2 mod 6))/3 (identical to F02)': lambda a:1+(M(a)-n2(a)%6)//3,
 'F04 1+floor(M/3)': lambda a:1+M(a)//3,
 'F05 1+T+floor(n2/3)': lambda a:1+T(a)+n2(a)//3,
 'F06 1+T+[n2>=6]': lambda a:1+T(a)+(n2(a)>=6),
 'F07 1+T+2[#(a_i=2)>=6]': lambda a:1+T(a)+2*(cnt(a,lambda x:x==2)>=6),
 'F08 1+T+2[#(a_i in{2,5})>=6]': lambda a:1+T(a)+2*(cnt(a,lambda x:x in(2,5))>=6),
 'F09 1+T+2[k>=6 and n1==0]': lambda a:1+T(a)+2*(len(a)>=6 and n1(a)==0),
 'F10 1+T+2[n2-n1>=4]': lambda a:1+T(a)+2*(n2(a)-n1(a)>=4),
 'F11 1+T+2[n2>=5]': lambda a:1+T(a)+2*(n2(a)>=5),
 'F12 1+T+2[n2>=7]': lambda a:1+T(a)+2*(n2(a)>=7),
 'F13 1+T+3[n2>=6]': lambda a:1+T(a)+3*(n2(a)>=6),
 'F14 1+T+2[#(a_i>=2)>=6 and n2>=6]': lambda a:1+T(a)+2*(cnt(a,lambda x:x>=2)>=6 and n2(a)>=6),
}
S={
 'S01 (T)': lambda a:(T(a),),
 'S02 (M)': lambda a:(M(a),),
 'S03 (k)': lambda a:(len(a),),
 'S04 (sum a)': lambda a:(sum(a),),
 'S05 (sum a,k)': lambda a:(sum(a),len(a)),
 'S06 (T,n1)': lambda a:(T(a),n1(a)),
 'S07 (T,k)': lambda a:(T(a),len(a)),
 'S08 (T,n2 mod 6)': lambda a:(T(a),n2(a)%6),
 'S09 (M,n2 mod 3)': lambda a:(M(a),n2(a)%3),
 'S10 (T,min a)': lambda a:(T(a),min(a)),
 'S11 (T,#(a_i>=2))': lambda a:(T(a),cnt(a,lambda x:x>=2)),
 'S12 (T,#1,#2,#4,#5)': lambda a:(T(a),)+tuple(cnt(a,lambda x,c=c:x==c) for c in (1,2,4,5)),
 'S13 (T,n2)': lambda a:(T(a),n2(a)),
 'S14 (T,[n2>=6])': lambda a:(T(a),n2(a)>=6),
 'S15 (M,n2)': lambda a:(M(a),n2(a)),
 'S16 (M,n2 mod 6)': lambda a:(M(a),n2(a)%6),
 'S17 (T,counts mod 6 classes)': lambda a:(T(a),)+tuple(cnt(a,lambda x,c=c:x%6==c) for c in (1,2,4,5)),
 'S18 (T,counts mod 9 classes)': lambda a:(T(a),)+tuple(cnt(a,lambda x,c=c:x%9==c) for c in (1,2,4,5,7,8)),
 'S19 (T,floor(n2/6))': lambda a:(T(a),n2(a)//6),
}
out=open('/tmp/claude-0/qu/explore/E8/candidates.tsv','w')
out.write('id\tkind\tcandidate\tfit_box_errors(of 772140 (a,b) pairs)\n')
for name,f in F.items():
    err=0
    for a,bs in D:
        B=f(a)
        err+=sum(1 for b in range(1,61) if (b<=B)!=(bs[b-1]=='1'))
    out.write(f"{name.split()[0]}\tformula\t{name}\t{err}\n"); print(name,err)
for name,f in S.items():
    cls=collections.defaultdict(list)
    for a,bs in D: cls[f(a)].append(bs)
    err=0
    for key,lst in cls.items():
        best=min(sum(sum(1 for b in range(1,61) if (b<=B)!=(bs[b-1]=='1')) for bs in lst) for B in range(0,61))
        err+=best
    out.write(f"{name.split()[0]}\tstatistic-set(best threshold fn)\t{name}\t{err}\n"); print(name,err)
out.close()
print('total candidates',len(F)+len(S))
