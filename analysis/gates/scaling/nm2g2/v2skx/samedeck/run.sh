#!/bin/bash
# Same-deck N against v2skx for the NM2 gen-2 bot, on the analysis line's machine under gate load (3 processes; the
# architecture thread 11:59Z): ramp-t, nemesis-t and a second ramp-t run at once (the replicate shows the run-to-run
# spread). Positions: the builder's rec-cost-nm2.jsonl.gz (ac985de; the first 30 games of 78700006/08/10). Code and
# specs: the builder's ac985de (data/samedeck/nm2g2-*.json). Then samedeck_fit.py.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx/samedeck
cd $S/wt_samedeck
export PYTHONPATH=$S/wt_samedeck
R=analysis/scaling/data/samedeck/rec-cost-nm2.jsonl.gz
specs() {  # deck
  python3 -c "
import json,sys
d=json.load(open('analysis/scaling/data/samedeck/nm2g2-$1.json'))
print(' '.join(f'--spec {k}={v[\"spec\"]}' for k,v in d['specs'].items()))"
}
python3 analysis/scaling/puct_cost.py --records $R --games 90 --deck ramp-t $(specs ramp-t) --out $OUT/ramp-t.json > $OUT/ramp-t.log 2>&1 &
python3 analysis/scaling/puct_cost.py --records $R --games 90 --deck nemesis-t $(specs nemesis-t) --out $OUT/nemesis-t.json > $OUT/nemesis-t.log 2>&1 &
python3 analysis/scaling/puct_cost.py --records $R --games 90 --deck ramp-t $(specs ramp-t) --out $OUT/ramp-t-rep.json > $OUT/ramp-t-rep.log 2>&1 &
wait
python3 analysis/scaling/samedeck_fit.py $OUT/ramp-t.json $OUT/nemesis-t.json $OUT/ramp-t-rep.json > $OUT/fit.jsonl 2>&1
cat $OUT/fit.jsonl
