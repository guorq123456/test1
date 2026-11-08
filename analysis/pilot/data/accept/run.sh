#!/bin/bash
# Acceptance gates for the trainer's pilots (analysis/pilot/PAGE-INSTALL.md): normal at the page N (87202100+100i),
# then strong at the page N (87201400+100i), 100 pairs each, field bot-frozen7, opponents mcts:100+plan.
P=/tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad; T=$P/wt/trainer; cd $T
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
KEYS=(T1-SWORD-1 T1-ABYSS-1 T3-RUNE-1 T1-HAVEN-1 T1-PORTAL-1)
for lv in normal strong; do
 for i in 0 1 2 3 4; do
  k=${KEYS[$i]}
  x=$(python3 -c "from svsim.ui.session import PILOTS; print(PILOTS[('$lv','$k')])")
  if [ $lv = normal ]; then base=mcts:100+plan; seed=$((87202100+100*i)); else base=mcts:400+plan; seed=$((87201400+100*i)); fi
  python3 -m svsim.tools.herogate --hero bot/$k --field analysis/pilot/fields/bot-frozen7.txt --x "$x" --base $base \
    --opp mcts:100+plan --seed $seed --pairs 100 --workers 4 --bank confirm --out $P/accept/$lv-$k.jsonl > $P/accept/$lv-$k.log 2>&1
 done
done
echo ALLDONE
