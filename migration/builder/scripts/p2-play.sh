#!/bin/bash
# Pilot line, EXTERNAL hero dfm/RUNE-ユーリ (measurement only, Salem 「隔离训练」): the bot hero's settings exactly;
# waits for the bot hero's self-play to end (the CPU), then 10 shards base 85995000 stride 2 + holdout 2 shards 85996000
cd /home/user/test1
while pgrep -f "hero bot/T3-RUNE-1" > /dev/null; do sleep 60; done
F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt
timeout 6600 python3 -m svsim.learn.scaledata play --pool $F --hero "dfm/RUNE-ユーリ" --base 85995000 --stride 2 \
    --shards 0 10 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-4} --every 500 --out runs/pilot-dfm/rec >> runs/pilot-dfm/play.log 2>&1 &&
timeout 6600 python3 -m svsim.learn.scaledata play --pool $F --hero "dfm/RUNE-ユーリ" --base 85996000 --stride 2 \
    --shards 0 2 --per-shard 1000 --spec "mcts:100+plan" --workers ${1:-4} --every 500 --out runs/pilot-dfm/holdout >> runs/pilot-dfm/play.log 2>&1
echo "EXIT $?" >> runs/pilot-dfm/play.log
tail -2 runs/pilot-dfm/play.log | cut -c1-300
