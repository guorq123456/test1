# Count (r,a) in the full fit box whose set of unimodal b (1..60) is not an initial segment {1..m}; print examples.
import collections
cnt=collections.Counter(); ex=[]
for L in open('/tmp/claude-0/qu/explore/E2/gt.txt'):
    x=L.split(); r,k=int(x[0]),int(x[1]); a=list(map(int,x[2:2+k])); m=int(x[2+k],16)
    if m & (m+1):  # not of form 2^j-1
        cnt[r]+=1
        if len(ex)<5: ex.append((r,a,[b for b in range(1,61) if (m>>(b-1))&1][:8]))
print("non-initial-segment (r,a) counts by r:",dict(cnt),"total",sum(cnt.values()))
print(ex)
