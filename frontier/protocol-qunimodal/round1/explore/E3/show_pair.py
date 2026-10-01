# Show coefficients of the smallest trivial-factor-free collision pair (r=6,b=4) and where unimodality fails.
import sys; sys.path.insert(0,'/tmp/claude-0/qu/tools')
from uni_ref import poly, unimodal
for a in [(2,3,4,4,4,4,4,8),(2,2,3,4,4,4,4,10),(2,2,4,4,4,4,4,9)]:
    c=poly(6,list(a),4)
    dips=[(i,c[i-1],c[i],c[i+1]) for i in range(1,len(c)-1) if c[i]<c[i-1] and c[i]<c[i+1]]
    print(a,'unimodal' if unimodal(c) else 'NOT unimodal','deg',len(c)-1,'center',(len(c)-1)/2,'interior local minima',dips)
    m=len(c)//2; print('   middle coeffs',c[m-8:m+9])
