#!/bin/bash
# Pilot line g1: hero bot/T3-RUNE-1 against the other 6 bot decks, mcts:100+plan both sides; training shards
# base 85990000 stride 2 (k < 10), then the holdout base 85991000 stride 2 (k < 2); resumable chunks
cd /home/user/test1
F=analysis/pilot/fields/bot-frozen7.txt
timeout 6600 python3 -m svsim.learn.scaledata play --pool $F --hero bot/T3-RUNE-1 --base 85990000 --stride 2 \
    --shards 0 10 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-4} --every 500 --out runs/pilot/rec >> runs/pilot/play.log 2>&1 &&
timeout 6600 python3 -m svsim.learn.scaledata play --pool $F --hero bot/T3-RUNE-1 --base 85991000 --stride 2 \
    --shards 0 2 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-4} --every 500 --out runs/pilot/holdout >> runs/pilot/play.log 2>&1
echo "EXIT $?" >> runs/pilot/play.log
tail -2 runs/pilot/play.log | cut -c1-300
