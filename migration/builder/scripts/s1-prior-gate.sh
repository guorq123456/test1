#!/bin/bash
# S1 (i) gate: the shared move prior over the hand-written score at the matched N, 300 pairs, bank 85820000; BLAS one thread
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
timeout 6600 python3 -m svsim.tools.deckgate --x "mcts:64+plan+puct=analysis/scaling/models/prior-s1-20k.npz" --y "mcts:100+plan" \
    --field analysis/sharednet/fields/B-r1.txt --seed 85820000 --pairs 300 --workers 4 \
    --out analysis/sharednet/s1/gate/prior-64.jsonl >> runs/s1/prior-gate.log 2>&1
echo "EXIT $?" >> runs/s1/prior-gate.log
tail -14 runs/s1/prior-gate.log
