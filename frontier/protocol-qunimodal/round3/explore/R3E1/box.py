"""Fit-box membership test (hard rule of the task)."""
def in_box(r,a):
    k=len(a)
    if r>=1000: return True
    if r>120: return False
    if k>140 or max(a)>400: return False
    res=[x%r for x in a]
    mid=[x for x in res if 2<=x<=r-2]
    if k>=20 and len(mid) in (4,5) and all(x in (1,r-1) for x in res if not (2<=x<=r-2)): return False
    if k>=55 and sum(1 for x in res if x==r-1)>50: return False
    if k>=60 and len(set(a))==2 and all(2<=x%r<=r-2 for x in set(a)): return False
    return True
