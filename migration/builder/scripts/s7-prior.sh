#!/bin/bash
# The (i) recipe on 60 shards (the architecture thread 2026-10-30 00:52Z): the shared move prior continued from
# prior-s1-20k on all 60 shards' decisions, 3 epochs at most, resumable chunks; memory every 60 s
cd /home/user/test1
SH=$(for k in $(seq 0 59); do echo -n "$((85830000 + 2*k)) "; done)
timeout 6600 python3 -m svsim.learn.setpolicy fit --data runs/s1/dec --cards runs/s1/cards-all60.npz --shards $SH \
    --prior analysis/scaling/models/prior-s1-20k.npz --extend-cards --split games:analysis/sharednet/s1/holdout-games.json \
    --ftz --epochs 3 --checkpoint runs/s1/ckpt-prior60.npz --out analysis/scaling/models/prior-s1-60k.npz \
    >> runs/s1/prior60-fit.log 2>> runs/s1/prior60-fit.err &
PID=$!
while kill -0 $PID 2>/dev/null; do
    echo "$(date -u +%H:%M:%S) $(ps -o rss= --ppid $PID | awk '{s+=$1} END {print s/1024}') MB" >> runs/s1/prior60-mem.log
    sleep 60
done
wait $PID; echo "EXIT $?" >> runs/s1/prior60-fit.err
tail -2 runs/s1/prior60-fit.err; tail -3 runs/s1/prior60-fit.log | cut -c1-300; sort -k2 -n runs/s1/prior60-mem.log | tail -1
