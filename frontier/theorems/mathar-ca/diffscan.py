import numpy as np
from repro import run
A = run(451, 128); B = run(193, 128)
c = 128
for n in range(0, 40):
    d = np.argwhere(A[n]!=B[n]) - c
    if len(d):
        dist = np.abs(d).sum(1)
        print(n, len(d), 'min |x|+|y|', dist.min(), 'min |y|', np.abs(d[:,0]).min(), 'sample', [tuple(x) for x in d[:6]])
    else:
        print(n, 0)
