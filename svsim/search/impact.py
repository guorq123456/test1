"""What a way of playing a turn does to winning, dimension by dimension.

The player's request (2026-10-06): judge each move by its effect on winning
the game, and show that effect in parts. A move's worth depends on the game
it is in (drawing is worth what it finds and what it costs in turns), so the
parts are measured by looking ahead in this position, not read off fixed
exchange rates:

- this turn: damage to the enemy leader, cards played and drawn, play points
  left unused, cards left in hand;
- the opponent's answer, by playing their turn with their AI on several
  determinizations (their hand and both decks reshuffled, so it doesn't peek):
  whether they kill, how much they hit back, how much of the board they
  answered ("能不能解"), how many play points it took them ("要花多少"), their
  board afterwards;
- then, at the start of the next turn: whether the player can kill now, both
  race clocks (search.race: turns each side still needs if unanswered), the
  share of samples where the player's clock comes first, and the evaluation's
  win probability there.

`assess(start, ends)` compares ways of playing the same turn, given as the
positions they end in (before ending the turn). Every way meets the same
determinizations (common random numbers), so the differences come from the
moves, not from luck.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase
from svsim.core.state import GameState
from svsim.core.view import determinize
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.search import race

DIMENSIONS = [
    # key, label, what it means (shown on the page)
    ("face", "本回合打脸", "这回合对对手主战者造成的伤害"),
    ("played", "出牌", "这回合打出的牌数"),
    ("drawn", "过牌", "这回合进手的牌数（抽牌、加入手牌）"),
    ("pp_left", "剩余PP", "结束回合时没用掉的 PP"),
    ("hand", "手牌", "结束回合时的手牌数"),
    ("killed", "被对手斩杀", "对手的回合里把你打死的比例（对手手牌按没见过的牌重新抽样，由对手的 AI 来打）"),
    ("hit_back", "对手还击", "对手回合里你掉的血"),
    ("answered", "被解场", "你场上随从的攻击力被对手处理掉的比例（能不能解）"),
    ("their_spend", "对手花费PP", "对手这回合花掉的 PP（要花多少）"),
    ("their_board", "对手场攻", "对手回合结束后对手场上随从的总攻击力"),
    ("lethal", "下回合斩杀", "到你下回合时能直接斩杀的比例"),
    ("my_clock", "我方时钟", "你下回合开始时，还要再过几个自己的回合才能斩杀（0 = 下回合就能；假设对手不再处理）"),
    ("their_clock", "对方时钟", "同一时刻对手还要几个回合能斩杀你（假设你不处理）"),
    ("race", "时钟领先", "你的时钟先到的比例（你先动，所以一样快算你先）"),
    ("value", "估值胜率", "现在的局面评估函数在你下回合开始时给的胜率，用来对照"),
]


@dataclass
class Impact:
    label: str
    turn: dict = field(default_factory=dict)        # this turn's rows (measured once)
    samples: int = 0
    totals: dict = field(default_factory=dict)      # the other rows, summed over samples
    clocks: list = field(default_factory=list)      # (mine, theirs) per sample

    def add(self, key: str, value: float) -> None:
        self.totals[key] = self.totals.get(key, 0.0) + value

    def __getitem__(self, key: str) -> float:
        if key in self.turn:
            return self.turn[key]
        return self.totals.get(key, 0.0) / max(self.samples, 1)


def _attack(state: GameState, side: int) -> dict:
    return {f.uid: f.atk for f in state.players[side].followers}


def _squash(score: float, scale: float = 8.0) -> float:
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, score / scale))))


def this_turn(start: GameState, end: GameState, played: int) -> dict:
    me = start.active
    p0, p1 = start.players[me], end.players[me]
    return {"face": start.players[1 - me].leader_hp - end.players[1 - me].leader_hp,
            "played": played,
            "drawn": len(p1.hand) - len(p0.hand) + played,
            "pp_left": p1.pp,
            "hand": len(p1.hand)}


def reply(end: GameState, me: int, agent, max_steps: int = 200) -> tuple[GameState, dict]:
    """End `me`'s turn on `end` (a determinized copy, modified) and let `agent` play
    the opponent's turn; returns the position at the start of `me`'s next turn and
    what happened."""
    board = _attack(end, me)
    hp = end.players[me].leader_hp
    apply(end, EndTurn())
    spend = 0
    for _ in range(max_steps):
        if end.over or end.active == me:
            break
        actions = legal_actions(end)
        action = agent.act(end, actions)
        if isinstance(action, EndTurn) and end.phase == Phase.MAIN:
            them = end.players[end.active]
            spend = them.max_pp - them.pp
        apply(end, action)
    left = _attack(end, me)
    total = sum(board.values())
    answered = (total - sum(a for uid, a in left.items() if uid in board)) / total if total else 0.0
    return end, {"killed": float(end.winner == 1 - me),
                 "hit_back": hp - end.players[me].leader_hp if not end.over else hp,
                 "answered": answered,
                 "their_spend": spend,
                 "their_board": sum(f.atk for f in end.players[1 - me].followers)}


def _canonical(state: GameState, me: int) -> GameState:
    """A copy whose hidden cards are in a fixed order (by card), so the
    determinizations depend only on which cards are hidden, not on how they lie."""
    s = state.clone()
    mine, theirs = s.players[me], s.players[1 - me]
    mine.deck.sort(key=lambda c: c.defn.card_id)
    pool = sorted(theirs.hand + theirs.deck, key=lambda c: c.defn.card_id)
    theirs.hand, theirs.deck = pool[:len(theirs.hand)], pool[len(theirs.hand):]
    return s


def assess(start: GameState, ends: list, labels: list | None = None, played: list | None = None,
           samples: int = 6, seed: int = 0, opponent: str = "mcts:50+plan+learned", weights=DEFAULT,
           horizon: int = race.HORIZON, nodes: int = 1000) -> list[Impact]:
    """Impacts of the ways of playing `start`'s turn that end in `ends` (positions
    before ending the turn, the same player to act). `played`: cards each way
    played this turn (for the "出牌"/"过牌" rows)."""
    from svsim.tools.arena import make_agent
    me = start.active
    labels = labels or [f"#{i + 1}" for i in range(len(ends))]
    played = played or [0] * len(ends)
    out = [Impact(label) for label in labels]
    for impact, end, n in zip(out, ends, played):
        impact.turn = this_turn(start, end, n)
    rng = random.Random(seed)
    seeds = [rng.getrandbits(64) for _ in range(samples)]
    canonical = [_canonical(end, me) for end in ends]
    for sample_seed in seeds:
        for impact, end in zip(out, canonical):
            s = determinize(end, me, random.Random(sample_seed))
            agent = make_agent(opponent, sample_seed % 100000)
            s, facts = reply(s, me, agent)
            impact.samples += 1
            for key, value in facts.items():
                impact.add(key, value)
            if s.over:
                won = s.winner == me
                impact.add("value", 1.0 if won else 0.0)
                impact.add("race", 1.0 if won else 0.0)
                impact.add("lethal", 1.0 if won else 0.0)
                impact.add("my_clock", 0 if won else horizon + 1)
                impact.add("their_clock", horizon + 1 if won else 0)
                impact.clocks.append((0, horizon + 1) if won else (horizon + 1, 0))
                continue
            mine = race.clock(s, me, horizon, nodes).turns
            theirs = race.clock(s, 1 - me, horizon, nodes).turns
            impact.clocks.append((mine, theirs))
            impact.add("lethal", float(mine == 0))
            impact.add("my_clock", mine)
            impact.add("their_clock", theirs)
            impact.add("race", float(mine <= theirs) if mine <= horizon or theirs <= horizon else 0.5)
            impact.add("value", _squash(evaluate(s, me, weights, player_moves_next=True)))
    return out


def _pad(text: str, width: int) -> str:
    """`text` padded to `width` terminal columns (Chinese characters take two)."""
    import unicodedata
    used = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)
    return text + " " * max(0, width - used)


def table(impacts: list[Impact], keys: list | None = None) -> str:
    """The impacts side by side, one row per dimension (Chinese labels)."""
    keys = keys or [k for k, _, _ in DIMENSIONS]
    labels = {k: label for k, label, _ in DIMENSIONS}
    percent = {"killed", "answered", "lethal", "race", "value"}
    width = max(10, *(len(i.label) * 2 + 2 for i in impacts))
    lines = [_pad("", 12) + "".join(_pad(i.label, width) for i in impacts)]
    for k in keys:
        cells = [_pad(f"{i[k]:.0%}" if k in percent else f"{i[k]:.1f}", width) for i in impacts]
        lines.append(_pad(labels[k], 12) + "".join(cells))
    return "\n".join(lines)


PERCENT = {"killed", "answered", "lethal", "race", "value"}


def cell(impact: Impact, key: str) -> str:
    v = impact[key]
    if key in PERCENT:
        return f"{v:.0%}"
    if key in ("my_clock", "their_clock") and impact.samples and all(
            c[0 if key == "my_clock" else 1] > race.HORIZON for c in impact.clocks):
        return f">{race.HORIZON}"
    return f"{v:.1f}" if key in ("my_clock", "their_clock", "hit_back", "their_spend", "their_board") else f"{v:.0f}"


def reading(mine: Impact, other: Impact, name: str = "AI") -> list[str]:
    """The differences that matter most between the player's way and another, in words."""
    out = []
    if abs(mine["killed"] - other["killed"]) >= 0.2:
        better = mine["killed"] < other["killed"]
        out.append(f"被对手斩杀的机会：你 {mine['killed']:.0%}，{name} {other['killed']:.0%}"
                   + ("，你的打法更安全" if better else "，你的打法更危险"))
    if abs(mine["lethal"] - other["lethal"]) >= 0.2:
        out.append(f"下回合能斩杀的机会：你 {mine['lethal']:.0%}，{name} {other['lethal']:.0%}")
    d = other["my_clock"] - mine["my_clock"]
    if abs(d) >= 0.5:
        out.append(f"你的打法让自己的斩杀{'提前' if d > 0 else '推迟'}约 {abs(d):.1f} 个回合"
                   f"（{mine['my_clock']:.1f} 对 {other['my_clock']:.1f}）")
    d = mine["their_clock"] - other["their_clock"]
    if abs(d) >= 0.5:
        out.append(f"对手斩杀你的时间{'推后' if d > 0 else '提前'}约 {abs(d):.1f} 个回合")
    if abs(mine["race"] - other["race"]) >= 0.15:
        out.append(f"时钟领先（我方时钟先到）的比例：你 {mine['race']:.0%}，{name} {other['race']:.0%}")
    if not out:
        out.append("两种打法在这些维度上差别不大")
    return out
