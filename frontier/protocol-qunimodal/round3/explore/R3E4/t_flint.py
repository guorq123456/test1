import time, flint, random
r=10000; k=100
random.seed(1)
a=[random.randint(3000,4000) for _ in range(k)]
t=time.time()
ps=[flint.fmpz_poly([1]*ai) for ai in a]
while len(ps)>1:
    ps=[ps[i]*ps[i+1] if i+1<len(ps) else ps[i] for i in range(0,len(ps),2)]
A=ps[0]
print('deg',A.degree(),time.time()-t)
d=A*flint.fmpz_poly([1,-1])
t=time.time(); c=d.coeffs(); print(len(c),time.time()-t)
t=time.time(); ci=[int(x) for x in c]; print(time.time()-t, ci[len(ci)//3].bit_length())
