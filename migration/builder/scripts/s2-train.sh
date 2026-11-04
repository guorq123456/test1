#!/bin/bash
# S1 (ii): the shared net continued from net-s1-20k on S1's 20 shards with advantage labels + the ranking loss
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
NAME=${1:-s1-ii}
timeout 6600 python3 analysis/scaling/train_mid.py --shared --init analysis/scaling/models/net-s1-20k.npz \
    --tokens runs/s1/tok --end 85830000:20 --mid-dir runs/s1/mid --mid 85830000:20 \
    --split games:analysis/sharednet/s1/holdout-games.json --advantage runs/s1/rec \
    --rank-dir runs/s1/rank --rank-weight 1.0 --rank-batch 64 --extend-cards \
    --name $NAME --checkpoint runs/s1/ckpt-$NAME.npz >> runs/s1/train-$NAME.log 2>&1
echo "EXIT $?" >> runs/s1/train-$NAME.log
tail -5 runs/s1/train-$NAME.log | cut -c1-600
