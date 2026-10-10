# Wall clock per decision: before the speed rounds and now (for Salem's decision on the levels)

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task** (the architecture thread 2026-10-10 14:36Z): the code before speed round 3 (3e9a331, the version Salem's
machine runs) against 0e038cb (after rounds 3, 4 and 6).
- What is reported: each level's ms per decision, and the N at 0e038cb that takes the same wall clock as the old
  level.
- **Whether the levels change is Salem's own decision.** Nothing here changes them.

**Method** (`wallclock.py`; data/wallclock/):
- The whole agent's move (lethal check included) at the first move of bench.py's 28 step-1 starts, the same seed per
  position.
- Specs in alternating order within a run. Old and new runs alternate as separate processes. The median of the
  rounds' means.
- Old: 6 rounds per spec. New: 4 rounds at N 200 / 300 / 1043 / 1600, plus 2 at the fitted N.
- This container's 4 cores, one thread. Single rounds vary by about ±10%.

| model | level | old (3e9a331) ms | 0e038cb at the same N | ratio | N at 0e038cb for the old wall clock |
|---|---|---|---|---|---|
| installed | strong, mcts:200 | 139.7 | 105.8 | 0.76 | **≈ 300** (fit; 292 measured 134.9 ms) |
| installed | strongest, mcts:1043 | 603.2 | 426.2 | 0.71 | **≈ 1460** (fit; 1506 measured 647 ms) |
| cand-kc | strong, mcts:200 | 145.7 | 119.1 | 0.82 | **≈ 280** (fit; 315 measured 168 ms) |
| cand-kc | strongest, mcts:1043 | 633.0 | 437.0 | 0.69 | **≈ 1450** (fit; 1455 measured 635 ms) |

- The N are least-squares lines through all the new points of each level and model. They carry the noise above:
  about ±10% on N.
- Iterations per decision at N 200 are 185.7. Some decisions end early: the lethal agent plays the move, or the
  search stops on a settled root. At 1043 they are 968.5.
- The ratio is lower for the strongest level: the fixed part of a decision (the lethal check) weighs less there.
