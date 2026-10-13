# Speed round 2 + 最强 level, checked on Salem's Windows machine (old c5413b3 vs new b215e3d)

Condition: 对手卡表已知（牌序、手牌未知）. Python 3.12.10, `_INLINE` True. Every run went through `python -m svsim.tools.host`
(below normal, mask 0xffffe, 19 CPUs), one process at a time. Step 1 data is RC 6f11111; analysis scripts are 552156e.

## 1. Behaviour (all identical)

- cmp_roots, 116 roots: `755a0bba6cfb1119729e19b4af0484d6a583854d678b1697cd91fb39f63596a6` in all four runs:
  - old
  - new
  - new with SVSIM_COW_CHECK=1
  - the merge a7fc7ff (cmp_roots_merged_a7fc7ff.txt)
- golden_hash: old, new, and new with SVSIM_COW_CHECK=1 all match the 8bb28a8 Windows values. The copy-on-write
  guard never fired.
- tests/test_lethal_same.py (SVSIM_STEP1_DIR set) + test_enums.py + test_cow.py: 11 passed.
- Full suite: 1121 passed, 5 skipped, 4 failed.
  - The 4 failures are test_golden_search's Linux record, the same games that fail on the old code (8bb28a8).
  - The skips are official card data (3), handvalue, and test_host needing Linux affinity.

## 2. Speed (bench.py STEP1 30 3; alternated, 3 runs each)

| | old c5413b3 | new b215e3d | |
|---|---|---|---|
| iterations per second, median of 9 rounds | 2280.0 | 2446.2 | ×1.07 |
| ms per decision, median of 9 rounds | 132.9 | 110.7 | −16.7% |

## 3. Per-turn cost on the new code (turn_cost, the same 60 starts; turn_cost_new_rerun.txt)

- `level-max`：每回合 1099 ms（中位 1019）；换了打法的回合 0/60
- `level-strong`：每回合 238 ms（中位 221）；A ÷ 它 = 4.627

On c5413b3 these were 1204 ms (mcts:1043) and 279 ms (level-strong).

The first run (turn_cost_new.txt) is not valid: one level-max turn took 16 820 s, so the machine was probably
asleep during it. Its median was 981 ms.
