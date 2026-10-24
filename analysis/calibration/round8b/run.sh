#!/bin/bash
# CR calibration round 8b (analysis/ramp-benchmark/README.md "第 8b 轮"): the two NM3 cells with the gen-3 bot.
# A = gen-3 explicit spec at the gate N (88 / 75), B = C = ruler20261008, --versus; code ac238cd; 3 workers.
# Usage: run.sh elf | nem   (one cell per background job)
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/calibration/round8b
cd $S/wt_nm3g3gate
export PYTHONPATH=$S/wt_nm3g3gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
cell() {  # deck opponent spec seed
  python3 -m svsim.tools.host svsim.tools.gate --a "$3" --b ruler20261008 --versus ruler20261008 --deck $1 --opponent $2 --fixed --workers 3 --max 600 --seed $4 --out $OUT/$1_vs_$2.jsonl > $OUT/log_$1_vs_$2.txt 2>&1 || { echo "$1_vs_$2 FAILED"; exit 1; }
  echo "$1_vs_$2 done at $(date -u +%H:%M:%S)"
}
case $1 in
  elf) cell elf-t nemesis-t "mcts:88+$P+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+puct=$M/prior-nm3g3-elf-t.npz:2:1" 84600000 ;;
  nem) cell nemesis-t elf-t "mcts:75+$P+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+puct=$M/prior-nm3g3-nemesis-t.npz:2:1" 84700000 ;;
esac
