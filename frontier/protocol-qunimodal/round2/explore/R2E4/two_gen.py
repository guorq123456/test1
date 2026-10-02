# Two-value family generator: a = (x^m, y^n), r in [rlo,rhi], 1<=x<y<=100, r∤x,y, m,n>=1, m+n<=K, #middle>=3
import sys
rlo,rhi,K=map(int,sys.argv[1:4])
for r in range(rlo,rhi+1):
    vals=[v for v in range(1,101) if v%r]
    for i,x in enumerate(vals):
        for y in vals[i+1:]:
            mx=2<=x%r<=r-2; my=2<=y%r<=r-2
            if not(mx or my): continue
            for s in range(2,K+1):
                for m in range(1,s):
                    n=s-m
                    if m*mx+n*my<3: continue
                    print(r,s,*([x]*m+[y]*n))
