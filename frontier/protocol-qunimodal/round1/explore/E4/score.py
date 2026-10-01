#!/usr/bin/env python3
"""Join gen_box.py output (instances) with checker output (truth) and score the rule in rule.py.
Usage: paste -d'|' inst.txt truth.txt | python3 score.py
Reports, per r: #instances, #(predict True), #(predict True & truth 0) [= counterexamples to the
theorem], #(predict False & truth 1) [= cases the one-sided sufficient condition does not cover]."""
import sys, collections
sys.path.insert(0, '/tmp/claude-0/qu/explore/E4')
from rule import predict, sufficient
S = collections.defaultdict(lambda: collections.Counter())
for line in sys.stdin:
    inst, t = line.rstrip('\n').split('|')
    x = list(map(int, inst.split())); r, k = x[0], x[1]; a = x[2:2+k]; b = x[2+k]
    t = int(t)
    suf = sufficient(r, a, b)
    p = predict(r, a, b)
    c = S[r]
    c['n'] += 1
    c['truth1'] += t
    c['suff'] += suf
    c['suff_and_truth0'] += (suf and t == 0)
    c['pred_err'] += (p != bool(t))
    c['pred_FP'] += (p and t == 0)
    c['pred_FN'] += ((not p) and t == 1)
    # the pure target condition (without the r|a_i clause)
    tc = b <= 1 + sum(ai // r for ai in a)
    c['target_cond'] += tc
    c['target_cond_and_truth0'] += (tc and t == 0)
tot = collections.Counter()
for r in sorted(S):
    print('r=%d' % r, dict(S[r])); tot.update(S[r])
print('TOTAL', dict(tot))
