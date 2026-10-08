"""One game against the AI, driven by a graphical front end (web/index.html).

The front end only draws what `view()` returns and sends back the index of
the action the player picked; all rules stay in the engine. The same session
runs in the browser (Pyodide) and behind the local web server
(tools/web.py). Every method returns plain JSON-friendly data.

A finished game can also be opened for review (`review`): the front end steps
through it (`goto`), the player marks their own moves as mistakes (`mark`, kept
in the record's "mistakes" so learning leaves them out) and writes notes; the
hint and lethal check answer for the position on screen.
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
         "pirate": ("海盗皇家", decks.PIRATE_SWORD), "combo": ("连击精灵", decks.COMBO_FOREST),
         "face": ("快攻龙", decks.FACE_DRAGON), "elf-t": ("连击妖（比赛版）", decks.ELF_T),
         "nemesis-t": ("机锋（比赛版）", decks.NEMESIS_T), "ramp-t": ("跳费龙（比赛版）", decks.RAMP_T),
         "pirate-t": ("旗皇（比赛版）", decks.PIRATE_T)}
# Every level uses a deck's learned evaluation where there is one (svsim/learn/weights); normal and
# strong are arena.VERSIONS v2r and v2s (the refitted turn-end model, learn.phased; normal also keeps
# its search tree between the moves of a turn, at v2's time per move: 53.3% over v2 in a fixed 600
# games, 2026-10-07). Both use the per-pairing models in svsim/learn/phased_models where one is installed.
LEVELS = {"fast": "greedy+plan+learned", "normal": "mcts:115+plan+learned+phased+reuse",
          "strong": "mcts:200+plan+learned+phased",
          # the normal level of the build published before (5175def): v2 with the lethal screen it had then
          # (200 iterations, no near-lethal deepening); to play against the old bot for comparison
          "original": "mcts:100+plan+learned+phased+screen=200"}


def bot_info(level: str, spec: str) -> dict:
    """What played the AI's side, for the record: the level picked, the version's name in
    arena.VERSIONS (None if the spec isn't one), the spec and the commit of the build."""
    from svsim.build import commit
    from svsim.tools.arena import VERSIONS
    return {"level": level if level in LEVELS else None,
            "version": next((k for k, v in VERSIONS.items() if v == spec or k == spec), None),
            "spec": spec, "build": commit()}


def bot_of(record: dict) -> dict:
    """A record's bot_info; records from before it was kept give their spec only."""
    return record.get("bot") or {"level": None, "version": None, "spec": record.get("ai"), "build": None}


def deck_names(record: dict) -> tuple:
    """Both decks' names (records from before "names" was kept: by their cards)."""
    keys = list(record.get("names") or [])
    if len(keys) != 2 or not all(k in DECKS for k in keys):
        lists = {key: sorted(c.card_id for c in decks.build(listing)) for key, (_, listing) in DECKS.items()}
        keys = [next((k for k, ids in lists.items() if ids == sorted(side)), None) for side in record["decks"]]
    return tuple(DECKS[k][0] if k in DECKS else "" for k in keys)


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
        self.reviewing = False

    # --- game flow ------------------------------------------------------------------

    def start(self, you: str = "rhino", opponent: str = "ramp", level: str = "normal",
              seed: int | None = None, first: str | None = None) -> dict:
        seed = random.randrange(10 ** 9) if seed is None else seed
        mine, theirs = decks.build(DECKS[you][1]), decks.build(DECKS[opponent][1])
        order = None if first in (None, "random") else (0 if first == "you" else 1)
        self.state = new_game(mine, theirs, seed=seed, first=order)
        self.reviewing = False
        spec = LEVELS.get(level, level)
        self.record = records.new_record(mine, theirs, seed, self.state.first, spec, first_arg=order)
        self.record["names"] = [you, opponent]
        self.record["bot"] = bot_info(level, spec)
        from svsim.tools.arena import make_agent
        self.ai = make_agent(spec, seed)
        self.decks = (DECKS[you][0], DECKS[opponent][0])
        self.log = [f"对局开始：你用{self.decks[0]}，AI 用{self.decks[1]}；你{'先手' if self.state.first == 0 else '后手'}。"]
        return self.view()

    def resume(self, record: dict) -> dict:
        """Carry on a saved game: replay its actions (the engine is deterministic)."""
        from svsim.core.actions import from_dict
        from svsim.tools.arena import make_agent
        self.decks = deck_names(record)
        self.reviewing = False
        self.state = records.start(record)
        self.record = {**record, "actions": [], "winner": None, "notes": list(record.get("notes", []))}
        from svsim.build import commit
        if record.get("bot") and record["bot"].get("build") != commit():   # carried on by another build
            self.record["bot"] = {**record["bot"], "resumed_build": commit()}
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
        if self.reviewing or self.state.active != 0 or self.state.over or not 0 <= index < len(self.actions):
            return self.view()
        self._apply(self.actions[index], "你")
        return self.view()

    def mulligan(self, indices: list) -> dict:
        if not self.reviewing and self.state.phase == Phase.MULLIGAN and self.state.active == 0:
            hand = self.state.players[0].hand
            self._apply(Mulligan(tuple(sorted({int(i) for i in indices if 0 <= int(i) < len(hand)}))), "你")
        return self.view()

    def ai_step(self) -> dict:
        """One action of the AI (it is the AI's turn or mulligan)."""
        if self.reviewing or self.state.over or self.state.active != 1:
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

    def impact(self, samples: int = 4) -> dict:
        """When reviewing, at one of your decisions: the rest of your turn as you
        played it, the AI's way from here and ending the turn now, compared by
        their impact on winning (search.impact). Kept in the record's "impact"
        (by action index), so it is worked out once."""
        from svsim.search import impact
        from svsim.tools.impact import ai_turn
        if not self.reviewing:
            return {"error": "打完的对局在复盘里可以看每一步对胜负的影响。"}
        at, state = self.review_at, self.state
        if state.over or state.active != 0 or state.phase != Phase.MAIN:
            return {"error": "翻到你自己回合里的一步再看。"}
        cached = (self.record.get("impact") or {}).get(str(at))
        if cached:
            return cached
        from svsim.core.actions import from_dict
        end, played = None, 0
        for i in range(at, len(self.positions) - 1):
            action = from_dict(self.record["actions"][i])
            pos = self.positions[i]
            if pos.active != 0 or pos.turn != state.turn:
                break
            if isinstance(action, EndTurn):
                end = pos
                break
            played += isinstance(action, PlayCard)
        if end is None:
            return {"error": "你在这回合赢了（或对局在这回合结束），不用比较。"}
        ai_end, ai_played = ai_turn(state, "mcts:100+plan+learned", self.record["seed"] + at)
        if ai_end.over:
            return {"error": "AI 从这里能直接斩杀，你的打法没有斩杀。"}
        labels = ["你的打法", "AI的打法", "直接结束"]
        out = impact.assess(state, [end, ai_end, state], labels, [played, ai_played, 0], samples=samples,
                            seed=at, opponent="greedy+plan+learned")
        result = {"at": at, "turn": state.turn, "samples": samples, "columns": labels,
                  "rows": [[label] + [impact.cell(i, key) for i in out] for key, label, _ in impact.DIMENSIONS],
                  "reading": impact.reading(out[0], out[1]),
                  "meaning": [[label, text] for _, label, text in impact.DIMENSIONS]}
        self.record.setdefault("impact", {})[str(at)] = result
        return result

    def note(self, text: str) -> dict:
        """A note before the next action (when reviewing: about the action on screen)."""
        text = text.strip()
        if text:
            at = self.review_at if self.reviewing else len(self.record["actions"])
            self.record.setdefault("notes", []).append({"at": at, "text": text})
            if not self.reviewing:
                self.log.append(f"备注：{text}")
        return self.view()

    def code(self) -> str:
        return records.encode(self.record)

    def record_data(self) -> dict:
        """The game record so far (for saving it outside the session)."""
        return self.record

    # --- reviewing a finished game ------------------------------------------------------

    def review(self, record: dict) -> dict:
        """Open a saved game: the view shows the position before its first move by
        the player, with `review` (that move, whether it is marked) and `moves`
        (every move of the game, to jump to)."""
        from svsim.core.actions import from_dict
        self.decks = deck_names(record)
        self.record = {**record, "mistakes": sorted(set(record.get("mistakes", []))),
                       "notes": list(record.get("notes", []))}
        self.ai, self.reviewing = None, True
        state = records.start(record)
        self.positions, self.moves = [], []
        for i, data in enumerate(record["actions"]):
            action = from_dict(data)
            self.positions.append(state.clone())
            if state.phase == Phase.MAIN:
                text = "结束回合" if isinstance(action, EndTurn) else describe(state, action)
                self.moves.append({"i": i, "turn": state.turn, "who": "you" if state.active == 0 else "ai",
                                   "text": text})
            apply(state, action)
        self.positions.append(state)
        first = next((m["i"] for m in self.moves if m["who"] == "you"), 0)
        return self.goto(first)

    def goto(self, at: int) -> dict:
        """Show the position before action `at` (the number of actions: the end)."""
        self.review_at = max(0, min(int(at), len(self.positions) - 1))
        self.state = self.positions[self.review_at]
        return self.view()

    def mark(self, on: bool = True, at: int | None = None) -> dict:
        """Mark the player's move (the one on screen, or action `at`) as a mistake, or unmark it."""
        at = self.review_at if at is None else int(at)
        move = next((m for m in self.moves if m["i"] == at), None)
        if not self.reviewing or move is None or move["who"] != "you":
            raise ValueError("只能标记你自己的操作")
        marks = set(self.record["mistakes"])
        (marks.add if on else marks.discard)(at)
        self.record["mistakes"] = sorted(marks)
        return self.view()

    def _review_view(self, out: dict) -> None:
        notes = records.notes_at(self.record)
        marks = set(self.record["mistakes"])
        lines, turn = [], None
        for m in self.moves:
            if m["i"] >= self.review_at:
                break
            if m["turn"] != turn:
                turn = m["turn"]
                lines.append(f"—— 第 {turn} 回合 ——")
            lines.append(("你" if m["who"] == "you" else "AI") + "：" + m["text"])
        out["log"] = lines[-60:]
        out["moves"] = [{**m, "mistake": m["i"] in marks, "notes": notes.get(m["i"], [])} for m in self.moves]
        move = next((m for m in out["moves"] if m["i"] == self.review_at), None)
        out["review"] = {"at": self.review_at, "end": len(self.positions) - 1, "move": move,
                         "winner": self.positions[-1].winner}

    # --- what the front end draws ------------------------------------------------------

    def view(self) -> dict:
        s = self.state
        legal = legal_actions(s) if not s.over and s.active == 0 and not self.reviewing else []
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
        if s.phase == Phase.MULLIGAN and s.active == 0 and not self.reviewing:
            out["mulligan"] = True
        if s.over:
            out["code"] = self.code()
        if self.reviewing:
            self._review_view(out)
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
