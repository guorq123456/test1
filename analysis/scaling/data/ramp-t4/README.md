# ramp-t PUCT self-play (the next cycle, README 45212fb)

Condition: the opponent's deck list is known (order and hand not).

- Agent on both sides, explore 0: `mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-gen3-30000.npz+neteot+puct=analysis/scaling/models/prior-ramp-ft-t05.npz:2:1`
- `scaledata play --base 75400000 --stride 2 --per-shard 500`, shard k at 75400000 + 2k, deal seed s x 100003 + g, agent seeds s x 1000 + 2g + i; code 72a5148.
- k = 19 (75400038) is this cycle's holdout, not for training.
- Who played: the analysis line k = 0-16 (75400000 ... 75400032); the builder line k = 17-19 (75400034 / 36 / 38).
  k = 15 was stopped at 380 games and resumed (scaledata play drops a cut-off last line and plays it again).
- Checked here (analysis/gates/scaling/btier/shardcheck.py): every shard g 0-499 once, both seeds, one agent string, ramp-t on both sides, explore 0, no draws.
- Cross-machine: 75400000 g 0-2 identical records on both machines (cfcc081).
- This SHA256SUMS covers the analysis line's 17 shards; it is recomputed over all 20 when the builder's 3 are merged.
- The analysis line's 17 shards: 8500 games, first player wins 60.2%.
