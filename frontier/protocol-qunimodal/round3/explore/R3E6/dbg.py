import rule_low as R
from core import U
from viol import kform
for r,a in [(31,[1,1,3,11,32,37,56]),(17,[13,14,16,25,36])]:
    u,T6,_=U(r,a)
    print(r,a,'U',u,'T6',T6,'pred',[b for b in range(1,T6+3) if R.predict(r,a,b)])
    D,tau,mu,T6,g=R._data(r,a); print(' tau',tau,'g',g[:2*r])
    for b in range(T6-1,T6+1):
        K,v=kform(r,a,b); print('   b',b,'K',K,'viol',v[:4], 'low', R.low(r,a,b))
