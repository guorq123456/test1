#!/bin/bash
# NM3 generation-3 self-play (README "NM3 第 3 代：自对弈开下"; the user confirmed in this session 10-23): both sides the
# NM3 gen-2 bot (7f1d5fb specs; elf-t N 88, nemesis-t N 75, the same-deck N). Training 83300000 + 2k (k 0-9), then
# holdout 83400000 + 2h (h 0-4). A seed in $S/nm3g3/SKIP is not played here; stops before the next shard when
# $S/nm3g3/PAUSE exists. Code 7f1d5fb.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
ELF="mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1"
NEM="mcts:75+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1"
for job in "83300000 0" "83300000 1" "83300000 2" "83300000 3" "83300000 4" "83300000 5" "83300000 6" "83300000 7" "83300000 8" "83300000 9" "83400000 0" "83400000 1" "83400000 2" "83400000 3" "83400000 4"; do
  set -- $job
  seed=$(($1 + 2*$2))
  [ -e $S/nm3g3/rec/rec-$seed.jsonl.gz ] && continue
  if [ -e $S/nm3g3/PAUSE ]; then echo "paused before $seed"; exit 0; fi
  if grep -qx "$seed" $S/nm3g3/SKIP 2>/dev/null; then echo "skip $seed (another line)"; continue; fi
  python3 -m svsim.learn.scaledata play --deck elf-t --opponent nemesis-t --spec "$ELF" --opponent-spec "$NEM" --base $1 --stride 2 --shards $2 $(($2 + 1)) --per-shard 1000 --workers 3 --out $S/nm3g3/rec || { echo "FAILED $1 $2"; exit 1; }
  echo "done $seed at $(date -u +%H:%M:%S)"
done
echo DONE
