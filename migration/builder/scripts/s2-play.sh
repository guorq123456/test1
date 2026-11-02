#!/bin/bash
# S1 (b) self-play in this container: shards k = 20..35 (seeds 85830040 + ...), pool P2, both sides mcts:100+plan
cd /home/user/test1
timeout 6600 python3 -m svsim.learn.scaledata play --pool analysis/sharednet/fields/P2-pool.txt --base 85830000 --stride 2 \
    --shards 20 36 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-3} --every 500 --out runs/s1/rec >> runs/s1/play2.log 2>&1
ls runs/s1/rec | grep -c "jsonl.gz"
