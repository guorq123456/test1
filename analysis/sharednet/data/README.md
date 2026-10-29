# S1 / S1(b) data, saved at the pause (Salem 2026-10-29 11:21Z 「先暂停一会」)

Condition: 对手卡表已知（牌序、手牌未知）.

- `rec/rec-<seed>.jsonl.gz`: learn.scaledata play records, 1000 games each, seed 85830000 + 2k.
  - k = 0..19 (85830000-85830038): S1, pool `fields/C-r0-pool.txt`, both sides mcts:100+plan.
  - k = 20..27 (85830040-85830054): S1(b), pool `fields/P2-pool.txt`, both sides mcts:100+plan.
  - `rec-85830056.part.jsonl`: k = 28, 911 of its 1000 games (the run was stopped; `scaledata play` with the same
    command resumes it from this part file when it is put back in the --out folder).
  - k = 29..35: not started here; k = 36..59: the RC line (Salem's computer).
- `ckpt-prior.npz`: learn.setpolicy fit's checkpoint of the shared move prior (S1 (i)), after epoch 3 (validation
  cross-entropy 1.3811 on the held-out decks' games; epochs 1-3: 1.3879, 1.3832, 1.3811); the same fit command
  with --checkpoint at this file resumes exactly.
- `cards-all.npz`: the static rows of every card in S1's turn-end, mid-turn and decision files (554 cards).

The encoded files (tok-, mid-, dec-) are not here: `scaledata encode`, `midrows encode` and `setpolicy encode` on
these records give them again.
