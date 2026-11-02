#!/bin/bash
# bot rune hero, round 2 (analysis/pilot/ROUND2.md on claude/pilot-dfm). A/B: self-play halves; C: encode + value g5;
# P: decisions + prior 2; T: time; G N: gate.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/botg4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
D=analysis/pilot/data R=runs/pilot-bot F=analysis/pilot/fields/bot-frozen7.txt H=bot/T3-RUNE-1 M=analysis/scaling/models
HERO="mcts:30+plan+setnet=$M/net-pilot-rune-bot-g4.npz+netmid+netany+puct=$M/prior-pilot-rune-bot-ft-t05.npz:2:1"
X() { echo "mcts:$1+plan+setnet=$M/net-pilot-rune-bot-g5.npz+netmid+netany+puct=$M/prior2-pilot-rune-bot-ft-t05.npz:2:1"; }
play() { nice -n 10 python3 -m svsim.learn.scaledata play --pool $F --hero $H --hero-spec "$HERO" --spec mcts:100+plan \
  --base 86043000 --stride 2 --shards $1 $2 --per-shard 1000 --workers ${W:-4} --every 500 --out $R/rec-r2 >> $R/r2.log 2>&1; }
case "$1" in
A) play 0 5 ;;
B) play 5 10; touch $R/r2-selfplay.done ;;
C) test -f $R/r2-selfplay.done
   mkdir -p $R/enc5
   for f in $D/rec/rec-*.jsonl.gz $D/rec-g2/rec-*.jsonl.gz $D/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz $R/rec-r2/rec-*.jsonl.gz $D/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc5/; done
   test -f $R/tok5.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc5 --out $R/tok5 --workers 4 >> $R/r2.log 2>&1; touch $R/tok5.done; }
   test -f $R/mid5.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc5 --out $R/mid5 --workers 4 >> $R/r2.log 2>&1; touch $R/mid5.done; }
   test -f $R/train5.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok5 --end 85990000:10 --end 85993000:10 --end 86020000:10 --end 86022000:10 --end 86043000:10 \
     --mid-dir $R/mid5 --mid 85990000:10 --mid 85993000:10 --mid 86020000:10 --mid 86022000:10 --mid 86043000:10 --holdout 85991000 85991002 --name pilot-rune-bot-g5 \
     --checkpoint $R/ckpt-g5.npz >> $R/g5-train.log 2>&1; touch $R/train5.done; } ;;
P) mkdir -p $R/enc-dec2
   for f in $R/rec-g4/rec-*.jsonl.gz $R/rec-r2/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc-dec2/; done
   test -f $R/dec2.done || { nice -n 10 python3 analysis/pilot/setpolicy_named.py encode --records $R/enc-dec2 --out $R/dec2 --workers 3 --deck $H >> $R/prior2.log 2>&1; touch $R/dec2.done; }
   SH=$(for k in $(seq 0 9); do echo $((86022000+2*k)) $((86043000+2*k)); done | tr '\n' ' ')
   test -f $R/prior2.done || { nice -n 10 python3 -m svsim.learn.setpolicy fit --data $R/dec2 --cards $R/tok5/cards.npz --shards $SH \
     --init $M/net-pilot-rune-bot-g5.npz --tau 0.5 --ftz --epochs 35 --checkpoint $R/ckpt-prior2.npz --out $M/prior2-pilot-rune-bot-ft-t05.npz >> $R/prior2.log 2>&1; touch $R/prior2.done; } ;;
T) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X 100)" --base mcts:100+plan --opp mcts:100+plan --seed 86044800 --time 24 --workers 4 --out $R/time-r2.jsonl > $R/timeR2.log 2>&1 ;;
G) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $2)" --base mcts:100+plan --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 4 --out $R/gate-r2-n$2.jsonl > $R/gateR2-n$2.log 2>&1 ;;
esac
