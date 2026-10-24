# R1: ft-t05's ramp-t decisions searched again by A's scorer (registered by the analysis line, 96c5b24, "R1")

The shards are gen4x, 72300000 + 2k for k = 0–39: the records ft-t05 was trained on. The decisions are those of
learn.setpolicy.decisions. A decision (s, g, i) is kept when crc32("r1-ramp-keep/s/g/i") is even, which keeps about
half. It is searched by a fresh agent, seeded crc32("r1-ramp-seed/s/g/i"), of
`mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-mid-ramp-t.npz+netmid`.
That is A's scorer with no prior: UCB1 with c 0.5, N 200.

Both lines ran the analysis line's analysis/gates/scaling/r1/relabel.py (sha256 11f7da6e…ac49), unchanged, in a
checkout of fbb3c21. In the output, a kept and searched decision has `search[i] = {"visits": new, "visits0": as
recorded}`; every other step is None. Each shard has a .stats.json.

| k | by | decisions | kept | searched | played without a search | unmatched keys |
|---|---|---|---|---|---|---|
| 0–25, 36–39 (30 shards) | builder line, 3–4 workers | 700042 | 349992 | 348973 | 1019 | 0 |
| 26–35 (10 shards) | analysis line (df7c482) | 235661 | 117810 | 117508 | 302 | 0 |

SHA256SUMS-builder covers the builder's 30 shards. SHA256SUMS-analysis is the analysis line's, for its 10 shards.

Condition: the opponent's deck list is known (order and hand not).
