#!/bin/bash
# Save ground-truth bits for the whole fit box, in gen_box.py enumeration order (one file per r).
cd /tmp/claude-0/qu/explore/E4
for r in "$@"; do
  python3 gen_box.py $r | /tmp/claude-0/qu/tools/uni > truth_r$r.txt
done
