# Score a rule on round-2 holdout format {'r','a','bs','unimodal'}; reports FP/FN.
import json, sys, importlib.util, collections
spec = importlib.util.spec_from_file_location('rule', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
dom = getattr(m, 'domain', lambda r, a: True)
c = collections.Counter(); ps = collections.defaultdict(collections.Counter); ex = []
for line in open(sys.argv[2]):
    o = json.loads(line); r, a, s = o['r'], o['a'], o['stratum']
    try:
        if not dom(r, list(a)): continue
    except Exception: continue
    c['tuples'] += 1; bad = 0
    for b, t in zip(o['bs'], o['unimodal']):
        try: p = bool(m.predict(r, list(a), b))
        except Exception: p = None
        c['inst'] += 1; ps[s]['inst'] += 1
        if p != t:
            bad += 1; c['err'] += 1; ps[s]['err'] += 1; c['FP' if p is True else 'FN'] += 1
            if len(ex) < 5: ex.append({'r': r, 'a': a, 'b': b, 'truth': t, 'pred': p, 'stratum': s})
    c['tuples_err'] += bad > 0
print(json.dumps({**c, 'per_stratum': {k: dict(v) for k, v in ps.items()}, 'first': ex}))
