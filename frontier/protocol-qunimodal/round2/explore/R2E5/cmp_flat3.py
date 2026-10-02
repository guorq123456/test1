# compare data3 (n>=2, r=9..30, a<=100, k=3..60; full Thm-A scan) with rule predictions (flat formula for n>=1)
import glob
from rule_allequal_middle import predict
tot=0;err=0;pairs=0
for f in sorted(glob.glob('data3/U_r*.txt')):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=set(x[6:])
        tot+=1; a=[n*r+s]*k; bad=False
        for b in range(F+1,T6+3):
            pairs+=1
            if predict(r,a,b)!=(b in U): bad=True
        err+=bad
print('data3 instances',tot,'(b in [F+1,T6+2]) pairs',pairs,'instances with any error',err)
