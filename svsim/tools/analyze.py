"""Analyze decks automatically: how each one wins, how fast, with what (Chinese report).

    python -m svsim.tools.analyze ramp pirate combo face --games 40

The player's way of picking up a deck (2026-10-06): first work out how the
deck wins, then how the opponent's deck wins, then plan around both. This
tool does the measuring part without being told anything about the decks:

- 打木桩 (goldfish): the race clock (search.race) from the opening after the
  redraw, with nobody answering, and with every follower answered on the
  opponent's turns (the player's premise for a damage deck); the turn it
  kills on and the route (holding, ramping, digging);
- AI games between every pair of decks (`--spec` on both sides), then from the
  records: win rates; the own turn each deck wins on; where its damage to the
  enemy leader comes from, card by card and by kind (follower attacks, cards'
  abilities, end-of-turn effects); healing; the followers that stay on the
  field (learn.survival); what it evolves; the cards that go with winning
  (win rate in the games a card was played against the deck's average).

The games are only as good as the AI playing them: read it as "what the AI
found", to be checked against how people play the deck.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
from multiprocessing import Pool
import statistics

from svsim.ui.session import DECKS

KINDS = {"attack": "随从攻击", "card": "卡牌效果", "end": "回合结束效果", "other": "其他"}


# --- goldfish ---------------------------------------------------------------------------------

def _goldfish(job) -> tuple:
    from svsim.agents.mulligan import mulligan
    from svsim.cards import decks
    from svsim.core.engine import apply, new_game
    from svsim.core.enums import Phase
    from svsim.learn.survival import Removal
    from svsim.search import race
    deck, opponent, g, answered = job
    side = g % 2
    cards = [None, None]
    cards[side], cards[1 - side] = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
    state = new_game(cards[0], cards[1], seed=7000 + g, first=(g // 2) % 2)
    while state.phase == Phase.MULLIGAN:
        apply(state, mulligan(state))
    clock = race.clock(state, side, horizon=9, digging=True, removal=Removal() if answered else None)
    return deck, answered, clock.turns, clock.how


def goldfish(decks_: list, n: int, pool) -> dict:
    """{(deck, answered): [(turns, how)]}; the opponent's deck only fills the other seat."""
    jobs = [(d, decks_[(i + 1) % len(decks_)], g, answered)
            for i, d in enumerate(decks_) for answered in (False, True) for g in range(n)]
    out = defaultdict(list)
    for deck, answered, turns, how in pool.imap_unordered(_goldfish, jobs):
        out[(deck, answered)].append((turns, how))
    return out


# --- what the games show ------------------------------------------------------------------------

def _label(state, action) -> tuple[str, str]:
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
    from svsim.ui.text import card_name
    me = state.active
    if isinstance(action, PlayCard):
        c = state.in_hand(me, action.uid)
        return "card", card_name(c.defn) if c else "?"
    if isinstance(action, Attack):
        c = state.in_play(action.attacker)
        return "attack", card_name(c.defn) if c else "?"
    if isinstance(action, Evolve):
        c = state.in_play(action.uid)
        return "card", (card_name(c.defn) if c else "?") + "（进化）"
    if isinstance(action, EndTurn):
        return "end", "回合结束 / 下回合开始"
    return "other", type(action).__name__


def game_facts(record: dict) -> dict:
    """One replay: per side, damage dealt to the enemy leader by source, healing, cards
    played (first own turn), evolutions, the winner and the turn the game ended on."""
    from svsim.core.actions import Evolve, PlayCard, from_dict
    from svsim.core.engine import apply
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    from svsim.ui.session import deck_names
    from svsim.ui.text import card_name
    names = {DECKS[k][0]: k for k in DECKS}
    keys = [names.get(n) for n in deck_names(record)]
    facts = {side: dict(deck=keys[side], damage=Counter(), kinds=Counter(), healed=0, played={}, evolved=Counter())
             for side in (0, 1)}
    state = R.start(record)
    for data in record["actions"]:
        action = from_dict(data)
        if state.phase != Phase.MAIN:
            apply(state, action)
            continue
        me = state.active
        kind, label = _label(state, action)
        if isinstance(action, PlayCard):
            c = state.in_hand(me, action.uid)
            facts[me]["played"].setdefault(card_name(c.defn), state.players[me].turns_taken)
        if isinstance(action, Evolve):
            c = state.in_play(action.uid)
            facts[me]["evolved"][("超进化" if action.super_ else "进化") + card_name(c.defn)] += 1
        hp = [p.leader_hp for p in state.players]
        cap = [p.leader_max_hp for p in state.players]
        apply(state, action)
        for side in (0, 1):
            change = state.players[side].leader_hp - hp[side]
            if state.players[side].leader_max_hp < cap[side]:
                continue                               # max defense lowered (Zooey): not damage
            if change > 0:
                facts[side]["healed"] += change
            elif change < 0:
                dealer = 1 - side
                if dealer == me:
                    facts[dealer]["damage"][label] += -change
                    facts[dealer]["kinds"][kind] += -change
                else:                                  # the side not acting: its effects on the other's turn
                    facts[dealer]["damage"]["对方回合中的效果"] += -change
                    facts[dealer]["kinds"]["other"] += -change
    for side in (0, 1):
        facts[side]["won"] = state.winner == side
        facts[side]["turns"] = state.players[side].turns_taken
    return facts


def summarize(records: list) -> dict:
    """Per deck: games, wins by opponent, winning turns, damage and kinds, healing, evolutions, card lift."""
    out = defaultdict(lambda: dict(games=0, wins=0, vs=defaultdict(lambda: [0, 0]), win_turns=[], damage=Counter(),
                                   kinds=Counter(), healed=[], evolved=Counter(), played=defaultdict(lambda: [0, 0])))
    for record in records:
        facts = game_facts(record)
        for side in (0, 1):
            f, foe = facts[side], facts[1 - side]
            d = out[f["deck"]]
            d["games"] += 1
            d["wins"] += f["won"]
            d["vs"][foe["deck"]][0] += f["won"]
            d["vs"][foe["deck"]][1] += 1
            if f["won"]:
                d["win_turns"].append(f["turns"])
            d["damage"].update(f["damage"])
            d["kinds"].update(f["kinds"])
            d["healed"].append(f["healed"])
            d["evolved"].update(f["evolved"])
            for card in f["played"]:
                d["played"][card][0] += f["won"]
                d["played"][card][1] += 1
    return out


# --- the report -------------------------------------------------------------------------------

def _rate(k: int, n: int) -> str:
    return f"{k}/{n} ({k / n:.0%})" if n else "-"


def report(decks_: list, fish: dict, summary: dict, survival: dict, say=print) -> None:
    for deck in decks_:
        name = DECKS[deck][0]
        say(f"\n## {name}")
        for answered, premise in ((False, "随从不被解"), (True, "随从全被解")):
            rows = fish.get((deck, answered), [])
            kills = [t + 1 for t, _ in rows if t <= 9]
            routes = Counter(h.split()[0] for t, h in rows if t <= 9 and h)
            if rows:
                say(f"- 打木桩（{premise}）：10 个自己的回合内打死 {len(kills)}/{len(rows)}，"
                    f"中位数第 {statistics.median(kills) if kills else '-'} 回合；路线 {dict(routes)}")
        s = summary.get(deck)
        if not s:
            continue
        vs = "，".join(f"对{DECKS[o][0]} {_rate(*s['vs'][o])}" for o in decks_ if o != deck and s["vs"][o][1])
        say(f"- AI 互打：{_rate(s['wins'], s['games'])}（{vs}）")
        if s["win_turns"]:
            say(f"- 赢的局在自己第几回合赢：中位数 {statistics.median(s['win_turns'])}，"
                f"分布 {sorted(Counter(s['win_turns']).items())}")
        total = sum(s["kinds"].values()) or 1
        say("- 对主战者的伤害（每局平均 " + f"{total / s['games']:.1f}）：" +
            "，".join(f"{KINDS[k]} {v / total:.0%}" for k, v in s["kinds"].most_common()))
        say("  主要来源：" + "，".join(f"{c} {v / s['games']:.1f}" for c, v in s["damage"].most_common(8)))
        say(f"- 每局回血 {statistics.mean(s['healed']):.1f}")
        if s["evolved"]:
            say("- 进化给谁（每局）：" + "，".join(f"{c} {v / s['games']:.2f}" for c, v in s["evolved"].most_common(6)))
        base = s["wins"] / s["games"]
        lift = [(k / n - base, card, k, n) for card, (k, n) in s["played"].items() if n >= max(8, s["games"] // 6)]
        lift.sort(reverse=True)
        if lift:
            say("- 打出来时胜率最高的牌：" + "，".join(f"{c} {k}/{n}" for _, c, k, n in lift[:5]) +
                f"（这套牌平均 {base:.0%}）")
        for opponent in decks_:
            prof = survival.get((deck, opponent))
            if prof is not None and prof.games:
                small = statistics.mean(prof.chance(t, l) for t in (5, 6, 7) for l in (1, 2, 3))
                big = statistics.mean(prof.chance(t, l) for t in (5, 6, 7) for l in (4, 5))
                say(f"- 对{DECKS[opponent][0]}，自己的随从活过对手第 5～7 回合：小随从（1～3 血）{small:.0%}，"
                    f"大随从（4 血以上）{big:.0%}")


def main() -> None:
    from svsim.learn.survival import collect
    from svsim.tools.survival import play
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("decks", nargs="*", default=["ramp", "pirate", "combo", "face"])
    parser.add_argument("--games", type=int, default=40, help="AI games per pair of decks")
    parser.add_argument("--goldfish", type=int, default=60, help="goldfish games per deck and premise")
    parser.add_argument("--spec", default="mcts:100+plan")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--save", help="save the AI games' records to this JSON file")
    args = parser.parse_args()
    with Pool(args.workers) as pool:
        fish = goldfish(args.decks, args.goldfish, pool) if args.goldfish else {}
        jobs = [(g, args.seed, a, b, args.spec, args.spec) for a, b in combinations(args.decks, 2)
                for g in range(args.games)]
        records = pool.map(play, jobs) if jobs else []
    if args.save:
        import json
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(records, f)
    summary = summarize(records)
    survival = {(a, b): collect(records, a, b) for a in args.decks for b in args.decks if a != b}
    print(f"# 卡组分析（AI：{args.spec}，每对卡组 {args.games} 局，打木桩每种前提 {args.goldfish} 局）")
    report(args.decks, fish, summary, survival)


if __name__ == "__main__":
    main()
