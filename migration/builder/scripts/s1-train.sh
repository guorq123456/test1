#!/bin/bash
# S1: the shared net from scratch on the first $1 shards (turn-end + mid-turn rows), validation = held-out decks' games
cd /home/user/test1
K=${1:-10}
NAME=${2:-s1-10k}
timeout 6600 python3 analysis/scaling/train_mid.py --shared --fresh --tokens runs/s1/tok --end 85830000:$K \
    --mid-dir runs/s1/mid --mid 85830000:$K --split games:analysis/sharednet/s1/holdout-games.json \
    --name $NAME --checkpoint runs/s1/ckpt-$NAME.npz >> runs/s1/train-$NAME.log 2>&1
tail -5 runs/s1/train-$NAME.log | cut -c1-400
