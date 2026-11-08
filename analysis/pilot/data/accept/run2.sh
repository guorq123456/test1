#!/bin/bash
# Unseen-opponent acceptance (PAGE-INSTALL.md A4/A5): page normal N vs mcts:100+plan, field fields/unseen/<key>.txt,
# 87202800 + 100 i, 100 pairs. Waits for run.sh to finish first.
P=/tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad; T=$P/wt/trainer; cd $T
while pgrep -f "accept/run.sh" > /dev/null; do sleep 20; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
KEYS=(T1-SWORD-1 T1-ABYSS-1 T3-RUNE-1 T1-HAVEN-1 T1-PORTAL-1)
for i in 0 1 2 3 4; do
  k=${KEYS[$i]}
  x=$(python3 -c "from svsim.ui.session import PILOTS; print(PILOTS[('normal','$k')])")
  python3 -m svsim.tools.herogate --hero bot/$k --field analysis/pilot/fields/unseen/$k.txt --x "$x" --base mcts:100+plan \
    --opp mcts:100+plan --seed $((87202800+100*i)) --pairs 100 --workers 4 --bank confirm --out $P/accept/unseen-$k.jsonl > $P/accept/unseen-$k.log 2>&1
done
echo ALLDONE2
