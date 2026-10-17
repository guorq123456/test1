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
| 13 | 72800026 | 500 (g 0–499) | builder line |
| 14 | 72800028 | 500 (g 0–499) | builder line |
| 15 | 72800030 | 500 (g 0–499) | builder line |
| 16 | 72800032 | 500 (g 0–499) | builder line |
| 17 | 72800034 | 500 (g 0–499) | builder line |
| 0–9 | 72800000 … 72800018 | 500 each | the analysis line (its 6b51f35) |
| 18 | 72800036 | 500 (g 0–499) | builder line |
| **19** | **72800038** | 500 (g 0–499); g 0–82 before a container restart, g 83–499 resumed | builder line; **holdout** |

Each shard was checked: g 0–499 each once, deal seed s×100003 + g, agent seeds s×1000 + 2g + i, no draw, and one
player string, elf-t on both sides.

**All 20 shards, merged (2026-10-17 05:0xZ).** The analysis line's 10 files matched its SHA256SUMS. They were
copied here, and SHA256SUMS was regenerated over all 20 files. Every shard was checked again: g 0–499 each once, both
seeds right, one player string, elf-t on both sides, explore 0, no draw. Each shard has exactly one source. In total
there are 10000 games; the first player won 65.0%. Training uses k = 0–18; k = 19 is the holdout.

**k = 19's resume.** A container restart stopped the shard after g = 82. The same command resumed it from its part
file, game by game. Seeds and game numbers run on across the boundary. Games 82 and 83 (the last before the restart
and the first after it) were played again outside the pool. After the JSON round trip, both match their stored records
field for field, apart from date and cpu.

Condition: the opponent's deck list is known (order and hand not).
