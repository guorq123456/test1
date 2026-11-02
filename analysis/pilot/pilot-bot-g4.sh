#!/bin/bash
# bot rune hero gen 4 (here, the builder is on the Portal pair): hero mcts:66 + g3 (g3's time-matched N), self-play 86022000;
# train fresh on gens 1-4 (40 shards); time 86023900; gate 86023000. Stages A/B/C/D, each under the 2 h background limit.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/botg4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
D=analysis/pilot/data R=runs/pilot-bot F=analysis/pilot/fields/bot-frozen7.txt H=bot/T3-RUNE-1
mkdir -p $R
play() { nice -n 10 python3 -m svsim.learn.scaledata play --pool $F --hero $H     --hero-spec "mcts:66+plan+setnet=analysis/scaling/models/net-pilot-rune-bot-g3.npz+netmid+netany" --spec mcts:100+plan     --base 86022000 --stride 2 --shards $1 $2 --per-shard 1000 --workers 4 --every 500 --out $R/rec-g4 >> $R/g4.log 2>&1; }
case "$1" in
A) play 0 5 ;;
B) play 5 10; touch $R/g4-selfplay.done ;;
C)
test -f $R/g4-selfplay.done
mkdir -p $R/enc4
for f in $D/rec/rec-*.jsonl.gz $D/rec-g2/rec-*.jsonl.gz $D/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz $D/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc4/; done
test -f $R/tok4.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc4 --out $R/tok4 --workers 4 >> $R/g4.log 2>&1; touch $R/tok4.done; }
test -f $R/mid4.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc4 --out $R/mid4 --workers 4 >> $R/g4.log 2>&1; touch $R/mid4.done; }
test -f $R/train4.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok4 --end 85990000:10 --end 85993000:10 --end 86020000:10 --end 86022000:10     --mid-dir $R/mid4 --mid 85990000:10 --mid 85993000:10 --mid 86020000:10 --mid 86022000:10 --holdout 85991000 85991002 --name pilot-rune-bot-g4     --checkpoint $R/ckpt-g4.npz >> $R/g4-train.log 2>&1; touch $R/train4.done; }
;;
D)
NET=analysis/scaling/models/net-pilot-rune-bot-g4.npz
test -f $R/time4.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86023900 --time 24 --workers 4 --out $R/time-g4.jsonl > $R/time4.log 2>&1; touch $R/time4.done; }
N=$(tail -1 $R/time4.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*')
echo "N=$N" >> $R/g4.log
python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:$N+plan+setnet=$NET+netmid+netany"     --base mcts:100+plan --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 4 --out $R/gate-g4.jsonl > $R/gate4.log 2>&1
touch $R/gate4.done
;;
esac
# G3: g3 at its equal-CPU N (58) on g4's gate deals, to pair g4 - g3 on the same deals (as the DFM rows)
case "$1" in
G3) cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/botg4
    python3 -m svsim.tools.herogate --hero bot/T3-RUNE-1 --field analysis/pilot/fields/bot-frozen7.txt \
      --x "mcts:58+plan+setnet=analysis/scaling/models/net-pilot-rune-bot-g3.npz+netmid+netany" --base mcts:100+plan \
      --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 3 --out runs/pilot-bot/gate4bank-g3-n58.jsonl \
      > runs/pilot-bot/gate4bank-g3-n58.log 2>&1 ;;
esac
