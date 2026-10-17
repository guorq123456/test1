# elf-t mirror, round 4: PUCT self-play (75500000 + 2k, 500 games a shard)

This is the next cycle's elf-t self-play, registered by the analysis line in 45212fb. The player is
`mcts:71+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-elft-gen2-19500.npz+neteot+puct=analysis/scaling/models/prior-elft-ft-t05.npz:2:1`
on both sides, elf-t vs elf-t. Its value net is net-elft-gen2-19500 (sha256 e244c577…) and its prior is
prior-elft-ft-t05 (sha256 bc086c53…), with N = 71, c_puct 2, T 1 and explore 0. It was played at code 72a5148 (the
pinned commit, without cdc7b6f or 8a2c450), in a 72a5148 worktree, with 4 workers.

The builder line plays all 20 shards. The analysis line plays the ramp-t mirror (base 75400000). **k = 19 (75500038) is
the holdout and goes into no training.** Before each batch was started, the analysis line's branch was checked to make sure it had not
started elf-t shards, and the analysis line was told first.

Cross-machine check: the analysis line replayed g 0–2 of 75500000 on its machine. The records were identical except for date and cpu
(cfcc081 / 46c5b9f). The ramp-t 75400000 g 0–2 check, the other way round, is in ../xcheck.

| k | seed | games | batch |
|---|---|---|---|
| 0 | 75500000 | 500 (g 0–499) | 1 |
| 1 | 75500002 | 500 (g 0–499) | 1 |
| 2 | 75500004 | 500 (g 0–499) | 1 |
| 3 | 75500006 | 500 (g 0–499) | 1 |

Batch 1 (k = 0–3) took 2636 s for 2000 games (5.19 cpu s a game, about 2730 games an hour).

Each shard was checked for the following:
- g 0–499, each once;
- deal seed s×100003 + g;
- agent seeds s×1000 + 2g + i;
- no draws;
- explore 0;
- one player string;
- elf-t on both sides.

The first player won 67.6% / 67.6% / 65.0% / 60.6% of the games (k = 0–3).

Condition: the opponent's deck list is known (order and hand not).
