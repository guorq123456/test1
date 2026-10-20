#!/bin/bash
# NM3 generation-2 self-play (README 47d4360): both sides the NM3 bot (2e5e17a specs; elf-t N 88, nemesis-t
# N 75, the install N after the gate's in-gate time). Training 80500000 + 2k (k 0-9), then holdout 80600000 + 2h.
# A seed in $S/nm3g2/SKIP is not played here; stops before the next shard when $S/nm3g2/PAUSE exists. Code 2e5e17a.
cd /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/wt_nm3
export PYTHONPATH=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/wt_nm3
ELF="mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3-elf-t.npz:2:1"
NEM="mcts:75+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3-nemesis-t.npz:2:1"
for job in "80500000 0" "80500000 1" "80500000 2" "80500000 3" "80500000 4" "80500000 5" "80500000 6" "80500000 7" "80500000 8" "80500000 9" "80600000 0" "80600000 1" "80600000 2" "80600000 3" "80600000 4"; do
  set -- $job
  seed=$(($1 + 2*$2))
  [ -e /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/nm3g2/rec/rec-$seed.jsonl.gz ] && continue
  if [ -e /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/nm3g2/PAUSE ]; then echo "paused before $seed"; exit 0; fi
  if grep -qx "$seed" /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/nm3g2/SKIP 2>/dev/null; then echo "skip $seed (another line)"; continue; fi
  python3 -m svsim.learn.scaledata play --deck elf-t --opponent nemesis-t --spec "$ELF" --opponent-spec "$NEM" --base $1 --stride 2 --shards $2 $(($2 + 1)) --per-shard 1000 --workers 3 --out /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/nm3g2/rec || { echo "FAILED $1 $2"; exit 1; }
  echo "done $seed at $(date -u +%H:%M:%S)"
done
echo DONE
