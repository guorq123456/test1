#!/bin/bash
# DFM rune hero gen 2 self-play: the hero piloted by mcts:58 + g1 (its time-matched N), opponents mcts:100+plan.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm NET=analysis/scaling/models/net-pilot-rune-dfm-g1.npz
nice -n 10 python3 -m svsim.learn.scaledata play --pool analysis/pilot/fields/dfm-yuri-vs-bot6.txt --hero dfm/RUNE-ユーリ     --hero-spec "mcts:58+plan+setnet=$NET+netmid+netany" --spec mcts:100+plan     --base 85998000 --stride 2 --shards 0 10 --per-shard 1000 --workers 4 --every 500 --out $R/rec-g2 >> $R/g2.log 2>&1
touch $R/g2-selfplay.done
