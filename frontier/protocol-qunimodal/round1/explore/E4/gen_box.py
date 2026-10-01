#!/usr/bin/env python3
"""Enumerate every fit-box instance (r in 2..6, 1<=k<=8, sorted a with 1<=a_i<=12, 1<=b<=60)
and print lines 'r k a1..ak b' for the ground-truth checker /tmp/claude-0/qu/tools/uni.
Usage: python3 gen_box.py [r]   (restrict to one r)"""
import sys, itertools
rs = [int(sys.argv[1])] if len(sys.argv) > 1 else range(2, 7)
out = sys.stdout
for r in rs:
    for k in range(1, 9):
        for a in itertools.combinations_with_replacement(range(1, 13), k):
            pre = '%d %d %s ' % (r, k, ' '.join(map(str, a)))
            out.write(''.join(pre + '%d\n' % b for b in range(1, 61)))
