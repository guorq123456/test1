#!/bin/bash
# DFM rune hero gen 4: hero mcts:63 + g3 (g3's time-matched N), self-play 86027000; train fresh on gens 1-4; time 86028900; gate 86028000.
# Stage A: shards 0-5; stage B: shards 5-10; stage C: encode, train, time, gate (each under the 2 h background limit).
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ
play() { nice -n 10 python3 -m svsim.learn.scaledata play --pool $F --hero $H     --hero-spec "mcts:63+plan+setnet=analysis/scaling/models/net-pilot-rune-dfm-g3.npz+netmid+netany" --spec mcts:100+plan     --base 86027000 --stride 2 --shards $1 $2 --per-shard 1000 --workers 4 --every 500 --out $R/rec-g4 >> $R/g4.log 2>&1; }
case "$1" in
A) play 0 5 ;;
B) play 5 10; touch $R/g4-selfplay.done ;;
C)
test -f $R/g4-selfplay.done
mkdir -p $R/enc4
for f in $R/rec/rec-*.jsonl.gz $R/rec-g2/rec-*.jsonl.gz $R/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz $R/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc4/; done
test -f $R/tok4.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc4 --out $R/tok4 --workers 4 >> $R/g4.log 2>&1; touch $R/tok4.done; }
test -f $R/mid4.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc4 --out $R/mid4 --workers 4 >> $R/g4.log 2>&1; touch $R/mid4.done; }
test -f $R/train4.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok4 --end 85995000:10 --end 85998000:10 --end 86025000:10 --end 86027000:10     --mid-dir $R/mid4 --mid 85995000:10 --mid 85998000:10 --mid 86025000:10 --mid 86027000:10 --holdout 85996000 85996002 --name pilot-rune-dfm-g4     --checkpoint $R/ckpt-g4.npz >> $R/g4-train.log 2>&1; touch $R/train4.done; }
;;
D)
NET=analysis/scaling/models/net-pilot-rune-dfm-g4.npz
test -f $R/time4.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86028900 --time 24 --workers 4 --out $R/time-g4.jsonl > $R/time4.log 2>&1; touch $R/time4.done; }
N=$(tail -1 $R/time4.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*')
echo "N=$N" >> $R/g4.log
python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:$N+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86028000 --pairs 300 --workers 4 --out $R/gate-g4.jsonl > $R/gate4.log 2>&1
touch $R/gate4.done
;;
esac
