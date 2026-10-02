# cross-check my U computation against the exact big-integer ground truth gt_big.profile
import sys; sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from reslev import *
r=57; rp=[6, 7, 9, 15, 18, 20, 22, 23, 25, 26, 27, 28, 30, 33, 37]; m=37
a=sorted([1+r]*m+rp)
bs=list(range(38,46))
print('gt_big',list(zip(bs,profile(r,a,bs))))
R=Res(r,a); print('mine ',[(b,R.unimodal(b)) for b in bs])
print('log2 max coeff',max(R.A).bit_length())
