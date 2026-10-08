#!/bin/sh
# Self-play for the leave-one-deck-out test: the four new tournament decks (bishop-t, nm-t, crystal-t,
# synergy-t; medoid lists, svsim/cards/decks.py) against three of the core decks, v2 at the 100 level,
# 3% random moves, 1000 games each. Records as learn.netdata writes them (gzip after).
O=${OUT:-/tmp/claude-0/sp}
mkdir -p $O
s=20261201
for d in bishop-t nm-t crystal-t synergy-t; do
  for o in ramp-t elf-t pirate-t; do
    s=$((s+1))
    [ -s $O/${d}_${o}.jsonl.gz ] && continue
    python3 -m svsim.learn.netdata --games 1000 --deck $d --opponent $o --agent v2 --explore 0.03 --workers 4 --seed $s --out $O/${d}_${o}.jsonl && gzip -f $O/${d}_${o}.jsonl
  done
done
