# Fifth new deck: 实验体法 (exp-t, post-patch witch), meta thread's suggestion 2026-10-08 05:46Z. Same settings as run.sh.
O=${OUT:-/tmp/claude-0/sp}; s=20261213
for o in ramp-t elf-t pirate-t; do s=$((s+1)); [ -s $O/exp-t_${o}.jsonl.gz ] && continue
python3 -m svsim.learn.netdata --games 1000 --deck exp-t --opponent $o --agent v2 --explore 0.03 --workers 4 --seed $s --out $O/exp-t_${o}.jsonl && gzip -f $O/exp-t_${o}.jsonl
done
