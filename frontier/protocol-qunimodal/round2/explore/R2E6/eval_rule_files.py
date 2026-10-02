"""Evaluate standalone rule files predict(r,a,b) on the fit set (pairs b in [1, T6+2]) and on extra
in-box sanity instances (r | a_i cases, which must be True)."""
import sys, json, importlib.util
def load(p):
    spec = importlib.util.spec_from_file_location("m", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
rows = [json.loads(l) for f in sys.argv[2:] for l in open(f)]
m = load(sys.argv[1])
err = 0; ierr = 0; pairs = 0; indom = 0
for R in rows:
    r, a, U, T6 = R['r'], R['a'], set(R['U']), R['T6']
    indom += m.domain(r, a)
    bad = 0
    for b in range(1, T6 + 3):
        pairs += 1
        bad += (m.predict(r, a, b) != (b in U))
    err += bad; ierr += bad > 0
print(sys.argv[1], "instances", len(rows), "in-domain", indom, "pairs", pairs, "pair errors", err, "instances with an error", ierr)
