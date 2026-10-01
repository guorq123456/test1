from itertools import combinations_with_replacement as cwr
a=[int(l.split()[1]) for l in open('a_dp.txt')]
def cnt(L,K):
    return sum(1 for w in cwr(range(K),L) if all(w[i+1]-w[i]!=1 for i in range(L-1)))
print("len n  :",[cnt(n,n+2) for n in range(0,11)])
print("len n+1:",[cnt(n+1,n+2) for n in range(0,11)])
print("a      :",a[:11])
# example list for n=3
print(sorted(w for w in cwr(range(5),3) if all(w[i+1]-w[i]!=1 for i in range(2)))[:5], cnt(3,5))
