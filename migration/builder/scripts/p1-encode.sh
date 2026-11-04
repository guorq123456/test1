#!/bin/bash
# Pilot g1 (bot/T3-RUNE-1): turn-end tokens (scaledata encode, v1) and mid-turn rows (midrows encode) of the 10
# training + 2 holdout shards into one folder each (one cards.npz)
cd /home/user/test1
mkdir -p runs/pilot/enc
for f in runs/pilot/rec/rec-*.jsonl.gz runs/pilot/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" runs/pilot/enc/; done
python3 -m svsim.learn.scaledata encode --records runs/pilot/enc --out runs/pilot/tok --workers 4 >> runs/pilot/encode.log 2>&1 &&
python3 -m svsim.learn.midrows encode --records runs/pilot/enc --out runs/pilot/mid --workers 4 >> runs/pilot/encode.log 2>&1
echo "EXIT $?" >> runs/pilot/encode.log
ls runs/pilot/tok | grep -c tok-; ls runs/pilot/mid | grep -c mid-
