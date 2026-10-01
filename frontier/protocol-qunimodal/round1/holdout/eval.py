"""Score a rule file against a hidden holdout of b-profiles.
Rule file must define predict(r, a, b) -> bool (a = sorted list of ints).
Optional: domain(r, a) -> bool restricting where the rule makes claims.
Usage: python3 eval.py rule.py holdout.jsonl"""
import json, sys, importlib.util, collections, traceback
spec = importlib.util.spec_from_file_location('rule', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
dom = getattr(m, 'domain', lambda r, a: True)
tot = collections.Counter(); bad = collections.Counter(); tup = collections.Counter(); tupbad = collections.Counter(); ex = []
for line in open(sys.argv[2]):
    o = json.loads(line); r, a, p, s = o['r'], o['a'], o['profile'], o['stratum']
    try:
        if not dom(r, list(a)): continue
    except Exception: continue
    tup[s] += 1; wrong = 0
    for b, truth in enumerate(p, 1):
        try: pr = bool(m.predict(r, list(a), b))
        except Exception as e: pr = None
        tot[s] += 1
        if pr != truth:
            bad[s] += 1; wrong += 1
            if len(ex) < 8: ex.append({'r': r, 'a': a, 'b': b, 'truth': truth, 'pred': pr, 'stratum': s})
    if wrong: tupbad[s] += 1
T = sum(tot.values()); B = sum(bad.values())
print(json.dumps({'instances_in_domain': T, 'instance_errors': B, 'tuples_in_domain': sum(tup.values()),
  'tuples_with_any_error': sum(tupbad.values()),
  'per_stratum': {s: {'inst': tot[s], 'err': bad[s], 'tuples': tup[s], 'tuples_err': tupbad[s]} for s in tot},
  'first_mismatches': ex}, indent=1))
