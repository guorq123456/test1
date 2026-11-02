#!/bin/bash
# S1 self-play: 20 shards x 1000 games, seeds 85830000 + 2k (the 858 block), both sides mcts:100+plan, pool C-r0
cd /home/user/test1
timeout 6600 python3 -m svsim.learn.scaledata play --pool analysis/sharednet/fields/C-r0-pool.txt --base 85830000 --stride 2 \
    --shards 0 20 --per-shard 1000 --spec "mcts:100+plan" --workers 4 --every 500 --out runs/s1/rec >> runs/s1/play.log 2>&1
tail -2 runs/s1/play.log; ls runs/s1/rec | grep -c "jsonl.gz"
