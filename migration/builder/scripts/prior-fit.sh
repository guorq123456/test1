#!/bin/bash
# The Portal pair's move prior (analysis/pilot/PRIOR-PORTAL.md): encode the hero's decisions, fit from INIT.
#   prior-fit.sh HERO RUNDIR INIT TAG SHARD_BASES(comma)
set -u
HERO=$1 RUN=$2 INIT=$3 TAG=$4 BASES=$5
cd /home/user/test1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
START=$(date +%s); LIMIT=${LIMIT:-6900}
left() { local l=$((LIMIT - $(date +%s) + START)); [ $l -gt 60 ] && echo $l || echo 60; }
LOG=$RUN/logs/prior-$TAG.log
test -f $RUN/dec.done || { timeout $(left) nice -n 10 python3 analysis/pilot/setpolicy_named.py encode --records $RUN/enc-dec --out $RUN/dec \
    --workers 3 --deck "$HERO" >> $LOG 2>&1 && touch $RUN/dec.done; }
test -f $RUN/dec.done || { echo "encode incomplete" >> $LOG; exit 1; }
SH=$(for b in ${BASES//,/ }; do for k in $(seq 0 9); do echo $((b + 2 * k)); done; done | tr '\n' ' ')
OUT=analysis/scaling/models/prior-pilot-portal-$TAG-ft-t05.npz
test -f $OUT || timeout $(left) nice -n 10 python3 -m svsim.learn.setpolicy fit --data $RUN/dec --cards $RUN/tok/cards.npz --shards $SH \
    --init $INIT --tau 0.5 --ftz --epochs 35 --checkpoint $RUN/ckpt-prior-$TAG.npz --out $OUT >> $LOG 2>&1
test -f $OUT && echo "fit done" >> $LOG || echo "fit incomplete" >> $LOG
