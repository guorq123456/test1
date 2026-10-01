#!/usr/bin/env python3
"""Score rule.py (plain) and rule_refined.py against saved ground truth truth_r{r}.txt
(produced by save_truth.sh in gen_box.py order: r, k=1..8, sorted a, b=1..60).
Usage: python3 score_refined.py r [r ...]"""
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore/E4')
import rule, rule_refined
for r in map(int, sys.argv[1:]):
    f = open('/tmp/claude-0/qu/explore/E4/truth_r%d.txt' % r)
    st = dict(n=0, truth1=0, plain_FP=0, plain_FN=0, ref_FP=0, ref_FN=0, ref_beats_plain=0)
    for k in range(1, 9):
        for a in itertools.combinations_with_replacement(range(1, 13), k):
            a = list(a)
            div = any(x % r == 0 for x in a)
            M = sum(x // r for x in a)
            Lm = rule_refined.lmin(r, a) if not div else None
            for b in range(1, 61):
                t = f.readline().strip() == '1'
                p1 = div or b <= 1 + M
                p2 = div or r*(b-1) <= Lm
                st['n'] += 1; st['truth1'] += t
                st['plain_FP'] += p1 and not t; st['plain_FN'] += (not p1) and t
                st['ref_FP'] += p2 and not t;   st['ref_FN'] += (not p2) and t
                st['ref_beats_plain'] += p2 and not p1
                assert p2 or not p1   # refined implies plain
    assert f.readline() == ''
    print('r=%d' % r, st, flush=True)
