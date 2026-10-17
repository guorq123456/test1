# elf-t mirror, generation 2 self-play (72800000 + 2k, 500 games a shard)

This is the elf-t mirror's second generation (the architecture thread 2026-10-17 00:00Z; seed table in the analysis
line's 87e9232). The player is `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-elft-10000.npz+neteot`
(net-elft-10000 sha256 3278ad1a…) on both sides, elf-t vs elf-t, code 69e3ad2, played in a 69e3ad2 worktree.

The analysis line plays k = 0–9; the builder line plays k = 10–19. **k = 19 (72800038) is the elf-t self-play holdout
and goes into no training.** Before each shard was started, the other line's branch was checked to make sure it had
not pushed that shard.

| k | seed | games | played by |
|---|---|---|---|
| 10 | 72800020 | 500 (g 0–499) | builder line |
| 11 | 72800022 | 500 (g 0–499) | builder line |
| 12 | 72800024 | 500 (g 0–499) | builder line |

Each shard was checked: g 0–499 each once, deal seed s×100003 + g, agent seeds s×1000 + 2g + i, no draw, and one
player string, elf-t on both sides.

Condition: the opponent's deck list is known (order and hand not).
