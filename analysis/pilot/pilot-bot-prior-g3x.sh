#!/bin/bash
# exploratory: bot rune g3 + g3-init prior. T: time 86024800; G N: gate 86023000.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/botg4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-bot F=analysis/pilot/fields/bot-frozen7.txt H=bot/T3-RUNE-1
X() { echo "mcts:$1+plan+setnet=analysis/scaling/models/net-pilot-rune-bot-g3.npz+netmid+netany+puct=analysis/scaling/models/prior-pilot-rune-bot-g3init-ft-t05.npz:2:1"; }
case "$1" in
T) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X 100)" --base mcts:100+plan --opp mcts:100+plan --seed 86024800 --time 24 --workers 3 --out $R/time-prior-g3x.jsonl > $R/timeP-g3x.log 2>&1
   N=$(tail -1 $R/timeP-g3x.log | grep -o '→ [0-9]*$' | grep -o '[0-9]*'); echo "N=$N"
   python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $N)" --base mcts:100+plan --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 3 --out $R/gate-prior-g3x-n$N.jsonl > $R/gateP-g3x-n$N.log 2>&1 ;;
G) python3 -m svsim.tools.herogate --hero $H --field $F --x "$(X $2)" --base mcts:100+plan --opp mcts:100+plan --seed 86023000 --pairs 300 --workers 3 --out $R/gate-prior-g3x-n$2.jsonl > $R/gateP-g3x-n$2.log 2>&1 ;;
esac
