#!/bin/bash
# The 60k prior's gate (the architecture thread 2026-10-30 00:53Z): wait for the fit, then the time match (24 pairs,
# seeds 85891500 on) and 300 pairs at the matched N on bank 85820000; BLAS on one thread, an idle machine
cd /home/user/test1
while pgrep -f "setpolicy fit" > /dev/null; do sleep 30; done
[ -f analysis/scaling/models/prior-s1-60k.npz ] || { echo "no prior file"; exit 1; }
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
P=analysis/scaling/models/prior-s1-60k.npz
G=analysis/sharednet/s1/gate
timeout 3000 python3 -m svsim.tools.deckgate --x "mcts:100+plan+puct=$P" --y "mcts:100+plan" \
    --field analysis/sharednet/fields/B-r1.txt --seed 85891500 --time 24 --workers 4 --out $G/prior60-time-100.jsonl > $G/prior60-time-100.log 2>&1
N=$(grep -o "→ N 100 → [0-9]*" $G/prior60-time-100.log | grep -o "[0-9]*$")
echo "matched N $N"
[ -n "$N" ] || exit 1
timeout 6000 python3 -m svsim.tools.deckgate --x "mcts:$N+plan+puct=$P" --y "mcts:100+plan" \
    --field analysis/sharednet/fields/B-r1.txt --seed 85820000 --pairs 300 --workers 4 --out $G/prior60-$N.jsonl > $G/prior60-$N.log 2>&1
echo "EXIT $?"
grep -v "^  X 用" $G/prior60-time-100.log | tail -3; tail -11 $G/prior60-$N.log
