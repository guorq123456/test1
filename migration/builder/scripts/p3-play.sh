#!/bin/bash
# Pilot gen 2 (bot/T3-RUNE-1): the hero piloted by mcts:64 + the g1 net, opponents mcts:100+plan; base 85993000
# stride 2, 10 shards x 1000; resumable chunks
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
timeout 6600 python3 -m svsim.learn.scaledata play --pool analysis/pilot/fields/bot-frozen7.txt --hero bot/T3-RUNE-1 \
    --hero-spec "mcts:64+plan+setnet=analysis/scaling/models/net-pilot-rune-bot-g1.npz+netmid+netany" --spec "mcts:100+plan" \
    --base 85993000 --stride 2 --shards 0 10 --per-shard 1000 --workers ${1:-4} --every 500 --out runs/pilot/rec-g2 >> runs/pilot/play-g2.log 2>&1
echo "EXIT $?" >> runs/pilot/play-g2.log
tail -2 runs/pilot/play-g2.log | cut -c1-300
