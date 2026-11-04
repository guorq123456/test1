#!/bin/bash
# DFM rune hero gen 3: hero mcts:61 + g2 (g2's time-matched N), self-play 86025000; train fresh on gens 1-3; time 86026900; gate 86026000.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ
test -f $R/g3-selfplay.done || { nice -n 10 python3 -m svsim.learn.scaledata play --pool $F --hero $H     --hero-spec "mcts:61+plan+setnet=analysis/scaling/models/net-pilot-rune-dfm-g2.npz+netmid+netany" --spec mcts:100+plan     --base 86025000 --stride 2 --shards 0 10 --per-shard 1000 --workers 4 --every 500 --out $R/rec-g3 >> $R/g3.log 2>&1; touch $R/g3-selfplay.done; }
mkdir -p $R/enc3
for f in $R/rec/rec-*.jsonl.gz $R/rec-g2/rec-*.jsonl.gz $R/rec-g3/rec-*.jsonl.gz $R/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc3/; done
test -f $R/tok3.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc3 --out $R/tok3 --workers 4 >> $R/g3.log 2>&1; touch $R/tok3.done; }
test -f $R/mid3.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc3 --out $R/mid3 --workers 4 >> $R/g3.log 2>&1; touch $R/mid3.done; }
test -f $R/train3.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok3 --end 85995000:10 --end 85998000:10 --end 86025000:10     --mid-dir $R/mid3 --mid 85995000:10 --mid 85998000:10 --mid 86025000:10 --holdout 85996000 85996002 --name pilot-rune-dfm-g3     --checkpoint $R/ckpt-g3.npz >> $R/g3-train.log 2>&1; touch $R/train3.done; }
NET=analysis/scaling/models/net-pilot-rune-dfm-g3.npz
test -f $R/time3.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86026900 --time 24 --workers 4 --out $R/time-g3.jsonl > $R/time3.log 2>&1; touch $R/time3.done; }
N=$(tail -1 $R/time3.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*')
echo "N=$N" >> $R/g3.log
python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:$N+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86026000 --pairs 300 --workers 4 --out $R/gate-g3.jsonl > $R/gate3.log 2>&1
touch $R/gate3.done
