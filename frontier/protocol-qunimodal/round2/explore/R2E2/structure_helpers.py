def mu_of(tt, r):
    for m in range(r):
        if all(tt[s] <= 0 for s in range(m + 1, r)): return m
    return r - 1
