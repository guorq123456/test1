#!/bin/bash
# DFM rune hero, prior arm (analysis/pilot/PRIOR.md): X = g3 value net + PUCT with the move prior. T: time-match on
# 86028900; G: gate on 86028000 at that N; E: if the in-gate CPU ratio > 1.08, the same deals at round(N / ratio).
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ
NET=analysis/scaling/models/net-pilot-rune-dfm-g3.npz PRI=analysis/scaling/models/prior-pilot-rune-dfm-ft-t05.npz
X() { echo "mcts:$1+plan+setnet=$NET+netmid+netany+puct=$PRI:2:1"; }
case "$1" in
T) test -f $R/timeP.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X 100)" \
     --base mcts:100+plan --opp mcts:100+plan --seed 86028900 --time 24 --workers 4 --out $R/time-prior.jsonl > $R/timeP.log 2>&1; touch $R/timeP.done; } ;;
G) N=$(tail -1 $R/timeP.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*'); echo "prior N=$N" >> $R/g4.log
   test -f $R/gateP.done || { python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $N)" \
     --base mcts:100+plan --opp mcts:100+plan --seed 86028000 --pairs 300 --workers 4 --out $R/gate-prior-n$N.jsonl > $R/gateP.log 2>&1; touch $R/gateP.done; } ;;
E) N=$2; test -n "$N"
   python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $N)" \
     --base mcts:100+plan --opp mcts:100+plan --seed 86028000 --pairs 300 --workers 4 --out $R/gate-prior-n$N.jsonl > $R/gateP-n$N.log 2>&1 ;;
esac
