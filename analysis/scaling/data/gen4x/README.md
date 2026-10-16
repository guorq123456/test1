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
| 9 | 72300018 | rec-72300018.jsonl.gz | 500 (g 0–499) |
| 10 | 72300020 | rec-72300020.jsonl.gz | 500 (g 0–499) |
| 11 | 72300022 | rec-72300022.jsonl.gz | 500 (g 0–499); g 0–134 before a container restart, g 135–499 resumed |
| 12 | 72300024 | rec-72300024.jsonl.gz | 500 (g 0–499), all after the restart |
| 13 | 72300026 | rec-72300026.jsonl.gz | 500 (g 0–499); g 0–118 before the restart, g 119–499 resumed |
| 14 | 72300028 | rec-72300028.jsonl.gz | 500 (g 0–499) |
| 15 | 72300030 | rec-72300030.jsonl.gz | 500 (g 0–499) |
| 16 | 72300032 | rec-72300032.jsonl.gz | 500 (g 0–499) |
| 17 | 72300034 | rec-72300034.jsonl.gz | 500 (g 0–499) |
| 18 | 72300036 | rec-72300036.jsonl.gz | 500 (g 0–499) |
| 19 | 72300038 | rec-72300038.jsonl.gz | 500 (g 0–499) |

k = 20–27 and 28–39 are the analysis line's (its branch, same directory name); k = 4 was finished there too.

Shard k = 4 is handed to the analysis line. It finishes g = 306–499 from this part file with the same command:
`scaledata play --base 72300000 --stride 2 --shards 4 5 --per-shard 500 --out <dir containing this file>`. The builder
line does not play k = 4 again, so every game has exactly one source. The part file has no cut-off line, and its g values
are unique and consecutive. No game is a draw. Every agent seed is s×1000 + 2g + i.

**Resume after the container restart (20:17Z, k = 11–13).** The play command was run again on the same part files. It
resumes game by game: games already played are kept and are not played again. The boundary check, as the architecture
thread asked (17:24Z), found the following. Every shard has g 0–499, each g exactly once. Every deal seed is s×100003 + g
and every agent seed is s×1000 + 2g + i. Games g = 134 and 135 of k = 11 (the last game before the restart and the first
after it) were played again outside the pool. After the JSON round trip, each matched its stored record field for field,
apart from date and cpu.

Condition: the opponent's deck list is known (order and hand not).
