# DFM rune hero: a move prior on top of the g3 value net (the architecture thread 2026-11-01 12:2xZ, before any game)

Condition: 对手卡表已知（牌序、手牌未知）. EXTERNAL list, isolated, measurement only (Salem 「隔离训练」).

## Where the value-net generations stand (equal CPU, 300 pairs each)

| gen | bank | X | baseline | paired |
|---|---|---|---|---|
| g1 | 85997000 | 7.8 | 6.5 | +1.3 ± 2.9 (N 58, ratio 1.157) |
| g2 | 85999000 | 10.8 | 4.5 | +6.3 ± 2.8 |
| g3 | 86026000 | 25.2 | 7.3 | +17.8 ± 4.0 |
| g3 | 86028000 | 23.5 | 5.3 | +18.2 ± 3.9 |
| g4 | 86028000 | 20.5 | 5.3 | +15.2 ± 3.7; g4 − g3 on the same deals −3.0 ± 3.8 |

Gen 4 added nothing: the value net alone has levelled off near 24% against the bot's six other decks. Salem's four
positions: g3 passes 3 of 4 (mid-turn branch); 锅 before 光 still fails.

## The lever

The precedent's next step after the value net was a move prior with PUCT at every node (analysis/scaling/README.md
section B; installed as `+puct=prior-*-ft-t05.npz:2:1`). For 三轴土 the search spends 50-60 iterations on turns of
eight to ten ordered steps; a prior learned from the net-guided search's own visits lets those iterations go to the
orders that matter.

- Data: the hero's decisions (`setpolicy encode --deck dfm/RUNE-ユーリ`) in the g3 and g4 self-play records
  (86025000 and 86027000, 20 shards; both net-guided).
- Fit: `setpolicy fit --init net-pilot-rune-dfm-g3 --tau 0.5 --ftz` (trunk fine-tuned, the precedent's ft-t05) ->
  prior-pilot-rune-dfm-ft-t05.
- Arm: X = mcts:N+plan+setnet=net-pilot-rune-dfm-g3+netmid+netany+puct=prior-pilot-rune-dfm-ft-t05.npz:2:1, N
  time-matched once on 86028900 against mcts:100+plan, then an equal-CPU gate on 86028000 (the same deals as the g3
  and g4 rows above), so X can be paired with g3 directly.

## Predictions (before any game)

- The prior arm beats g3 on the same deals by at least +3 points: 0.4.
- It passes 锅 before 光 (Salem's position 2) with the prior's own ranking (prior P(锅) > P(光) at that position): 0.45.

The bot rune hero gets the same step only if this one gains (its gen 4 is running first).
