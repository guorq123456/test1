#!/bin/bash
# S1 (i): the shared move prior, resumed from its checkpoint; exit code and memory (RSS every 60 s) recorded
cd /home/user/test1
SH=$(for k in $(seq 0 19); do echo -n "$((85830000 + 2*k)) "; done)
timeout 6600 python3 -m svsim.learn.setpolicy fit --data runs/s1/dec --cards runs/s1/cards-all.npz --shards $SH \
    --init analysis/scaling/models/net-s1-20k.npz --split games:analysis/sharednet/s1/holdout-games.json --ftz --epochs 6 \
    --checkpoint runs/s1/ckpt-prior.npz --out analysis/scaling/models/prior-s1-20k.npz >> runs/s1/prior-fit.log 2>> runs/s1/prior-fit.err &
PID=$!
while kill -0 $PID 2>/dev/null; do
    echo "$(date -u +%H:%M:%S) $(ps -o rss= --ppid $PID | awk '{s+=$1} END {print s/1024}') MB" >> runs/s1/prior-mem.log
    sleep 60
done
wait $PID; echo "EXIT $?" >> runs/s1/prior-fit.err
tail -2 runs/s1/prior-fit.err; tail -3 runs/s1/prior-fit.log | cut -c1-200; sort -k2 -n runs/s1/prior-mem.log | tail -1
