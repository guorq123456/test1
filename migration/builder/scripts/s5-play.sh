#!/bin/bash
# P3 self-play, this container's share k=160..179 (the architecture thread 19:45Z / 19:47Z), resumable chunks
cd /home/user/test1
timeout 6600 python3 -m svsim.learn.scaledata play --pool analysis/sharednet/fields/P3-pool.txt --base 85830000 --stride 2 \
    --shards 160 180 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-3} --every 500 --out runs/s1/rec >> runs/s1/play3.log 2>&1
echo "EXIT $?" >> runs/s1/play3.log
tail -2 runs/s1/play3.log | cut -c1-300
