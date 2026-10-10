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
