# +xprune: discard choices pruned by a cross-turn judgment (pre-gate prototype; off by default)

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task:** the architecture thread 2026-10-10 16:57Z, from Salem's direction:
「克，算力不够我认为可以根据算法解决而不是应搜，比如754弃牌，看起来选择空间很大但用跨回合算法判断哪些牌在接下来的对局里价值不够高，哪些牌价值在近几回合一定不会出——判断空间基本就会少非常多了」

## What it does (`svsim/search/xprune.py`; spec flag `+xprune` or `+xprune=M:H:ORDER`)

- **Only discard choices are touched.**
  - A discard choice is a play, evolve or engage whose targets include hand cards that its resolution discards
    (`core.effects.discard`).
  - That is found once per card and action kind, by resolving the action on a copy. There is no card list.
- **What the search keeps:** only the discard choices of the M most discardable hand cards (M + K − 1 for a choice
  of K cards, e.g. Lumiore & Argente's pairs). This holds at every node of its own turn. The other moves are
  untouched.
- **How discardable a card is,** computed from costs, the play-point curve and the position (no fixed value per
  card):
  1. **Discarding it gains something:** it has a "when discarded" ability. Vorlalai summons itself. This always
     comes first.
  2. **It won't come out soon:** the turn in which the hand would play it, if each turn plays the most play points'
     worth of the hand.
     - Budgets: this turn, what is left after the discarding card (plus the Bonus Play Point if unused); turn t,
       min(10, max PP + t).
     - Current costs, reductions included. Not played within H turns (3) counts as H + 1.
     - Cards drawn meanwhile are unknown and not counted.
  3. **It is worth less later:** the lower cost.
  - ORDER combines 2 and 3:
    - `when`: 2, then 3. The first version and the code default.
    - `cost`: 3, then 2.
    - `value`: cost × 0.8^turns until played (0 if not within H), then 2.
- **No peeking:** only the player's own visible cards and play points are read, so every determinization of a
  decision gets the same answer (the root cache holds).
- **Off by default:** without the flag the module isn't even imported.
  - golden (`tests/test_golden_search.py`): 5 passed.
  - cmp_roots (116 roots, level-strong whole agent): `116 142cc5676ed8bef092a604ab0068e383cb66eb4928c6e3ec14e9eb1c062b9adf`,
    unchanged.

## Results

### Puzzles 2 and 3, 8 seeds each (`python -m svsim.tools.puzzles --seeds 1,…,8 --only …`)

| spec | puzzle 2 (k 518) | puzzle 3 (k 445) |
|---|---|---|
| mcts:200+plan+learned+phased (level-strong) | 0/8 | 0/8 |
| **mcts:200 + `+xprune` (m 2, when)** | **8/8** | **8/8** |
| mcts:200 + `+xprune=3:3:cost` | 8/8 | 8/8 |
| mcts:200 + `=2:3:cost` / `=2:3:value` / `=3:3:when` / `=3:3:value` | 8/8 each | 8/8 each |
| mcts:1043+plan+learned+phased | 8/8 | 8/8 |

**J78 is right:** strong + `+xprune` solves at least one puzzle 6/8 or more; it solves both 8/8.

**Root moves:**

| setting | puzzle 2 | puzzle 3 |
|---|---|---|
| m 2 | 56 → 20 | 15 → 10 |
| m 3 | 56 → 26 | 15 → 14 |

**Salem's discard is never cut:** Spilling Red discarding Vorlalai is kept in both puzzles, under every setting.
- Puzzle 3, m 2: the bot's line (Lumiore & Argente discarding Erntz and Sloth) is cut.
- Puzzle 2, m 2: Spilling Red may discard Vorlalai or Kimika (4 targets each); the 7 other cards are cut.

### Safety (`xp_safety.py`, data/safety.json)

The rate that counts: among decisions where the setting cuts something and the chosen move is itself a discard
choice, the share whose chosen discard is cut.

| setting | mcts:1043, 28 starts + bank (report) | Salem's own discards, 47 games (development) |
|---|---|---|
| m 2 when (code default) | 12 / 30 = **40%** | 29 / 92 = 32% |
| m 2 cost | 12 / 30 = 40% | 29 / 92 = 32% |
| m 2 value | 11 / 30 = 37% | 26 / 92 = 28% |
| m 3 when | 10 / 26 = 38% | 17 / 89 = 19% |
| **m 3 cost** | **7 / 26 = 27%** | **11 / 89 = 12%** |
| m 3 value | 9 / 26 = 35% | 10 / 89 = 11% |

- **mcts:1043 decisions:**
  - 64 decisions in its own turns had a discard choice among the legal moves; at 33 of them it chose a discard.
  - Counted over every decision the pruning touched (non-discard choices are never cut), m 2 when cuts 1043's move
    at 12 of 57 = 21%; m 3 cost at 7 of 50 = 14%.
  - Mean moves at those decisions: 18.7 → 9.0 (m 2), 20.4 → 12.2 (m 3).
- **How the setting was chosen:**
  - "when" was the only order when the first safety run was read (40% / 32%).
  - The other orders and m 3 were then tried on Salem's discards first (the development set). There m 3 value
    (11.2%) and m 3 cost (12.4%) tie within one decision; cost is the simpler rule.
  - The 1043 numbers for all six came out of the same later run. So they are not an untouched check of cost against
    value.
- **What the cut 1043 discards look like:**
  - 1043 sometimes discards a big card that would come out soon, e.g. Normagdala (7) with Sagatsumatsu at 10 play
    points in ramp-lyria-crest, all 3 seeds.
  - Salem does the opposite: he discards cheap cards that have done their job (Roar of Prominence, Dragonsign,
    Dragonewt Promoter, Lyria).
  - The rule follows Salem's habit. Which of the two is right is for the gate to show.

### Cost (`xp_cost.py`, data/cost.json)

Whole agent, ms per decision, mcts:200+plan+learned+phased with and without `+xprune=3:3:cost`. Turns played to their
end, alternating, median of 3 rounds, one process; another job was running on the machine, so the ratios are what
count.

| positions | without | with | ratio |
|---|---|---|---|
| step 1's 28 starts (96 / 99 decisions) | 62.4 | 66.5 | **1.066** |
| puzzles 2 and 3, seeds 1–8 (80 decisions) | 111.4 | 128.9 | 1.157 |

- The cost comes from working out the kept cards at the nodes where a discard choice is legal. It is cached per
  hand, play points and discarding card.
- At equal compute, strong's N would be about 200 / 1.07 ≈ 188. The gate's own ms check sets it.

## For the gate (the analysis line pre-registers it)

- Suggested candidate: `level-strong+xprune=3:3:cost`, i.e. `mcts:N+plan+learned+phased+xprune=3:3:cost` with N
  matched to level-strong's compute. Code default `+xprune` (m 2 when) as the first version, if wanted.
- Nothing is installed and no level changed. That stays Salem's decision.
