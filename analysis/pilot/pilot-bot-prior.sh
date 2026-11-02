#!/bin/bash
# bot rune hero: move prior (analysis/pilot/PRIOR.md, bot section). E: encode hero decisions of gens 3-4;
# F INIT: fit from INIT (the better of g3/g4); T/G/X: time 86024900, gate 86023000, equal-CPU rerun at N.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/botg4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
D=analysis/pilot/data R=runs/pilot-bot F=analysis/pilot/fields/bot-frozen7.txt H=bot/T3-RUNE-1
PRI=analysis/scaling/models/prior-pilot-rune-bot-ft-t05.npz
case "$1" in
E) mkdir -p $R/enc-dec
   for f in $D/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc-dec/; done
   test -f $R/dec.done || { nice -n 10 python3 analysis/pilot/setpolicy_named.py encode --records $R/enc-dec --out $R/dec --workers 3 --deck $H >> $R/prior.log 2>&1; touch $R/dec.done; } ;;
F) INIT=$2; TAG=$3; test -f "$INIT"; test -n "$TAG"
   SH=$(for k in $(seq 0 9); do echo $((86020000+2*k)) $((86022000+2*k)); done | tr '\n' ' ')
   test -f $R/prior-$TAG.done || { nice -n 10 python3 -m svsim.learn.setpolicy fit --data $R/dec --cards $R/tok4/cards.npz --shards $SH \
     --init $INIT --tau 0.5 --ftz --epochs 35 --checkpoint $R/ckpt-prior-$TAG.npz --out analysis/scaling/models/prior-pilot-rune-bot-$TAG-ft-t05.npz >> $R/prior-$TAG.log 2>&1; touch $R/prior-$TAG.done; } ;;
T) NET=$2; test -f $R/timeP.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=$NET+netmid+netany+puct=$PRI:2:1" \
     --base mcts:100+plan --opp mcts:100+plan --seed 86024900 --time 24 --workers 4 --out $R/time-prior.jsonl > $R/timeP.log 2>&1; touch $R/timeP.done; } ;;
G) NET=$2; N=$3; python3 -m svsim.tools.herogate --hero $H --field $F --x "mcts:$N+plan+setnet=$NET+netmid+netany+puct=$PRI:2:1" \
     --base mcts:100+plan --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 4 --out $R/gate-prior-n$N.jsonl > $R/gateP-n$N.log 2>&1 ;;
esac
