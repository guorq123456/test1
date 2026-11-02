#!/bin/bash
# Pilot g1: a fresh flagged value net (turn ends + mid-turn rows) on the hero's 10 training shards
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
timeout 6600 python3 analysis/scaling/train_mid.py --shared --fresh --tokens runs/pilot/tok --end 85990000:10 \
    --mid-dir runs/pilot/mid --mid 85990000:10 --holdout 85991000 85991002 --name pilot-rune-bot-g1 \
    --checkpoint runs/pilot/ckpt-g1.npz >> runs/pilot/train-g1.log 2>&1
echo "EXIT $?" >> runs/pilot/train-g1.log
tail -3 runs/pilot/train-g1.log | cut -c1-400
