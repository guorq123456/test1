# Speed-up check on Salem's Windows machine (old cefd7c1 vs new c5413b3)

Measurement only, nothing installed. Condition: 对手卡表已知（牌序、手牌未知）. Python 3.12.10 (Windows, AMD64),
`svsim.core.view._INLINE` = True on the new code. Every run went through `python -m svsim.tools.host`
(below normal, mask 0xffffe, 19 CPUs), one process at a time, nothing else running. Step 1 data: RC 6f11111.
Analysis scripts (turn_cost, student_data): 552156e (turn_cost.py identical to 3235164).

## 1. Behaviour unchanged on Windows

- `cmp_roots.py` (116 roots): old `755a0bba6cfb1119729e19b4af0484d6a583854d678b1697cd91fb39f63596a6`,
  new the same. (Linux 142cc567…2b9adf differs: another machine.)
- `tests/test_enums.py`: passed.
- `tests/test_golden_search.py` (frozen on Linux): 4 of 5 games fail on the **new and the old code alike**, at the
  same decisions (ramp 101 #6, ramp-t 102 #6, elf-t 103 #4, elf-t/ramp-t 104 #8), and only in the last bits of root
  values (e.g. 0.58313761072133 vs 0.5831376107213299); nemesis-t/pirate-t passes. So it is the machine, not the change.
- `golden_hash.py` (here): sha256 of every decision of the five golden games, played on this machine: old and new
  identical in all five (golden_hash_old.txt / golden_hash_new.txt).

## 2. Speed (bench.py STEP1 30 3; old and new alternated, 3 runs each, 9 rounds each)

| | old cefd7c1 | new c5413b3 | |
|---|---|---|---|
| iterations per second, median of 9 rounds | 1667.0 (run medians 1651.0 / 1679.0 / 1668.0) | 2233.6 (2224.5 / 2233.6 / 2237.3) | ×1.34 |
| ms per decision, median of 9 rounds | 172.6 (176.3 / 169.3 / 172.6) | 135.2 (138.5 / 135.2 / 135.1) | −21.7% |

## 3. Per-turn cost on the new code (turn_cost, the 60 starts of split_cost, RC 11839b3)

- `mcts:200+plan+learned+phased+pickd8i200m0z1kstr`：每回合 1234 ms（中位 1097）；换了打法的回合 7/60
- `level-strong`：每回合 279 ms（中位 269）；A ÷ 它 = 4.422
- `mcts:1043+plan+learned+phased`：每回合 1204 ms（中位 1144）；A ÷ 它 = 1.025，配平的 N = round(1043 × 1.025) = 1070

Against the split measurement on the old code: level-strong 377 → 279 ms (−26%), mcts:1043 1661 → 1204 ms (−28%),
turnpick 1639 → 1234 ms (−25%).

The first speed.ps1 run stopped at the golden test failure after cmp_roots; it was rerun from the tests on
(log-speed.txt keeps both).
