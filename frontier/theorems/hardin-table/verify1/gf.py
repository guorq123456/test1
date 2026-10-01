import sympy as sp
x=sp.symbols('x')
exec(open('compare.py').read().split('tm={}')[0])
gfs={'A253431':(lambda n:T(n,4), x*(109 - 225*x + 32*x**2)),
'A253438':(lambda n:T(4,n), x*(109 - 219*x + 15*x**2 + 9*x**3 + 2*x**4)),
'A253433':(lambda n:T(n,6), x*(325 - 657*x + 32*x**2)),
'A253440':(lambda n:T(6,n), x*(325 - 651*x + 15*x**2 + 9*x**3 + 2*x**4)),
'A253434':(lambda n:T(n,7), x*(613 - 1233*x + 32*x**2)),
'A253441':(lambda n:T(7,n), x*(613 - 1227*x + 15*x**2 + 9*x**3 + 2*x**4)),
'A253152':(lambda n:T(n,1), x*(16 - 9*x - 16*x**2 - 20*x**3 - 8*x**4)),
'A253429':(lambda n:T(n,2), x*(39 - 59*x - 23*x**2 + 5*x**3 + 2*x**4)),
'A253430':(lambda n:T(n,3), x*(69 - 137*x + 13*x**2 + 6*x**3)),
'A253436':(lambda n:T(2,n), x*(39 - 59*x - 26*x**2 + 8*x**3 + 8*x**4)),
'A253437':(lambda n:T(3,n), x*(69 - 134*x + 4*x**2 + 11*x**3 + 2*x**4)),
}
N=40
for a,(fn,num) in gfs.items():
    s=sp.series(num/((1-x)*(1-2*x)),x,0,N+1).removeO()
    co=[s.coeff(x,i) for i in range(1,N+1)]
    print(a, all(co[i-1]==fn(i) for i in range(1,N+1)))
