#!/bin/bash
# One generation of the pilot recipe for a hero (the architecture thread 2026-11-01 06:10Z): self-play (10 shards x
# 1000, resumable), the holdout (gen 1 only), encode, a fresh net on the listed generations' shards, the time match
# once, the 300-pair gate, and an equal-CPU check if the in-gate CPU ratio is above 1.08.
#   pilot-gen.sh HERO FIELD RUNDIR NAME SELF_BASE HOLDOUT_BASE|- HERO_SPEC|- TRAIN_BASES(comma) TIME_SEED GATE_SEED [STAGE]
# STAGE: play (the self-play only), rest (the holdout onward), all (default). Each background task stays under the
# 2-hour limit: the self-play (~2 h) and the rest (~1 h) run as separate planned chunks.
set -u
# One deadline for the whole chunk (LIMIT seconds, default 6900, under the 2-hour task limit); every step gets
# what is left, so no step outlives the chunk (an outer timeout killed the script but not its inner timeout child).
START=$(date +%s); LIMIT=${LIMIT:-6900}
left() { local l=$((LIMIT - $(date +%s) + START)); [ $l -gt 60 ] && echo $l || echo 60; }
HERO=$1 FIELD=$2 RUN=$3 NAME=$4 SELF=$5 HOLD=$6 HSPEC=$7 TRAIN=$8 TSEED=$9 GSEED=${10} STAGE=${11:-all}
cd /home/user/test1
mkdir -p $RUN/enc $RUN/logs
LOG=$RUN/logs/$NAME.log
echo "== $(date -u +%FT%TZ) $NAME: hero $HERO field $FIELD self $SELF holdout $HOLD hero-spec $HSPEC train $TRAIN" >> $LOG
play() {   # base out [hero-spec]
    local base=$1 out=$2 n=$3 extra=()
    [ "$4" != "-" ] && extra=(--hero-spec "$4")
    [ "$(ls $out/rec-*.jsonl.gz 2>/dev/null | wc -l)" -ge "$n" ] && return 0
    timeout $(left) python3 -m svsim.learn.scaledata play --pool $FIELD --hero "$HERO" "${extra[@]}" --spec "mcts:100+plan" \
            --base $base --stride 2 --shards 0 $n --per-shard 1000 --workers ${WORKERS:-4} --every 500 --out $out >> $LOG 2>&1
    [ "$(ls $out/rec-*.jsonl.gz 2>/dev/null | wc -l)" -ge "$n" ]
}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
if [ "$STAGE" != rest ]; then play $SELF $RUN/rec-$SELF 10 "$HSPEC" || { echo "self-play incomplete" >> $LOG; exit 1; }; fi
[ "$STAGE" = play ] && { echo "== $(date -u +%FT%TZ) $NAME self-play done" >> $LOG; exit 0; }
[ "$(ls $RUN/rec-$SELF/rec-*.jsonl.gz 2>/dev/null | wc -l)" -ge 10 ] || { echo "self-play incomplete" >> $LOG; exit 1; }
if [ "$HOLD" != "-" ]; then play $HOLD $RUN/holdout 2 "-" || { echo "holdout incomplete" >> $LOG; exit 1; }; fi
for f in $RUN/rec-*/rec-*.jsonl.gz $RUN/holdout/rec-*.jsonl.gz; do [ -e "$f" ] && ln -sf "$(realpath $f)" $RUN/enc/; done
python3 -m svsim.learn.scaledata encode --records $RUN/enc --out $RUN/tok --workers 4 >> $LOG 2>&1 &&
python3 -m svsim.learn.midrows encode --records $RUN/enc --out $RUN/mid --workers 4 >> $LOG 2>&1 || { echo "encode failed" >> $LOG; exit 1; }
ENDS=() MIDS=()
for b in ${TRAIN//,/ }; do ENDS+=(--end $b:10); MIDS+=(--mid $b:10); done
HOLDS=$(ls $RUN/holdout/rec-*.jsonl.gz | sed -E 's#.*/rec-([0-9]+)\.jsonl\.gz#\1#' | tr '\n' ' ')
if [ ! -f analysis/scaling/models/net-$NAME.npz ]; then
    timeout $(left) python3 analysis/scaling/train_mid.py --shared --fresh --tokens $RUN/tok "${ENDS[@]}" --mid-dir $RUN/mid \
        "${MIDS[@]}" --holdout $HOLDS --name $NAME --checkpoint $RUN/ckpt-$NAME.npz >> $RUN/logs/train-$NAME.log 2>&1
fi
[ -f analysis/scaling/models/net-$NAME.npz ] || { echo "train failed" >> $LOG; exit 1; }
NET=analysis/scaling/models/net-$NAME.npz
X="+plan+setnet=$NET+netmid+netany"
timeout $(left) python3 -m svsim.tools.herogate --hero "$HERO" --field $FIELD --x "mcts:100$X" --base mcts:100+plan --opp mcts:100+plan \
    --seed $TSEED --time 24 --workers 4 --out $RUN/logs/time-$NAME.jsonl > $RUN/logs/time-$NAME.log 2>&1
N=$(grep -o "→ N 100 → [0-9]*" $RUN/logs/time-$NAME.log | grep -o "[0-9]*$")
[ -n "$N" ] || { echo "time match failed" >> $LOG; exit 1; }
timeout $(left) python3 -m svsim.tools.herogate --hero "$HERO" --field $FIELD --x "mcts:$N$X" --base mcts:100+plan --opp mcts:100+plan \
    --seed $GSEED --pairs 300 --workers 4 --out $RUN/logs/gate-$NAME.jsonl > $RUN/logs/gate-$NAME.log 2>&1
R=$(grep -o "比 [0-9.]*" $RUN/logs/gate-$NAME.log | tail -1 | grep -o "[0-9.]*$")
echo "N $N in-gate ratio $R" >> $LOG
if python3 -c "import sys; sys.exit(0 if float('$R') > 1.08 else 1)"; then
    N2=$(python3 -c "print(max(1, round($N / $R)))")
    timeout $(left) python3 -m svsim.tools.herogate --hero "$HERO" --field $FIELD --x "mcts:$N2$X" --base mcts:100+plan --opp mcts:100+plan \
        --seed $GSEED --pairs 300 --workers 4 --out $RUN/logs/gate-$NAME-n$N2.jsonl > $RUN/logs/gate-$NAME-n$N2.log 2>&1
    echo "equal-CPU N $N2" >> $LOG
fi
echo "== $(date -u +%FT%TZ) $NAME done" >> $LOG
grep -h "^300 对\|比 " $RUN/logs/gate-$NAME*.log
