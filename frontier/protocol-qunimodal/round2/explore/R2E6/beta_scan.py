"""Scan the single fitted constant beta for the standalone rule files (fit set)."""
import sys, json, importlib.util
def load(p):
    spec = importlib.util.spec_from_file_location("m", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m = load(sys.argv[1])
rows = [json.loads(l) for f in sys.argv[2:] for l in open(f)]
cache = []
for R in rows:
    cache.append(R)
for i in range(-12, 3):
    beta = i / 10
    m.BETA = beta
    err = 0
    for R in cache:
        r, a, U, T6, F = R['r'], R['a'], set(R['U']), R['T6'], R['F']
        e = m.E_pred(r, sorted(a), beta)
        err += sum(1 for b in range(1, T6 + 3) if ((b <= 1 + F) or (b <= 1 + F + e)) != (b in U))
    print("beta=%.1f pair errors %d" % (beta, err), flush=True)
