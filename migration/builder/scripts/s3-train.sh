#!/bin/bash
# S1 B: the (ii) recipe on all K shards (S1 + S1(b) + RC), from net-s1-20k; resumable chunks (checkpoint)
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
K=${1:-60}
NAME=${2:-s1-b60}
timeout 6600 python3 analysis/scaling/train_mid.py --shared --init analysis/scaling/models/net-s1-20k.npz \
    --tokens runs/s1/tok --end 85830000:$K --mid-dir runs/s1/mid --mid 85830000:$K \
    --split games:analysis/sharednet/s1/holdout-games.json --advantage runs/s1/rec \
    --rank-dir runs/s1/rank --rank-weight 1.0 --rank-batch 64 --extend-cards \
    --name $NAME --checkpoint runs/s1/ckpt-$NAME.npz >> runs/s1/train-$NAME.log 2>&1 &
PID=$!
while kill -0 $PID 2>/dev/null; do
    echo "$(date -u +%H:%M:%S) $(ps -o rss= --ppid $PID | awk '{s+=$1} END {print s/1024}') MB" >> runs/s1/train-$NAME-mem.log
    sleep 60
done
wait $PID; echo "EXIT $?" >> runs/s1/train-$NAME.log
tail -4 runs/s1/train-$NAME.log | cut -c1-500; sort -k2 -n runs/s1/train-$NAME-mem.log | tail -1
