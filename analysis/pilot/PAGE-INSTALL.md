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

Seeds: requested from the analysis line (timing only).

## Acceptance at strong (before publishing)

Native hero gate at the page's strong N: X = the pilot, base = mcts:400+plan, opponents mcts:100+plan, 100 pairs a
deck on deals of its own. Max is not gated (its cost); it rides on strong's result and is labelled as not measured.

Predictions (written before any of these games):
- (A1) For each installed deck, the pilot at strong scores at least as high as mcts:400+plan on the same pairs (paired
  difference ≥ 0): 0.85 each; all of them: 0.55.
- (A2) The paired difference at strong is smaller than at normal for most decks (deeper search narrows the gap): 0.55.
- (A3) The page's normal N is within ±15% of the native gated N for every deck: 0.6.

## Results

(to come)
