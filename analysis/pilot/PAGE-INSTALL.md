# The bot decks' pilots in the trainer (written 2026-11-08 20:0xZ, before any of its games)

**Salem, 2026-11-08 19:41Z:** 「那就帮我都装进去吧」 (install the trained pilots into the bot and the trainer; this is
also the go-ahead to publish the trainer). Measurement-only nets (names with `-dfm-`) are never installed.

Condition: 对手卡表已知（牌序、手牌未知）.

## What changes

- `ui.session.PILOT_MODELS` / `PILOTS`: when the AI plays one of the bot's own frozen decks that has a pilot (the same
  deck code as `ui/bot_decks.txt`), the normal, strong and max levels play that deck's pilot instead of the generic
  hand-set bot. fast and original stay generic. The player's own decks, and the bot decks without a pilot, are
  unchanged.
- `tools.arena.VERSIONS["pilot-<key>"]`: the pilot as the page's normal level plays it, for the gates and tools.
- `tools.web`: the build ships the pilots' nets and priors (base64 in `models-N.json`); `ratings.json` gets `pilots`.
- The page: the start screen says when the AI plays a pilot, with its gate; the bot decks with one are marked
  「专门练过」 in the opponent picker.

## Versions (each the best arm of its own line, equal CPU against mcts:100+plan, 300 pairs, field bot-frozen7)

| deck | net | prior | gated N | pilot | generic | source |
|---|---|---|---|---|---|---|
| T1-SWORD-1 皇家护卫 | g2 | from g2 | 39 | 76.7% | 67.5% | PC-PILOTS.md (F-24) |
| T1-ABYSS-1 梦魇 | g3 | from g3 | 39 | 76.5% | 58.8% | PC-PILOTS.md (abyss prior rerun) |
| T3-RUNE-1 巫师 | g5 | prior 2 | 28 | 55.5% | 27.2% | ROUND2.md |
| T1-HAVEN-1 主教 | g3 | from g3 | 35 | 64.3% | 48.8% | PRIOR-HAVEN.md |
| T1-PORTAL-1 超越者 | g3 | from g3 | 47 | 82.3% | 69.7% | PRIOR-PORTAL.md |
| T1-FOREST-1 精灵 | waits on the second prior (g4/g5) | | | | | PC-PILOTS.md P8 |
| T3-DRAGON-1 龙族 | waits on the second prior (g4/g5) | | | | | PC-PILOTS.md P8 |

## N in the page's runtime

`analysis/pilot/page_time.py`, run in Pyodide through `page_time_in_pyodide.py` and `analysis/scaling/web_sim/run_py.js`
on the build's own bundle: the hero gate's time match without its pool (X then the generic bot piloting the hero,
both seats, the field's six other decks in turn, mcts:100+plan opposite). Hero wall time per searched decision; in
Pyodide one thread, so wall = CPU. The gates' rule: inside 0.97-1.03 N stays, else N = round(N / ratio), once.

- normal: X = the pilot at its gated N, base = mcts:100+plan, 24 pairs.
- strong: X = the pilot at a first guess, base = mcts:400+plan, 24 pairs. First guess from the native gates' two
  points (ratio 1.94 at N 100, about 1.1-1.2 at the equal-CPU N): the pilot's time is about a fixed part plus N times
  about twice the hand-set bot's per iteration, so x4 iterations is far under 4x time; guess N = 6.4 x the gated N.
- max: the same with base = mcts:1000+plan, 12 pairs; guess N = 17.7 x the gated N.

Seeds: the analysis line (timing only); see Results.

## Acceptance at strong (before publishing)

Native hero gate at the page's strong N: X = the pilot, base = mcts:400+plan, opponents mcts:100+plan, 100 pairs a
deck on deals of its own. Max is not gated (its cost); it rides on strong's result and is labelled as not measured.

Predictions (written before any of these games):
- (A1) For each installed deck, the pilot at strong scores at least as high as mcts:400+plan on the same pairs (paired
  difference ≥ 0): 0.85 each; all of them: 0.55.
- (A2) The paired difference at strong is smaller than at normal for most decks (deeper search narrows the gap): 0.55.
- (A3) The page's normal N is within ±15% of the native gated N for every deck: 0.6.

Added 20:5xZ, before any of its games: the pilots were trained and gated against the bot's six other frozen decks
only, but in the trainer the AI faces the player's own deck. So the acceptance adds opponents the pilot never saw: the
hero against the bot's 12 decks without a pilot (analysis/pilot/fields/unseen/<key>.txt; bot-built lists only), at the
page's normal N against mcts:100+plan, 100 pairs a deck.
- (A4) For each installed deck, the pilot scores at least as high as the generic bot against the unseen decks (paired
  difference ≥ 0): 0.75 each.
- (A5) The gain against unseen decks is smaller than against the training field for most decks: 0.7.

## Results

### N in the page's runtime (20:0x-20:3xZ, Pyodide 0.26.4 in Node on the build's bundle; data/page-time)

Seeds (timing only, the analysis line 6e112a1a / 620bea29): normal 87200000 + 100 i (24 pairs), strong 87200700 + 100 i
(24 pairs), max the normal deals' first 12 (an intended reuse, so the two levels' times pair by deal). Hero wall ms per
searched decision (Pyodide has one thread; its process_time reads 0).

| deck | level | X ms | generic ms | ratio | N → page N |
|---|---|---|---|---|---|
| T1-SWORD-1 | normal (mcts:100) | 71.33 | 55.1 | 1.295 | 39 → 30 |
| T1-SWORD-1 | strong (mcts:400) | 200.14 | 143.39 | 1.396 | 180 → 129 |
| T1-SWORD-1 | max (mcts:1000) | 454.11 | 330.76 | 1.373 | 480 → 350 |
| T1-ABYSS-1 | normal (mcts:100) | 90.14 | 69.02 | 1.306 | 39 → 30 |
| T1-ABYSS-1 | strong (mcts:400) | 205.56 | 142.46 | 1.443 | 180 → 125 |
| T1-ABYSS-1 | max (mcts:1000) | 501.78 | 329.56 | 1.523 | 480 → 315 |
| T3-RUNE-1 | normal (mcts:100) | 74.25 | 56.95 | 1.304 | 28 → 21 |
| T3-RUNE-1 | strong (mcts:400) | 182.63 | 162.04 | 1.127 | 126 → 112 |
| T3-RUNE-1 | max (mcts:1000) | 390.17 | 353.97 | 1.102 | 336 → 305 |
| T1-HAVEN-1 | normal (mcts:100) | 68.49 | 58.02 | 1.18 | 35 → 30 |
| T1-HAVEN-1 | strong (mcts:400) | 186.98 | 134.78 | 1.387 | 180 → 130 |
| T1-HAVEN-1 | max (mcts:1000) | 421.64 | 305.35 | 1.381 | 480 → 348 |
| T1-PORTAL-1 | normal (mcts:100) | 98.92 | 75.72 | 1.306 | 47 → 36 |
| T1-PORTAL-1 | strong (mcts:400) | 265.47 | 161.2 | 1.647 | 216 → 131 |
| T1-PORTAL-1 | max (mcts:1000) | 561.07 | 334.07 | 1.679 | 576 → 343 |

- The net costs more in the page than natively: at the gated N the native in-gate ratio was 1.11-1.20, in the page
  1.18-1.31. The page's normal N is 23-25% below the gated N (主教 14%).
- The generic bot's time grows much slower than its iterations (mcts:400 about 2.5x mcts:100's time, mcts:1000 about
  5.5x): it has a large fixed part per decision. The pilot's per-iteration cost is about 3x the hand-set bot's in the
  page (皇家护卫: about 36 ms fixed + 0.88 ms an iteration).
- (A3) page normal N within ±15% of the gated N for every deck: **FALSE** (only 主教, −14%).
- Installed N (ui.session.PILOT_N):

  | deck | normal | strong | max |
  |---|---|---|---|
  | 皇家护卫 T1-SWORD-1 | 30 | 129 | 350 |
  | 梦魇 T1-ABYSS-1 | 30 | 125 | 315 |
  | 巫师 T3-RUNE-1 | 21 | 112 | 305 |
  | 主教 T1-HAVEN-1 | 30 | 130 | 348 |
  | 超越者 T1-PORTAL-1 | 36 | 131 | 343 |

### Acceptance (native, 100 pairs a deck, --bank confirm)

Because the page's N is below the gated N, normal is re-checked at the page's N too (87202100 + 100 i), then strong
(87201400 + 100 i). (running)
