# Faster engine and search with behaviour unchanged

Assigned by the architecture thread 2026-10-10 01:18Z: same-seed play and every root's visit counts must stay
bit-identical. Behaviour is unchanged, so no gate. Condition: 对手卡表已知（牌序、手牌未知）.

## Result (this container, one process, one thread; alternating runs of the old and new code)

`bench.py` runs level-strong's search (`mcts:200+plan+learned+phased`) on the first move at the first 30 training
starts of step 1 (RC 6f11111; 28 have more than one legal action). Three alternating rounds of old (cefd7c1) and
new code:

| | before (cefd7c1) | after | |
|---|---|---|---|
| iterations per second (ISMCTS.choose) | 1481 / 1458 / 1425 (median 1458) | 2029 / 2007 / 2078 (median 2029) | ×1.39 |
| ms per decision (whole agent, lethal search included) | 191.5 / 192.7 / 201.1 (median 192.7) | 144.8 / 145.3 / 135.3 (median 144.8) | −25% |

## Behaviour unchanged: how it was checked

- **tests/test_golden_search.py** (new): five fixed-seed games covering the original Ramp mirror, the ramp-t
  mirror, the elf-t mirror, elf-t vs ramp-t and nemesis-t vs pirate-t, 250 decisions in all, at mcts:30. The
  record holds every decision's action, iterations, and root children (key, visits, value as repr, bit for bit).
  It was frozen before any change (cefd7c1) and still matches after every change, also under another
  PYTHONHASHSEED.
- **cmp_roots.py**: level-strong at 200 iterations on 116 step-1 starts, whole agent. The sha256 of all actions and
  root statistics is the same for old and new code: 142cc567…2b9adf.
- **Full test suite**: 1118 passed, 1 skipped.
  - Two new test files: tests/test_enums.py checks the keyword table and the shuffle;
    tests/test_golden_search.py is the record above.

## The changes (from the profile, cProfile on bench.py)

Before, the 25 s profiled went to: state copying 5.4 s (1.28 million card copies, 2.7 s); legal actions 4.7 s (the
Python 3.11 IntFlag `&` 1.2 s); features 4.3 s; determinize 4.1 s; lethal search 4.6 s.

1. `GameState.clone`: the generator is made with `Random.__new__`, not `random.Random()`, which first seeds itself
   from the OS. `determinize` uses `clone(copy_rng=False)`, because it reseeds the copy at once.
2. `PlayerState.copy` copies field by field, as CardInstance already did (`copy.copy` went through `__reduce_ex__`).
   `CardInstance.copy` assigns each field once.
3. `Keyword` `&` and `|` use a table of all 512 combinations. They return the same members IntFlag's own operators
   return, checked over every pair in tests/test_enums.py.
4. `features._roles_sum` is unrolled, with the additions in the same order: the same floats on any Python version.
5. `determinize` writes out `random.shuffle` around `getrandbits`: the same draws and the same permutation.
   - At import it checks itself against this Python's own shuffle and falls back to the library's if they differ,
     so a newer Python can't change the play.
6. `PhasedLearned.score`: with two named decks, the model is looked up once per (deck, deck, moment). The class
   pair is no longer built for every evaluation; the order is the same as matchup_keys.
7. `effects.enqueue`: a card with no granted scripts whose own script lacks the hook returns at once.
   `engine.selectable` builds the enemy lists only for the target kinds that read them.

A rule held throughout: no float `sum()` was replaced by a hand-written loop, or the other way round. From
Python 3.12 on, `sum()` over floats is compensated, so such a swap could change the last bits there (Salem's
machine).

## Not done (where the rest of the time is)

- **Copying cards in decks**, about 17% of the search time. Sharing deck cards between clones (copy on write) would
  need a guarantee on every path that takes a card out of a deck or changes one inside it: nine places in the
  engine, plus card scripts that change costs and stats in the deck. A miss would change play without a word, so it
  stays out of a no-change round.
- **What is left is spread thin**: legal actions, the features' remaining sums, action keys and engine resolution.
  Each is a few percent, within the noise.

## Round 2 (the architecture thread 01:40Z): lethal search, deck copy on write, the reuse measurement

The same rules: golden record bit-identical, cmp_roots hash equal, the full suite, no float `sum()` swapped, no
gate. Condition: 对手卡表已知（牌序、手牌未知）.

| alternating, this container | previous round (c5413b3) | this round | original (cefd7c1) |
|---|---|---|---|
| iterations per second | 1920 / 2056 / 2017 (median 2017) | 2112 / 2251 / 2186 (median 2186) | 1458 |
| ms per decision, whole agent | 149.6 / 148.4 / 142.2 (median 148.4) | 129.8 / 119.8 / 121.2 (median 121.2) | 192.7 |

Overall since cefd7c1: ×1.50 iterations per second, −37% time per decision. Outside ISMCTS.choose: the previous
round about 148 − 200/2017×1000 ≈ 49 ms, now about 121 − 91 ≈ 30 ms.

1. **Lethal search.** On the 116 starts, 19 of 50 s of the whole agent's profile, mostly cloning (one clone per
   action tried) and `hidden_info` (two RNG `getstate` per action).
   - No early exit or pruning: the search has node budgets (200 / 1000 / 2000), so anything that changes which
     positions are visited can change the verdict.
   - Exact changes only:
     - the hidden information before an action is the parent's, computed once per node;
     - a chance sample is cloned without copying the generator it reseeds at once;
     - the decks are reshuffled with core.view's written-out shuffle;
     - deck copy on write (2.) helps most, since the search clones constantly.
   - **tests/test_lethal_same.py**: tests/lethal_reference.py is a frozen copy of the search as of cefd7c1. Old and
     new run side by side under three settings: the agent's (2000, screen 200, near 1000/4), 400 nodes unscreened,
     and sure-only 300. They are compared on probability, line (repr), sure, nodes, completeness and screening, on
     every main-phase decision of the golden games and on the 116 starts ($SVSIM_STEP1_DIR): all equal, in both
     modes.
2. **Deck cards copied on write.**
   - `PlayerState.deck` is a property. A clone shares the deck's cards; whoever reads `deck` copies them first, so
     an unaudited site can only cost time, never change play.
   - `deck_view()` is for audited read-only code: features, evaluate, the lethal search's keys, uid sets in the
     search and the planner, `moves._evolving_matters`.
   - Exact special cases:
     - `emit` touches the deck only when a card in it listens;
     - `expire` touches it only when a card in it has grants or cost changes;
     - `_invoke` returns at once when no invoker is in the deck;
     - `draw` copies only the card it takes (`draw_top`);
     - determinize reorders the lists without copying and copies a card that goes from the deck into the hand.
   - Card copies per profiled run: 1.28 million to 0.28 million.
   - **Check mode** `SVSIM_COW_CHECK=1`:
     - every card is fingerprinted (all fields, with counters, grants and cost changes) when first shared;
     - fingerprints are verified at every clone, before a deck is copied, on every draw from a shared deck, at the
       end of every search iteration, and in a sweep after every ISMCTS decision and lethal search;
     - tests/test_cow.py checks that the guard fires on a change made through the view.
   - Results in both modes:
     - golden identical;
     - cmp_roots 142cc567…2b9adf;
     - test_lethal_same green;
     - full suite 1126 passed, 2 skipped (the skips: a pre-existing one, and the step-1 test without its data);
     - the guard never fired.
3. **Tree reuse, measurement only** (`reuse_share.py`, `reuse_share.log`).
   - Every decision starts from a fresh tree: ISMCTS.reuse is off in v2s. `+plan` is the lethal planner, not a turn
     plan, so later steps are searched like the first unless a lethal line is being played.
   - Whole turns from the 116 starts: 308 searched decisions, 2.66 a turn.
   - For a searched step k, the visits its chosen child already held, as a share of 200 (mean / median /
     quartiles):

| | n | mean | median | quartiles |
|---|---|---|---|---|
| all searched steps | 308 | 0.429 | 0.400 | 0.201 to 0.605 |
| followed by another searched decision this turn | 199 | 0.343 | 0.280 | 0.170 to 0.490 |
| ... the move reveals nothing (reusable, as ISMCTS._expect requires) | 146 | 0.363 | 0.290 | 0.180 to 0.535 |
| ... the move reveals something (a draw, randomness: not reusable) | 53 | 0.285 | 0.235 | 0.155 to 0.358 |

   By step, reusable ones: k = 0 mean 0.31 (n 62), k = 1 0.37 (38), k = 2 0.40 (25), k = 3 0.41 (16), k = 4 0.61
   (5). So reuse would hand a later decision about a third of its 200 iterations on average, at 73% of the decisions
   that follow a search. It changes play, so it isn't done here.

**What's left** (the search's profile): legal actions about 3.9 s of 17 (play_form, target sets, signatures), the
features about 2.7, engine resolution about 2.0, action keys about 1.0, sorting by rank about 0.8, card copies 0.8
(hand and field now), the two shuffles 0.65. Each is a few percent.

## Running the checks on another machine (Windows included)

From the repository root, with `D` the folder holding step 1's data (RC 6f11111's analysis/turn-level/step1, with
the analysis line's student_data.py and teacher_ends.py in `D\ana`):

```
python tests\test_lethal_same.py D                  (or: set SVSIM_STEP1_DIR=D, then python -m pytest tests\test_lethal_same.py)
python -m pytest tests\test_golden_search.py tests\test_cow.py
python analysis\speed\cmp_roots.py D                 (prints the 116 starts' hash: compare old and new code on the same machine)
set SVSIM_COW_CHECK=1                                 (check mode, read when svsim.core.state is imported; then rerun the lines above)
```

The golden record holds root values bit for bit, which depend on the Python version (3.12's compensated float
`sum`) and on the C math library (`math.exp` / `math.log` are not correctly rounded alike everywhere): it was frozen
on Linux under 3.11. On another machine compare old against new there (cmp_roots, or the golden games' own hash),
not against this record.
