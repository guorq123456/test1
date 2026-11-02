#!/bin/bash
# DFM rune hero, round 2 (analysis/pilot/ROUND2.md). A/B: self-play halves; C: encode + value g5; P: decisions + prior 2;
# T: time; G N: gate.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ M=analysis/scaling/models
HERO="mcts:31+plan+setnet=$M/net-pilot-rune-dfm-g3.npz+netmid+netany+puct=$M/prior-pilot-rune-dfm-ft-t05.npz:2:1"
X() { echo "mcts:$1+plan+setnet=$M/net-pilot-rune-dfm-g5.npz+netmid+netany+puct=$M/prior2-pilot-rune-dfm-ft-t05.npz:2:1"; }
play() { nice -n 10 python3 -m svsim.learn.scaledata play --pool $F --hero $H --hero-spec "$HERO" --spec mcts:100+plan \
  --base 86041000 --stride 2 --shards $1 $2 --per-shard 1000 --workers 4 --every 500 --out $R/rec-r2 >> $R/r2.log 2>&1; }
case "$1" in
A) play 0 5 ;;
B) play 5 10; touch $R/r2-selfplay.done ;;
C) test -f $R/r2-selfplay.done
   mkdir -p $R/enc5
   for f in $R/rec/rec-*.jsonl.gz $R/rec-g2/rec-*.jsonl.gz $R/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz $R/rec-r2/rec-*.jsonl.gz $R/holdout/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc5/; done
   test -f $R/tok5.done || { nice -n 10 python3 -m svsim.learn.scaledata encode --records $R/enc5 --out $R/tok5 --workers 4 >> $R/r2.log 2>&1; touch $R/tok5.done; }
   test -f $R/mid5.done || { nice -n 10 python3 -m svsim.learn.midrows encode --records $R/enc5 --out $R/mid5 --workers 4 >> $R/r2.log 2>&1; touch $R/mid5.done; }
   E=$(grep -o -- '--end [0-9:]*' runs/pilot-dfm/pilot-dfm-g4.sh | tr '\n' ' '); MID=$(grep -o -- '--mid [0-9:]*' runs/pilot-dfm/pilot-dfm-g4.sh | tr '\n' ' ')
   HO=$(grep -o -- '--holdout [0-9 ]*' runs/pilot-dfm/pilot-dfm-g4.sh | head -1)
   test -f $R/train5.done || { nice -n 10 python3 analysis/scaling/train_mid.py --shared --fresh --tokens $R/tok5 $E --end 86041000:10 \
     --mid-dir $R/mid5 $MID --mid 86041000:10 $HO --name pilot-rune-dfm-g5 --checkpoint $R/ckpt-g5.npz >> $R/g5-train.log 2>&1; touch $R/train5.done; } ;;
P) mkdir -p $R/enc-dec2
   for f in $R/rec-g4/rec-*.jsonl.gz $R/rec-r2/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc-dec2/; done
   test -f $R/dec2.done || { nice -n 10 python3 analysis/pilot/setpolicy_named.py encode --records $R/enc-dec2 --out $R/dec2 --workers 3 --deck $H >> $R/prior2.log 2>&1; touch $R/dec2.done; }
   SH=$(for k in $(seq 0 9); do echo $((86027000+2*k)) $((86041000+2*k)); done | tr '\n' ' ')
   test -f $R/prior2.done || { nice -n 10 python3 -m svsim.learn.setpolicy fit --data $R/dec2 --cards $R/tok5/cards.npz --shards $SH \
     --init $M/net-pilot-rune-dfm-g5.npz --tau 0.5 --ftz --epochs 35 --checkpoint $R/ckpt-prior2.npz --out $M/prior2-pilot-rune-dfm-ft-t05.npz >> $R/prior2.log 2>&1; touch $R/prior2.done; } ;;
T) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X 100)" --base mcts:100+plan --opp mcts:100+plan --seed 86044900 --time 24 --workers 4 --out $R/time-r2.jsonl > $R/timeR2.log 2>&1 ;;
G) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $2)" --base mcts:100+plan --opp mcts:100+plan --seed 86028000 --pairs 300 --workers 4 --out $R/gate-r2-n$2.jsonl > $R/gateR2-n$2.log 2>&1 ;;
esac
