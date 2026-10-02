# Check: for 2<=s<=r-2 and 2<=j<=r-2:  |sin(pi j s/r)/sin(pi j/r)| < sin(pi s/r)/sin(pi/r)  (pure trigonometry, r<=120 and r in {1000,1001,1200})
import math
worst=0; cnt=0
for r in list(range(4,121))+[1000,1001,1200]:
    for s in range(2,r-1):
        base=math.sin(math.pi*s/r)/math.sin(math.pi/r)
        for j in range(2,r-1):
            v=abs(math.sin(math.pi*j*s/r)/math.sin(math.pi*j/r))
            cnt+=1
            if v/base>worst: worst=v/base; arg=(r,s,j)
print('pairs',cnt,'max ratio',worst,arg)
