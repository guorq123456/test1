"""One game against the AI, driven by a graphical front end (web/index.html).

The front end only draws what `view()` returns and sends back the index of
the action the player picked; all rules stay in the engine. The same session
runs in the browser (Pyodide) and behind the local web server
(tools/web.py). Every method returns plain JSON-friendly data.
"""
from __future__ import annotations

import random

from svsim.cards import decks, library
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, Mulligan, PlayCard
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import CardType, Phase
from svsim.core.state import CardInstance, GameState, leader_of
from svsim.tools import records
from svsim.ui.text import _follower_status, card_name, describe, describe_line, keywords_zh

assert library.__all__

DECKS = {"rhino": ("破魔虫精灵", decks.RHINO_FOREST), "ramp": ("跳费龙", decks.RAMP_DRAGON),
         "pirate": ("海盗皇家", decks.PIRATE_SWORD)}
LEVELS = {"fast": "greedy+plan", "normal": "mcts:100+plan", "strong": "mcts:200+plan"}


def _kind(defn) -> str:
    return {CardType.FOLLOWER: "follower", CardType.AMULET: "amulet", CardType.SPELL: "spell"}.get(
        defn.type, "other")


def card_view(state: GameState, c: CardInstance, in_hand: bool = False) -> dict:
    out = {"uid": c.uid, "name": card_name(c.defn), "kind": _kind(c.defn), "cost": c.cost,
           "base_cost": c.defn.cost, "keywords": keywords_zh(c.keywords)}
    if c.defn.is_follower:
        out.update(atk=c.atk, life=c.life, max_life=c.max_life,
                   evolved=2 if c.super_evolved else 1 if c.evolved else 0)
        if not in_hand:
            out["status"] = _follower_status(state, c)
    if c.countdown is not None:
        out["countdown"] = c.countdown
    return out


class Session:
    def __init__(self):
        self.state: GameState | None = None
        self.actions: list = []
        self.log: list[str] = []
        self.record: dict | None = None
        self.ai = None

    # --- game flow ------------------------------------------------------------------

    def start(self, you: str = "rhino", opponent: str = "ramp", level: str = "normal",
              seed: int | None = None, first: str | None = None) -> dict:
        seed = random.randrange(10 ** 9) if seed is None else seed
        mine, theirs = decks.build(DECKS[you][1]), decks.build(DECKS[opponent][1])
        order = None if first in (None, "random") else (0 if first == "you" else 1)
        self.state = new_game(mine, theirs, seed=seed, first=order)
        spec = LEVELS.get(level, level)
        self.record = records.new_record(mine, theirs, seed, self.state.first, spec, first_arg=order)
        self.record["names"] = [you, opponent]
        from svsim.tools.arena import make_agent
        self.ai = make_agent(spec, seed)
        self.decks = (DECKS[you][0], DECKS[opponent][0])
        self.log = [f"对局开始：你用{self.decks[0]}，AI 用{self.decks[1]}；你{'先手' if self.state.first == 0 else '后手'}。"]
        return self.view()

    def resume(self, record: dict) -> dict:
        """Carry on a saved game: replay its actions (the engine is deterministic)."""
        from svsim.core.actions import from_dict
        from svsim.tools.arena import make_agent
        names = record.get("names") or []
        self.decks = tuple(DECKS[n][0] for n in names) if all(n in DECKS for n in names) and names else ("", "")
        self.state = records.start(record)
        self.record = {**record, "actions": [], "winner": None, "notes": list(record.get("notes", []))}
        self.ai = make_agent(record["ai"], record["seed"])
        self.log = ["继续之前没下完的对局。"]
        for data in record["actions"]:
            action = from_dict(data)
            if action not in legal_actions(self.state):
                raise ValueError("这局的记录对不上，没法继续")
            self._apply(action, "你" if self.state.active == 0 else "AI")
        return self.view()

    def summary(self) -> dict:
        """A line for "carry on" buttons: the turn and both leaders' defense."""
        me, ai = self.state.players
        return {"turn": self.state.turn, "you": me.leader_hp, "ai": ai.leader_hp, "over": self.state.over}

    def _apply(self, action, who: str) -> None:
        if self.state.phase == Phase.MAIN:
            text = describe(self.state, action)
            if isinstance(action, EndTurn):
                text = "结束回合"
            self.log.append(f"{who}：{text}")
        records.add(self.record, action)
        turn = self.state.turn
        apply(self.state, action)
        if self.state.over:
            self.record["winner"] = self.state.winner
            self.log.append({0: "你赢了！", 1: "AI 赢了。"}.get(self.state.winner, "平局。"))
        elif self.state.turn != turn and self.state.phase == Phase.MAIN:
            self.log.append(f"—— 第 {self.state.turn} 回合（{'你' if self.state.active == 0 else 'AI'}）——")

    def act(self, index: int) -> dict:
        """Play the action at `index` in the last view's action list."""
        if self.state.active != 0 or self.state.over or not 0 <= index < len(self.actions):
            return self.view()
        self._apply(self.actions[index], "你")
        return self.view()

    def mulligan(self, indices: list) -> dict:
        if self.state.phase == Phase.MULLIGAN and self.state.active == 0:
            hand = self.state.players[0].hand
            self._apply(Mulligan(tuple(sorted({int(i) for i in indices if 0 <= int(i) < len(hand)}))), "你")
        return self.view()

    def ai_step(self) -> dict:
        """One action of the AI (it is the AI's turn or mulligan)."""
        if self.state.over or self.state.active != 1:
            return self.view()
        action = self.ai.act(self.state, legal_actions(self.state))
        self._apply(action, "AI")
        return self.view()

    # --- help -------------------------------------------------------------------------

    def hint(self) -> str:
        from svsim.search.mcts import ISMCTS
        if self.state.active != 0 or self.state.phase != Phase.MAIN:
            return "现在不是你的回合。"
        return "AI 会这样走：" + describe(self.state, ISMCTS(iterations=300).choose(self.state))

    def lethal(self) -> str:
        from svsim.search.combo import solve
        from svsim.search.lethal import find_lethal
        if self.state.active != 0 or self.state.phase != Phase.MAIN:
            return "现在不是你的回合。"
        hp = self.state.players[1].leader_hp
        quick = solve(self.state, search_nodes=0)
        lines = []
        if not quick.estimate.pattern.startswith("没有"):
            lines.append("速算：" + quick.estimate.text(hp))
        if quick.sure:
            return "\n".join(lines + ["有必杀：" + " → ".join(describe_line(self.state, quick.line))])
        r = find_lethal(self.state, max_nodes=5000)
        if r.sure:
            lines.append("有必杀：" + " → ".join(describe_line(self.state, r.line)))
        elif r.probability > 0:
            lines.append(f"没有必杀；靠运气的斩杀成功率约 {r.probability:.0%}：{describe(self.state, r.line[0])}")
        else:
            lines.append("这回合杀不了。" + ("" if r.complete else "（没搜完）"))
        return "\n".join(lines)

    def note(self, text: str) -> dict:
        text = text.strip()
        if text:
            self.record.setdefault("notes", []).append({"at": len(self.record["actions"]), "text": text})
            self.log.append(f"备注：{text}")
        return self.view()

    def code(self) -> str:
        return records.encode(self.record)

    def record_data(self) -> dict:
        """The game record so far (for saving it outside the session)."""
        return self.record

    # --- what the front end draws ------------------------------------------------------

    def view(self) -> dict:
        s = self.state
        legal = legal_actions(s) if not s.over and s.active == 0 else []
        self.actions = legal
        me, ai = s.players[0], s.players[1]
        out = {
            "turn": s.turn, "active": s.active, "over": s.over, "winner": s.winner,
            "phase": "over" if s.over else "mulligan" if s.phase == Phase.MULLIGAN else "main",
            "decks": list(getattr(self, "decks", ("", ""))),
            "you": self._side(me, True), "ai": self._side(ai, False),
            "log": self.log[-60:], "actions": [],
        }
        for i, a in enumerate(legal):
            if isinstance(a, Mulligan):
                continue
            entry = {"i": i, "text": "结束回合" if isinstance(a, EndTurn) else describe(s, a), "source": None,
                     "target": None, "type": type(a).__name__}
            if isinstance(a, PlayCard):
                entry["source"] = a.uid
            elif isinstance(a, Attack):
                entry["source"], entry["target"] = a.attacker, a.target
                entry["target_leader"] = leader_of(a.target) is not None
            elif isinstance(a, (Evolve, Engage, Fuse)):
                entry["source"] = a.uid
            out["actions"].append(entry)
        if s.phase == Phase.MULLIGAN and s.active == 0:
            out["mulligan"] = True
        if s.over:
            out["code"] = self.code()
        return out

    def _side(self, p, mine: bool) -> dict:
        s = self.state
        out = {"hp": p.leader_hp, "max_hp": p.leader_max_hp, "pp": p.pp, "max_pp": p.max_pp, "ep": p.ep,
               "sep": p.sep, "deck": len(p.deck), "hand_count": len(p.hand), "grave": p.shadows,
               "combo": p.combo, "bonus": bool(p.bonus_ready), "bonus_active": bool(p.bonus_active),
               "field": [card_view(s, c) for c in p.field],
               "leader_area": [card_view(s, c) for c in p.leader_area]}
        if mine:
            out["hand"] = [card_view(s, c, in_hand=True) for c in p.hand]
        return out
