#!/bin/bash
# Reproduce every number reported by explorer E6 (sufficiency counterexample search), fit box only.
set -e
cd /tmp/claude-0/qu/explore/E6
gcc -O2 -o exh exh.c && gcc -O2 -o margins margins.c
for r in 2 3 4 5 6; do ./exh $r > out_r$r.txt & done; wait          # exhaustive region + margins + Cor4.3 sanity + slack
for r in 2 3 4 5 6; do ./margins $r > marg_r$r.txt & done; wait     # strict ratio / tie size / tie depth / hard subset
./check_uni.sh                                                        # ground-truth checker on all region instances
for r in 2 3 4 5 6; do python3 verify_ff.py $r; done                 # slack data vs ground truth
python3 families.py > families_out.txt                                # structured families, independent Python code
grep -h "region_instances" out_r*.txt
