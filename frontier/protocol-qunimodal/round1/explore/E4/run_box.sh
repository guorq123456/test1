#!/bin/bash
# Score rule.py against the ground-truth checker on the whole fit box, one r at a time.
cd /tmp/claude-0/qu/explore/E4
for r in "$@"; do
  paste -d'|' <(python3 gen_box.py $r) <(python3 gen_box.py $r | /tmp/claude-0/qu/tools/uni) | python3 score.py > score_r$r.txt
done
