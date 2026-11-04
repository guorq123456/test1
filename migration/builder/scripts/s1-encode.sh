#!/bin/bash
# S1: encode the finished record shards (turn ends: scaledata encode; mid-turn: midrows encode), one worker
cd /home/user/test1
mkdir -p runs/s1/enc
for f in runs/s1/rec/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" runs/s1/enc/; done
timeout 6600 python3 -m svsim.learn.scaledata encode --records runs/s1/enc --out runs/s1/tok --workers ${1:-4} >> runs/s1/encode.log 2>&1
timeout 6600 python3 -m svsim.learn.midrows encode --records runs/s1/enc --out runs/s1/mid --workers ${1:-4} >> runs/s1/encode.log 2>&1
ls runs/s1/tok | grep -c tok-; ls runs/s1/mid | grep -c mid-
