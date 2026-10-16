# Generation 4 extra games (72300000 + 2k, 500 games a shard)

These games are part of the 2×10⁴ extra gen-4 games (the architecture thread 16:23Z; seed table in the analysis line's
2b28ddf). The player is `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-gen3-30000.npz+neteot`
(net-gen3-30000 sha256 64e17c13…) on both sides, ramp-t mirror, code 69e3ad2. The games were played in a 69e3ad2 worktree.
Before the first shard, gen 4 k = 0's games g = 0 and 1 were played again in that worktree. Every field matched the
analysis line's records apart from date and cpu.

| k | seed | file | games |
|---|---|---|---|
| 0 | 72300000 | rec-72300000.jsonl.gz | 500 (g 0–499) |
| 1 | 72300002 | rec-72300002.jsonl.gz | 500 (g 0–499) |
| 2 | 72300004 | rec-72300004.jsonl.gz | 500 (g 0–499) |
| 3 | 72300006 | rec-72300006.jsonl.gz | 500 (g 0–499) |
| 4 | 72300008 | rec-72300008.part.jsonl | **306 (g 0–305)**, stopped at the 2-hour limit |
| 5 | 72300010 | rec-72300010.jsonl.gz | 500 (g 0–499) |
| 6 | 72300012 | rec-72300012.jsonl.gz | 500 (g 0–499) |
| 7 | 72300014 | rec-72300014.jsonl.gz | 500 (g 0–499) |
| 8 | 72300016 | rec-72300016.jsonl.gz | 500 (g 0–499) |

Shard k = 4 is handed to the analysis line. It finishes g = 306–499 from this part file with the same command:
`scaledata play --base 72300000 --stride 2 --shards 4 5 --per-shard 500 --out <dir containing this file>`. The builder
line does not play k = 4 again, so every game has exactly one source. The part file has no cut-off line, and its g values
are unique and consecutive. No game is a draw. Every agent seed is s×1000 + 2g + i.

Condition: the opponent's deck list is known (order and hand not).
