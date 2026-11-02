#!/bin/bash
# The prior arm (PRIOR-PORTAL.md): time match once, the 300-pair gate on the hero's gen-3 bank, an equal-CPU rerun if
# the in-gate ratio is over 1.08, then the pairing with the net's own equal-CPU row.  Run on an idle machine.
#   prior-gate.sh HERO FIELD RUNDIR NET PRIOR TAG TIME_SEED GATE_SEED NET_ROW_JSONL
set -u
HERO=$1 FIELD=$2 RUN=$3 NET=$4 PRI=$5 TAG=$6 TSEED=$7 GSEED=$8 ROW=$9
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
START=$(date +%s); LIMIT=${LIMIT:-6900}
left() { local l=$((LIMIT - $(date +%s) + START)); [ $l -gt 60 ] && echo $l || echo 60; }
X="+plan+setnet=$NET+netmid+netany+puct=$PRI:2:1"
L=$RUN/logs
G() { timeout $(left) python3 -m svsim.tools.herogate --hero "$HERO" --field $FIELD --base mcts:100+plan --opp mcts:100+plan --workers 4 "$@"; }
grep -q "时间匹配" $L/time-prior-$TAG.log 2>/dev/null || G --x "mcts:100$X" --seed $TSEED --time 24 --out $L/time-prior-$TAG.jsonl > $L/time-prior-$TAG.log 2>&1
N=$(grep -o "→ N 100 → [0-9]*" $L/time-prior-$TAG.log | grep -o "[0-9]*$"); [ -n "$N" ] || { echo "time match incomplete"; exit 1; }
G --x "mcts:$N$X" --seed $GSEED --pairs 300 --out $L/gate-prior-$TAG-n$N.jsonl > $L/gate-prior-$TAG-n$N.log 2>&1
R=$(grep -o "比 [0-9.]*" $L/gate-prior-$TAG-n$N.log | tail -1 | grep -o "[0-9.]*$"); [ -n "$R" ] || { echo "gate incomplete"; exit 1; }
echo "N $N in-gate ratio $R"
F=$L/gate-prior-$TAG-n$N.jsonl
if python3 -c "import sys; sys.exit(0 if float('$R') > 1.08 else 1)"; then
    N2=$(python3 -c "print(max(1, round($N / $R)))")
    G --x "mcts:$N2$X" --seed $GSEED --pairs 300 --out $L/gate-prior-$TAG-n$N2.jsonl > $L/gate-prior-$TAG-n$N2.log 2>&1
    grep -q "^300 对" $L/gate-prior-$TAG-n$N2.log || { echo "equal-CPU gate incomplete"; exit 1; }
    echo "equal-CPU N $N2"; F=$L/gate-prior-$TAG-n$N2.jsonl
fi
grep -h "^300 对\|比 " $L/gate-prior-$TAG-n*.log
python3 analysis/pilot/paired.py $F $ROW
