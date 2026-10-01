#!/bin/bash
cd /tmp/claude-0/conj/verify-q-integer-product-unimodality/
( ./mychk 3 12 14 | tail -1 ; ./mychk 3 6 30 | tail -1; ./mychk 3 10 17 | tail -1 ) > r3.out 2>&1 &
( ./mychk 2 10 21 | tail -1 ; ./mychk 2 12 15 | tail -1 ) > r2.out 2>&1 &
( for r in $(seq 2 40); do ./mychk $r 3 80 | grep -v "^NEC FAIL r=[23] k=[4-9]" | tail -1; done ) > k3.out 2>&1 &
( for r in 4 5 6; do ./mychk $r 7 17 | tail -1; done; for r in 7 8 9 10 11 12; do ./mychk $r 6 20 | tail -1; done ) > rmid.out 2>&1 &
wait
