#!/bin/bash
# CR calibration round 8 (analysis/ramp-benchmark/README.md "第 8 轮改登记"): the 8 cells the strong tier installs.
# A = the new bot's explicit spec at the gate N, B = C = ruler20261008, --versus; code 7f1d5fb; 3 workers.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/calibration/round8
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
cell() {  # deck opponent spec seed max
  [ -e $OUT/$1_vs_$2.jsonl ] && [ "$(wc -l < $OUT/$1_vs_$2.jsonl)" -ge $(($5 / 4)) ] && { echo "have $1_vs_$2"; return; }
  python3 -m svsim.tools.host svsim.tools.gate --a "$3" --b ruler20261008 --versus ruler20261008 --deck $1 --opponent $2 --fixed --workers 3 --max $5 --seed $4 --out $OUT/$1_vs_$2.jsonl > $OUT/log_$1_vs_$2.txt 2>&1 || { echo "$1_vs_$2 FAILED"; exit 1; }
  echo "$1_vs_$2 done at $(date -u +%H:%M:%S)"
}
cell ramp-t ramp-t "mcts:83+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1" 83100000 600
cell elf-t elf-t "mcts:73+$P+setnet=$M/net-mid-elf-t.npz+netmid+puct=$M/prior-elft-ft-t05.npz:2:1" 83200000 600
cell ramp-t elf-t "mcts:89+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-ramp-t.npz:2:1" 83800000 400
cell ramp-t nemesis-t "mcts:85+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-ramp-t.npz:2:1" 83900000 400
cell elf-t ramp-t "mcts:95+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-elf-t.npz:2:1" 84000000 400
cell elf-t nemesis-t "mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1" 84100000 400
cell nemesis-t ramp-t "mcts:80+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-nemesis-t.npz:2:1" 84200000 400
cell nemesis-t elf-t "mcts:75+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1" 84300000 400
PYTHONPATH=. python3 /home/user/test1/analysis/ramp-benchmark/calibrate.py $OUT --ref 20bcfbe > /home/user/test1/analysis/calibration/round8_report.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
