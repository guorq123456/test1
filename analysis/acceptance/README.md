# The acceptance library (process item 5)

The library holds positions where Salem said which play is right and why. Any value net and any move prior is
scored on them. These are checks only: they never enter search, self-play or training. The dfm lists are EXTERNAL
(Salem 「隔离训练」).

Condition: 对手卡表已知（牌序、手牌未知）.

## Running it

```
python analysis/acceptance/run.py [--net NET.npz] [--prior PRIOR.npz] [--deck LABEL]
```

- It prints each item and the pass rate per scoring (回合末, 回合中, 先验第一步, 手写评估).
- Each scoring is reported per tier, clear and marginal. Marginal pass rates are noisy and never gate alone.
- `tools.herogate` prints the same rates at the end of a gate when the hero deck has positions here and X names a
  net or a prior.

## Files

- `positions/<id>.json`: one position per file. It holds:
  - the decks, as codes;
  - how to rebuild it;
  - its fingerprint (the side's hand ids, field ids, pp, leader hp and the turn);
  - Salem's line and reason, and the line he calls wrong;
  - the scorings that apply, the number of reseeded copies, and the tier.
- `lib.py`: rebuilding, fingerprint checks and scoring.
  - A replay position is rebuilt by applying its stored action list from the deal, so no search runs.
  - A rebuild that no longer matches its fingerprint is reported and not scored.
- `builders.py`: hand-built positions (the 11-01 bunny board).
- `record.py`: writes the position files. It was run once (2026-11-02) with the two list files of claude/deck-search.
  Only the needed lists were written into the files.

## Positions

| id | deck | Salem's choice | the wrong choice | scorings |
|---|---|---|---|---|
| rune-g1t3-snack | dfm/RUNE-ユーリ | 零嘴做4土 | 空过 | turn-end, mid-turn, prior, hand-set |
| rune-g2t3-pot | dfm/RUNE-ユーリ | 先锅后光 | 先光后锅 | turn-end, mid-turn, prior, hand-set |
| rune-g3t4-evidence | dfm/RUNE-ユーリ | 先打物证再启动 | 先打解谜旋律再启动 | turn-end, mid-turn, prior, hand-set |
| rune-g1t7-tico | dfm/RUNE-ユーリ | 琪可打骑士+魔弹 | 怪兽打骑士+魔弹+琪可打脸 | turn-end, mid-turn, prior, hand-set |
| haven-bunny-board-2026-11-01 | dfm/HAVEN-ユーリ (Salem's side) | 不撞 | 全撞 | hand-set (for now) |

## Adding a position from a replay review

1. Record its action list once from the replay with `record.py`'s `record_replay`, or its own builder.
2. Write the file with Salem's line, his reason in his words, the wrong line, the scorings and the tier.
3. Check that `tests/test_acceptance_lib.py` still passes; it rebuilds every stored position.
