import numpy as np
from repro import run
A = run(451, 64); B = run(193, 64)
c = 64
def nb(X):
    return np.roll(X,1,0)+np.roll(X,-1,0)+np.roll(X,1,1)+np.roll(X,-1,1)
for t in range(1, 27):
    for name, X in (('451',A[t]),('193',B[t])):
        s = nb(X)
        iso = np.argwhere((X==1)&(s==0)) - c   # (c=1,s=0)
        hole = np.argwhere((X==0)&(s==4)) - c  # (c=0,s=4)
        if len(iso) or len(hole):
            print('step',t,'rule',name,'(c=1,s=0) at', [ (int(x[1]),int(x[0])) for x in iso][:12], '(c=0,s=4) at', [(int(x[1]),int(x[0])) for x in hole][:12])
def show(X, R):
    rows=[]
    for y in range(R, -R-1, -1):
        rows.append(''.join('#' if X[c-y, c+x] else '.' for x in range(-R, R+1)))
    return '\n'.join(rows)
print('step 16 (common), |x|,|y|<=17:'); print(show(B[16], 17))
for t in (17,):
    print('step',t,'rule 193:'); print(show(B[t], 18)); print('rule 451:'); print(show(A[t],18))
