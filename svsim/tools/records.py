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

from svsim.cards.pool import card
from svsim.core.actions import from_dict, to_dict
from svsim.core.engine import apply, new_game
from svsim.core.state import GameState

VERSION = 1


def new_record(you_deck: list, ai_deck: list, seed: int, first: int, ai_spec: str) -> dict:
    return {"version": VERSION, "seed": seed, "first": first, "ai": ai_spec,
            "decks": [[c.card_id for c in you_deck], [c.card_id for c in ai_deck]],
            "actions": [], "winner": None, "date": time.strftime("%Y-%m-%d %H:%M")}


def add(record: dict, action) -> None:
    record["actions"].append(to_dict(action))


def encode(record: dict) -> str:
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw, 9)).decode()


def decode(text: str) -> dict:
    """A record from a replay code or the path of a saved record."""
    text = text.strip()
    if os.path.exists(text):
        with open(text, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(zlib.decompress(base64.b64decode("".join(text.split()))))


def save(record: dict, folder: str = "replays") -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("%Y%m%d-%H%M%S") + f"-{record['seed']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
    return path


def start(record: dict) -> GameState:
    d0, d1 = ([card(i) for i in ids] for ids in record["decks"])
    return new_game(d0, d1, seed=record["seed"], first=record["first"])


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
