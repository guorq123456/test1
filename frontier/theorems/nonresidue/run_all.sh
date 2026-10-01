#!/bin/sh
# Reproduce all computations referenced in proof.md
cd /tmp/claude-0/deep/nonresidue
python3 verify_oeis.py
python3 small_cases.py
gp -q -s 200000000 check.gp < /dev/null
gcc -O3 -march=native -fopenmp -o ext ext.c && ./ext 100000000 2 && ./ext 10000000000 3
