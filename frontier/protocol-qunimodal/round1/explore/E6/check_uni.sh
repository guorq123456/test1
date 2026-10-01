#!/bin/bash
# Run ground-truth checker on the whole sufficiency region for each r; prints r, #instances, #non-unimodal
cd /tmp/claude-0/qu/explore/E6
for r in 2 3 4 5 6; do
 ( python3 gen_region.py $r | /tmp/claude-0/qu/tools/uni | awk -v r=$r '{n++; if($1==0) z++} END{print "r="r" instances="n" non_unimodal="z+0}' > uni_r$r.txt ) &
done
wait
cat uni_r*.txt
