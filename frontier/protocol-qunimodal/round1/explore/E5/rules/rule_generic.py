# RULE G (closed form, residues only, for r in {2,3}):
# B* = 1 + Q + max(0, 2*floor((sigma+3-r)/(2r))), Q=sum floor(a_i/r), sigma=sum((a_i mod r)-1)
# r=2: B* = 1+Q ; r=3: B* = 1 + Q + 2*floor(n2/6), n2 = #{i: a_i = 2 mod 3}.
def domain(r, a):
    return r in (2, 3)
def predict(r, a, b):
    if any(x % r == 0 for x in a):
        return True
    Q = sum(x//r for x in a); sig = sum(x % r - 1 for x in a)
    return b <= 1 + Q + max(0, 2*((sig + 3 - r)//(2*r)))
