"""Game records: the decks, seed and every action of a game, enough to replay it
exactly (the engine is deterministic given the seed).

A record is a JSON-friendly dict; `encode` turns it into a short text code (a
"回放码", zlib + base64) that can be pasted into a chat, `decode` reads a code
or a saved file back.
"""
from __future__ import annotations

import base64
import json
import os
import time
import zlib

from svsim.cards import library
from svsim.cards.pool import card
from svsim.core.actions import from_dict, to_dict
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.state import GameState

VERSION = 1
assert library.__all__                 # card scripts registered: a replay needs every card's abilities


def new_record(you_deck: list, ai_deck: list, seed: int, first: int, ai_spec: str,
               first_arg: int | None = None) -> dict:
    """`first` is who went first; `first_arg` what new_game was asked for (None: at
    random, which draws from the game's random numbers, so a replay must ask the same)."""
    return {"version": VERSION, "seed": seed, "first": first, "first_arg": first_arg, "ai": ai_spec,
            "decks": [[c.card_id for c in you_deck], [c.card_id for c in ai_deck]],
            "actions": [], "winner": None, "date": time.strftime("%Y-%m-%d %H:%M")}


def add(record: dict, action) -> None:
    record["actions"].append(to_dict(action))


def encode(record: dict) -> str:
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw, 9)).decode()


def decode(text: str) -> dict:
    """A record from a replay code or the path of a saved record (or of a game
    saved by the web page, which keeps the record under "record")."""
    text = text.strip()
    if os.path.exists(text):
        with open(text, encoding="utf-8") as f:
            data = json.load(f)
        return data["record"] if "decks" not in data and isinstance(data.get("record"), dict) else data
    return json.loads(zlib.decompress(base64.b64decode("".join(text.split()))))


def save(record: dict, folder: str = "replays") -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("%Y%m%d-%H%M%S") + f"-{record['seed']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
    return path


def _new(record: dict, first_arg) -> GameState:
    d0, d1 = ([card(i) for i in ids] for ids in record["decks"])
    return new_game(d0, d1, seed=record["seed"], first=first_arg)


def _replays(record: dict, first_arg) -> bool:
    state = _new(record, first_arg)
    if state.first != record["first"]:
        return False
    for data in record["actions"]:
        action = from_dict(data)
        if action not in legal_actions(state):
            return False
        apply(state, action)
    return True


def start(record: dict) -> GameState:
    """The game's opening position. Records from before `first_arg` was kept don't
    say whether the first player was drawn at random: the one that replays wins."""
    if "first_arg" in record:
        return _new(record, record["first_arg"])
    return _new(record, None if _replays(record, None) else record["first"])


def steps(record: dict):
    """Replay the game: yields (state before the action, action) for every action;
    the state is advanced after each yield, so copy it to keep it."""
    state = start(record)
    for data in record["actions"]:
        action = from_dict(data)
        yield state, action
        apply(state, action)


def notes_at(record: dict) -> dict:
    """The player's notes by the index of the action they were written before."""
    out: dict = {}
    for note in record.get("notes", []):
        out.setdefault(note["at"], []).append(note["text"])
    return out
