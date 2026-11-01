"""Salem's board of 2026-11-01 (his 兔子教 against 三轴土, a screenshot he posted; analysis only, never search or
training): would the bot keep the four Bunnies of Desolation back, as he did, or trade them?

The screenshot is the start of the opponent's turn 8. Rebuilt here as Salem's turn 7 (he is second), just before he
casts 荒废的繁殖 with Enhance 8 (7 play points plus the bonus point):
- Salem: 19 defense; hand 荒废的繁殖, 地害矫正者, 勤劳的女祭司·泰瑞莎, 神域的物证, 图书室的魔女·莉莉尤姆, plus four
  cards set to cost 0 (the four the bunnies banish: they banish the cheapest card, and 神域的物证 at cost 1 stayed);
  deck 29. His list is DFM's 兔子主教 (dfm/HAVEN-ユーリ), close to but maybe not his own.
- The opponent (DFM's 三轴土, dfm/RUNE-ユーリ): 12 defense; a super-evolved 琪可 (6/5) with its crest, an evolved
  琪可 (5/4), an earth sigil stack of 7 and a clue amulet of 3 (as read off the screenshot); 8 cards in hand dealt
  at random from their deck, 21 left in it.
Unknown and set by assumption: evolution points (Salem 0/0, the opponent 1/0), what is in the opponent's hand, the
exact earth sigil and clue counts.

Lines after the four bunnies are in (evolved 3/3s that can attack followers; Last Words 2 damage to the enemy
leader each):
  keep   no attack (Salem's line)
  all    two into the 6/5, two into the 5/4
  big    two into the 6/5
  small  two into the 5/4

For each line: the hand-set turn-end score (search.evaluate, the bot's own), what mcts:100+plan picks from the same
position, and the line played out to the end of the game by mcts:100+plan on both sides, with the opponent's hand
re-dealt at random each time. Condition: 对手卡表已知（牌序、手牌未知）.

    python analysis/pilot/salem_board_2026_11_01.py [--playouts 100] [--workers 2]
"""
import argparse
import json
import random
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import svsim.tools.arena  # noqa: E402,F401  (card scripts)
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core import effects as E  # noqa: E402
from svsim.core.actions import Attack, EndTurn, Mulligan, PlayCard, UseBonusPP  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.search import evaluate as EV  # noqa: E402
from svsim.cards import deckcode  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402
from svsim.ui.text import describe  # noqa: E402

REF = ROOT / "analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt"
if not REF.exists():                                     # on a branch without it: claude/deck-search's copy
    REF = Path("/home/claude/test1/.wt/ds/analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt")
PROPAGATION, REHAB, TERESA, CLUE, LILIUM = 11062310, 11063110, 10861120, 90001210, 10861110
TICO, TICO_CREST, SEDIMENT = 10833110, 10833112, 90031210
LINES = ("keep", "all", "big", "small")


def read_seeds(path) -> dict:
    """label -> ids for each line "label|code" (deckbuild.read_seeds, which this branch lacks)."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            label, _, code = line.rpartition("|")
            out[label.strip()] = deckcode.decode_deck(code.strip())[2]
    return out


def _nice():
    import os
    try:
        os.nice(10)
    except (OSError, AttributeError):
        pass


def build(seed: int):
    """Salem (player 0) to act, turn 14, before 荒废的繁殖."""
    ref = read_seeds(REF)
    haven, rune = [POOL[i] for i in ref["dfm/HAVEN-ユーリ"]], [POOL[i] for i in ref["dfm/RUNE-ユーリ"]]
    st = new_game(haven, rune, seed=seed, first=1)
    apply(st, Mulligan(()))
    apply(st, Mulligan(()))
    me, op = st.players
    rng = random.Random(seed)
    for p in st.players:
        p.deck.extend(p.hand)
        p.hand.clear()
        p.field.clear()
        p.leader_area.clear()
        rng.shuffle(p.deck)
    st.turn = 14
    st.active = 0
    me.turns_taken, op.turns_taken = 7, 7
    me.max_pp, me.pp = 7, 7
    me.bonus_ready, me.bonus_active = True, False
    op.max_pp, op.pp = 7, 0
    me.leader_hp, op.leader_hp = 19, 12
    me.ep, me.sep, op.ep, op.sep = 0, 0, 1, 0

    def take(p, cid):
        card = next((c for c in p.deck if c.defn.card_id == cid), None)
        if card is not None:
            p.deck.remove(card)

    for cid in (PROPAGATION, REHAB, TERESA, LILIUM):
        take(me, cid)
        E.add_to_hand(st, 0, POOL[cid])
    E.add_to_hand(st, 0, POOL[CLUE])
    for _ in range(4):                                    # the four the bunnies banish
        E.set_cost(E.add_to_hand(st, 0, me.deck.pop().defn), 0)
    del me.deck[29:]
    for super_ in (True, False):
        take(op, TICO)
        t = E.summon(st, 1, POOL[TICO])
        t.entered_turn = -1
        E.evolve(st, t, super_=super_, notify=False)
    E.add_to_leader_area(st, 1, POOL[TICO_CREST])
    E.gain_earth_sigils(st, 1, 7, POOL[SEDIMENT])
    clue = E.summon(st, 1, POOL[CLUE])
    E.counters(clue)["clues"] = 3
    for _ in range(8):
        op.hand.append(op.deck.pop())
    del op.deck[21:]
    return st


def cast(st):
    """Bonus point, then 荒废的繁殖 enhanced (four bunnies)."""
    apply(st, next(a for a in legal_actions(st) if isinstance(a, UseBonusPP)))
    plays = [a for a in legal_actions(st) if isinstance(a, PlayCard)
             and (st.in_hand(0, a.uid) is not None) and st.in_hand(0, a.uid).defn.card_id == PROPAGATION]
    before = len(st.players[0].field)
    for a in plays:                                       # the enhanced play is the one that summons four
        t = st.clone()
        apply(t, a)
        if len(t.players[0].field) - before == 4:
            apply(st, a)
            return st
    raise RuntimeError("no enhanced play")


def line(st, name):
    me, op = st.players
    bunnies = [c for c in me.field if c.defn.is_follower]
    big, small = sorted([c for c in op.field if c.defn.is_follower], key=lambda c: -c.atk)
    plan = {"keep": [], "all": [big, big, small, small], "big": [big, big], "small": [small, small]}[name]
    for b, target in zip(bunnies, plan):
        if st.on_field(target.uid) is not None and st.on_field(b.uid) is not None:
            apply(st, Attack(b.uid, target.uid))
    return st


def hand_score(st, k=20):
    total = 0.0
    for j in range(k):
        t = st.clone()
        t.rng = random.Random(j)
        total += EV.evaluate(EV.after_end_of_turn(t), 0, EV.DEFAULT)
    return total / k


def search_pick(seed):
    """What mcts:100+plan does with the bunnies, from the cast position to its end of turn."""
    st = cast(build(seed))
    agent = make_agent("mcts:100+plan", 1000 + seed)
    steps = []
    while st.active == 0 and st.winner is None:
        a = agent.act(st, legal_actions(st))
        steps.append(describe(st, a))
        apply(st, a)
        if isinstance(a, EndTurn):
            break
    return steps


def playout(job):
    name, seed, opp_spec = job
    st = line(cast(build(seed)), name)
    agents = [make_agent("mcts:100+plan", 2 * seed), make_agent(opp_spec, 2 * seed + 1)]
    apply(st, EndTurn())
    n = 0
    while st.winner is None and n < 400:
        apply(st, agents[st.active].act(st, legal_actions(st)))
        n += 1
    return name, seed, (1.0 if st.winner == 0 else 0.0 if st.winner == 1 else 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--playouts", type=int, default=100)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--base", type=int, default=86040000)
    ap.add_argument("--out", default="runs/salem-board-2026-11-01.jsonl")
    ap.add_argument("--opp-spec", default="mcts:100+plan", help="the 三轴土 side's agent in the playouts")
    args = ap.parse_args()
    st = cast(build(args.base))
    me, op = st.players
    print("位置：", [f"{c.defn.name_zh} {c.atk}/{c.life}" for c in me.field], "对",
          [f"{c.defn.name_zh} {c.atk}/{c.life}" for c in op.field], "土", E.earth_sigils(st, 1),
          "血", me.leader_hp, op.leader_hp, flush=True)
    for name in LINES:
        t = line(st.clone(), name)
        print(f"手写评分 {name:5s} {hand_score(t):6.2f}   对面血 {t.players[1].leader_hp}，对面随从 "
              f"{len(t.players[1].followers)}，我方随从 {len(t.players[0].followers)}", flush=True)
    for seed in range(args.base, args.base + 5):
        print("mcts:100+plan 的选择：", search_pick(seed), flush=True)
    jobs = [(name, args.base + 100 + i, args.opp_spec) for i in range(args.playouts) for name in LINES]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    res = {n: [] for n in LINES}
    with out.open("w") as fh, Pool(args.workers, initializer=_nice) as pool:
        for name, seed, pts in pool.imap_unordered(playout, jobs):
            res[name].append(pts)
            fh.write(json.dumps({"line": name, "seed": seed, "points": pts, "opp_spec": args.opp_spec}) + "\n")
            fh.flush()
    print("三轴土一方：", args.opp_spec)
    for name in LINES:
        v = res[name]
        m = sum(v) / len(v)
        se = (m * (1 - m) / len(v)) ** 0.5
        print(f"打到底（两边 mcts:100+plan）{name:5s} Salem 胜率 {100 * m:5.1f}% ± {196 * se:4.1f}（{len(v)} 局）")


if __name__ == "__main__":
    main()
