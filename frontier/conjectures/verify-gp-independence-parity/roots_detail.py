import mpmath as mp, sympy as sp
mp.mp.dps = 60
polys = {}
for fn in ['polys_k2.txt','polys_k4.txt']:
    for line in open(fn):
        k,n,cs = line.split(); polys[(int(k),int(n))] = list(map(int, cs.split(',')))
x = sp.symbols('x')
for key in [(2,25),(4,20)]:
    c = polys[key]
    print(key, c)
    P = sp.Poly(list(reversed(c)), x)
    print('  degree', P.degree(), 'sympy count_roots (real):', P.count_roots(), 'sqfree:', sp.gcd(P, P.diff(x)).degree()==0)
    r = mp.polyroots(list(reversed(c)), maxsteps=500, extraprec=500)
    nr = [z for z in r if abs(mp.im(z)) > mp.mpf(10)**-30]
    print('  nonreal:', [mp.nstr(z, 8) for z in nr])
    # certify via residual
    print('  min |Im| over nonreal:', mp.nstr(min(abs(mp.im(z)) for z in nr), 6))
