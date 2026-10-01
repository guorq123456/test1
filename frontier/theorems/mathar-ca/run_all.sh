#!/bin/sh
# Reproduces every computational claim in proof.md (total run time ~ 20 s on one core).
set -e
cd /tmp/claude-0/deep/mathar-ca
for a in 282297 279721 282295 279720; do [ -s b$a.txt ] || curl -sS -o b$a.txt https://oeis.org/A$a/b$a.txt; done
echo "== (1) numpy replica of Price's Mathematica program (torus g=257) vs b-files =="
python3 repro.py
echo "== (2) independent C plane simulator, n <= 1000 =="
gcc -O2 -o plane plane.c
./plane 451 1000 > r451.txt
./plane 193 1000 > r193.txt
python3 compare.py
echo "== (3) naive set-based plane simulator (rules as Boolean formulas), n <= 40 =="
python3 transparent.py > transparent_out.txt; cat transparent_out.txt
echo "== (4) local certificate stage 23 -> 26 around (3,0) =="
python3 diamond.py
