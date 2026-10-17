# elf-t mirror, generation 3 self-play (74100000 + 2k, 500 games a shard)

This is the elf-t mirror's third generation. The architecture thread asked for it after J120 (elft-gen2 against
elft-10000, 56.2%), and the analysis line registered the seeds. The player is
`mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-elft-gen2-19500.npz+neteot`
(net-elft-gen2-19500, sha256 e244c577…) on both sides, elf-t vs elf-t, code d884a3c, played in a d884a3c worktree.

The analysis line plays k = 0–9; the builder line plays k = 10–19. **k = 19 (74100038) is the gen-3 self-play
holdout and goes into no training.** Before each batch was started, the analysis line's branch was checked to make
sure it had not pushed those shards.

| k | seed | games | played by |
|---|---|---|---|
| 10 | 74100020 | 500 (g 0–499) | builder line |
| 11 | 74100022 | 500 (g 0–499) | builder line |
| 12 | 74100024 | 500 (g 0–499) | builder line |

Each shard was checked: g 0–499 each once, deal seed s×100003 + g, agent seeds s×1000 + 2g + i, no draw, explore 0,
one player string, elf-t on both sides. The first player won 65.8% / 61.2% / 66.6% of the games.

Condition: the opponent's deck list is known (order and hand not).
