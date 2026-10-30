#!/bin/bash
# usage: train.sh start|fresh|prior-elf|prior-nem   (NM3 generation 3: gen 1 + 2 + 3, 30 shards; as gen 2: two value-net
# arms, valid split key, the arm rule of the architecture thread 2026-10-20 01:23Z; priors continued from gen 2's)
N=/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/scale/nm3g3
cd /home/user/test1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
SH=""
for b in 79100000 80500000 83300000; do for k in 0 1 2 3 4 5 6 7 8 9; do SH="$SH $((b + 2 * k))"; done; done
HOLD=""
for b in 79200000 80600000 83400000; do for h in 0 1 2 3 4; do HOLD="$HOLD $((b + 2 * h))"; done; done
case $1 in
  start|fresh)
    if [ $1 = start ]; then X="--init analysis/scaling/models/net-nm3g2f-elf-nem.npz --extend-cards --name nm3g3-elf-nem"
    else X="--fresh --name nm3g3f-elf-nem"; fi
    python analysis/scaling/train_mid.py --deck elf-t --opponent nemesis-t --pairs elf-t:nemesis-t nemesis-t:elf-t --split key \
      --tokens $N/all/tok --end 79100000:10 --end 80500000:10 --end 83300000:10 \
      --mid-dir $N/all/mid --mid 79100000:10 --mid 80500000:10 --mid 83300000:10 \
      --holdout $HOLD --epochs 60 --patience 4 --checkpoint $N/ckpt-$1.npz $X >> $N/train-$1.log 2>&1 ;;
  prior-elf)
    python -m svsim.learn.setpolicy fit --data $N/all/dec-elf-t --cards $N/all/tok/cards.npz --shards $SH \
      --prior analysis/scaling/models/prior-nm3g2-elf-t.npz --extend-cards --deck elf-t --opponent nemesis-t \
      --tau 0.5 --ftz --split key --checkpoint $N/ckpt-prior-elf.npz \
      --out analysis/scaling/models/prior-nm3g3-elf-t.npz >> $N/train-$1.log 2>&1 ;;
  prior-nem)
    python -m svsim.learn.setpolicy fit --data $N/all/dec-nemesis-t --cards $N/all/tok/cards.npz --shards $SH \
      --prior analysis/scaling/models/prior-nm3g2-nemesis-t.npz --extend-cards --deck nemesis-t --opponent elf-t \
      --tau 0.5 --ftz --split key --checkpoint $N/ckpt-prior-nem.npz \
      --out analysis/scaling/models/prior-nm3g3-nemesis-t.npz >> $N/train-$1.log 2>&1 ;;
esac
echo EXIT $?
