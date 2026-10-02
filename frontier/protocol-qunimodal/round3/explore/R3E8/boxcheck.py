# fit-box admissibility of a residue-level instance (r<=120,k<=140 region; residue vector s)
def allowed(r,s):
    k=len(s)
    if r>=1000: return True
    if r>120 or k>140: return False
    mid=[x for x in s if 2<=x<=r-2]
    if k>=20 and len(mid) in (4,5) and all(x in (1,r-1) for x in s if not (2<=x<=r-2)): return False
    if k>=55 and sum(1 for x in s if x==r-1)>50: return False
    if k>=60 and len(mid)==k and len(set(s))<=2: return False
    return True
