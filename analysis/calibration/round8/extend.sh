#!/bin/bash
# Round 8 extension (README "补登记"): the 6 non-mirror cells get pairs 100-149 from the same bank (--seed bank+100,
# --max 200) into *_ext.jsonl; merged into the cell file afterwards. Same specs and code as run.sh.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/calibration/round8
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
ext() {  # deck opponent spec bank
  [ -e $OUT/$1_vs_$2_ext.jsonl ] && [ "$(wc -l < $OUT/$1_vs_$2_ext.jsonl)" -ge 50 ] && { echo "have $1_vs_$2_ext"; return; }
  python3 -m svsim.tools.host svsim.tools.gate --a "$3" --b ruler20261008 --versus ruler20261008 --deck $1 --opponent $2 --fixed --workers 3 --max 200 --seed $(($4 + 100)) --out $OUT/$1_vs_$2_ext.jsonl > $OUT/log_$1_vs_$2_ext.txt 2>&1 || { echo "$1_vs_$2_ext FAILED"; exit 1; }
  echo "$1_vs_$2_ext done at $(date -u +%H:%M:%S)"
}
ext ramp-t elf-t "mcts:89+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-ramp-t.npz:2:1" 83800000
ext ramp-t nemesis-t "mcts:85+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-ramp-t.npz:2:1" 83900000
ext elf-t ramp-t "mcts:95+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-elf-t.npz:2:1" 84000000
ext elf-t nemesis-t "mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1" 84100000
ext nemesis-t ramp-t "mcts:80+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-nemesis-t.npz:2:1" 84200000
ext nemesis-t elf-t "mcts:75+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1" 84300000
echo "EXT DONE at $(date -u +%H:%M:%S)"
