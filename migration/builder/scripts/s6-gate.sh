#!/bin/bash
# S1 B gate: wait for the machine to be idle (no self-play), then the time match (24 pairs, seeds 85891400 on) and the
# fixed 300 pairs at the matched N on bank 85820000; BLAS on one thread
cd /home/user/test1
while pgrep -f "scaledata play" > /dev/null; do sleep 30; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
NET=analysis/scaling/models/net-s1-b60.npz
G=analysis/sharednet/s1/gate
timeout 3000 python3 -m svsim.tools.deckgate --x "mcts:100+plan+setnet=$NET+netmid+netany" --y "mcts:100+plan" \
    --field analysis/sharednet/fields/B-r1.txt --seed 85891400 --time 24 --workers 4 --out $G/b60-time-100.jsonl > $G/b60-time-100.log 2>&1
N=$(grep -o "→ N 100 → [0-9]*" $G/b60-time-100.log | grep -o "[0-9]*$")
echo "matched N $N"
[ -n "$N" ] || exit 1
timeout 6000 python3 -m svsim.tools.deckgate --x "mcts:$N+plan+setnet=$NET+netmid+netany" --y "mcts:100+plan" \
    --field analysis/sharednet/fields/B-r1.txt --seed 85820000 --pairs 300 --workers 4 --out $G/b60-$N.jsonl > $G/b60-$N.log 2>&1
echo "EXIT $?"
grep -v "^  X 用" $G/b60-time-100.log | tail -3; tail -11 $G/b60-$N.log
