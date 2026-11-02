#!/bin/bash
# DFM rune hero: a move prior (learn.setpolicy) on the hero's decisions of the net-guided self-play (gens 3 and 4),
# trunk from net-pilot-rune-dfm-g3, fine-tuned, tau 0.5 (the precedent's prior-*-ft-t05). Isolated, measurement only.
set -e
cd /tmp/claude-0/-home-claude-test1/e4ec387d-7120-5b27-b512-265616e53678/scratchpad/wt/pilot
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
R=runs/pilot-dfm
mkdir -p $R/enc-dec
for f in $R/rec-g3/rec-*.jsonl.gz $R/rec-g4/rec-*.jsonl.gz; do ln -sf "$(realpath $f)" $R/enc-dec/; done
test -f $R/dec.done || { nice -n 10 python3 analysis/pilot/setpolicy_named.py encode --records $R/enc-dec --out $R/dec --workers 2 --deck dfm/RUNE-ユーリ >> $R/prior.log 2>&1; touch $R/dec.done; }
SH=$(for k in $(seq 0 9); do echo $((86025000+2*k)) $((86027000+2*k)); done | tr '\n' ' ')
test -f $R/prior.done || { nice -n 10 python3 -m svsim.learn.setpolicy fit --data $R/dec --cards $R/tok4/cards.npz --shards $SH     --init analysis/scaling/models/net-pilot-rune-dfm-g3.npz --tau 0.5 --ftz --checkpoint $R/ckpt-prior.npz     --out analysis/scaling/models/prior-pilot-rune-dfm-ft-t05.npz >> $R/prior.log 2>&1; touch $R/prior.done; }
