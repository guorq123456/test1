#!/bin/bash
# DFM rune hero gen 2: encode gen 1 + gen 2 + holdout together, train fresh on 20 shards, time-match, gate on 85999000.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm
test -f $R/g2-selfplay.done
mkdir -p $R/enc2
for f in $R/rec/rec-*.jsonl.gz $R/rec-g2/rec-*.jsonl.gz $R/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc2/; done
test -f $R/tok2.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc2 --out $R/tok2 --workers 4 >> $R/g2.log 2>&1; touch $R/tok2.done; }
test -f $R/mid2.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc2 --out $R/mid2 --workers 4 >> $R/g2.log 2>&1; touch $R/mid2.done; }
test -f $R/train2.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok2 --end 85995000:10 --end 85998000:10     --mid-dir $R/mid2 --mid 85995000:10 --mid 85998000:10 --holdout 85996000 85996002 --name pilot-rune-dfm-g2     --checkpoint $R/ckpt-g2.npz >> $R/g2-train.log 2>&1; touch $R/train2.done; }
F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ NET=analysis/scaling/models/net-pilot-rune-dfm-g2.npz
test -f $R/time2.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 85999900 --time 24 --workers 4 --out $R/time-g2.jsonl > $R/time2.log 2>&1; touch $R/time2.done; }
N=$(tail -1 $R/time2.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*')
echo "N=$N" >> $R/g2.log
python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:$N+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 85999000 --pairs 300 --workers 4 --out $R/gate-g2.jsonl > $R/gate2.log 2>&1
touch $R/gate2.done
