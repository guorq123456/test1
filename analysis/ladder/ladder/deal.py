"""The referee's deal (base-2, LEDGER LD-27 and LD-29): how a job's seed becomes a game, the same everywhere a game
is started or rebuilt (runner, replay, arena, submission checks).

- LD-27: with no key, the strategies' seeds are the game seed x2+1 / x2+2 and the engine is seeded with the game
  seed itself, so a strategy can work its seed back to the game seed and rerun svsim's new_game to read its own
  deck order (and the opponent's, when the opponent's list is public). With a key, the engine seed and both
  strategy seeds go through HMAC-SHA256 under a key that exists only on the host's side: nothing a strategy is
  given leads back to them.
- LD-29: new_game numbers the cards (uid) in list order before it shuffles, and lists come sorted by card id, so
  every uid the opponent shows says where that card sits in its list. With a key, each list is put in a keyed
  random order first: the uids carry nothing.

The parent process seals each job (`seal`) before a worker sees it; workers and strategies never hold the key.
The log keeps the derived values ("deal"), so a replay needs no key. A job with no "deal" plays exactly as before
base-2 (phase 1's logs replay unchanged).

    python -m ladder.deal new KEYFILE      # the host makes a key once (32 random bytes, hex); never in the repo
"""
from __future__ import annotations

import hashlib
import hmac
import os
import random
import secrets
import sys
from pathlib import Path

DEAL_VERSION = "deal-2"
KEY_ENV = "LADDER_KEY_FILE"
DEFAULT_KEY = Path(r"C:\claude\ladder-host\ladder.key")      # Salem's computer; the host's directory


# The task's formal seed segments (SEEDS.md 正式分段): a game on one of these seeds is never dealt without the key
# (LD-27: without it a strategy's seed gives the game seed away). Host measurement and probe segments are not here.
FORMAL = ((87400000, 88400000, "调参（练习场、收提交的冒烟局）"), (88500000, 89000000, "把关"),
          (89100000, 89400000, "累计确认"), (89500000, 91000000, "正式天梯"), (91100000, 91600000, "最终自测"),
          (91700000, 91800000, "锚点"), (91900000, 92000000, "公共题、起点测量"), (92100000, 92200000, "抽查重测"))


def formal(seed: int) -> str | None:
    """The name of the formal segment `seed` is in, or None."""
    for lo, hi, name in FORMAL:
        if lo <= int(seed) < hi:
            return name
    return None


def require(job: dict, key: bytes | None) -> None:
    """Refuse a formal-seed job without the key, loudly (review of 11-22: only the pool used to refuse)."""
    if key is None and job.get("deal") is None:
        seg = formal(job["seed"])
        if seg:
            raise DealError(f"{job['id']}: seed {job['seed']} is in the formal segment {seg}; no deal key "
                            f"(base-2): put it at {DEFAULT_KEY} or set {KEY_ENV}")


class DealError(Exception):
    pass


def load_key(path=None) -> bytes | None:
    """The key from `path`, else from $LADDER_KEY_FILE, else from DEFAULT_KEY if it exists; None if there is none.
    A path given (or named by the variable) that can't be read is an error, not "no key"."""
    p = path or os.environ.get(KEY_ENV)
    if p:
        p = Path(p)
        if not p.is_file():
            raise DealError(f"no key file at {p}")
    elif DEFAULT_KEY.is_file():
        p = DEFAULT_KEY
    else:
        return None
    text = p.read_text(encoding="ascii").strip()
    key = bytes.fromhex(text)
    if len(key) < 16:
        raise DealError(f"{p}: a key has at least 16 bytes")
    return key


def resolve(key) -> bytes | None:
    """`key` as the runner takes it: "auto" (load_key()), None (no key: the old deal), bytes, or a path."""
    if key == "auto":
        return load_key()
    if key is None or isinstance(key, bytes):
        return key
    return load_key(key)


def key_id(key: bytes) -> str:
    """Names the key in logs without giving it away."""
    return hashlib.sha256(b"ladder-key-id:" + key).hexdigest()[:12]


def derive(key: bytes, seed: int, what: str) -> int:
    return int.from_bytes(hmac.new(key, f"{what}:{int(seed)}".encode(), hashlib.sha256).digest()[:8], "big")


def seal(job: dict, key: bytes | None) -> dict:
    """The job with its deal filled in (a copy). No key, or a job already sealed: unchanged. Strategy seeds a
    host tool chose itself (gate, arena, submission checks draw them apart from the game seed) are kept."""
    if key is None or job.get("deal") is not None:
        return job
    s = int(job["seed"])
    out = dict(job)
    out["deal"] = {"version": DEAL_VERSION, "key": key_id(key), "engine": derive(key, s, "engine"),
                   "order": [derive(key, s, "order0"), derive(key, s, "order1")]}
    if not out.get("strategy_seeds"):
        out["strategy_seeds"] = [derive(key, s, "strategy0") % 2 ** 62, derive(key, s, "strategy1") % 2 ** 62]
    return out


def strategy_seeds(job: dict) -> list[int]:
    """The seeds the two strategies are built with (without a deal and none given: the old x2+1 / x2+2)."""
    return list(job.get("strategy_seeds") or [job["seed"] * 2 + 1, job["seed"] * 2 + 2])


def start(job: dict, first="first_arg"):
    """(decks, state) at the start of the game `job` (a job or a log line). `first`: the key holding the
    first-player argument ("first" in a job, "first_arg" in a log line)."""
    from ladder.runner import load_deck
    from svsim.core.engine import new_game
    decks = [load_deck(d) for d in job["decks"]]
    d = job.get("deal")
    seed = job["seed"]
    if d is not None:
        decks = [list(x) for x in decks]
        for i, x in enumerate(decks):
            random.Random(d["order"][i]).shuffle(x)
        seed = d["engine"]
    return decks, new_game(decks[0], decks[1], seed=seed, first=job.get(first))


def new_key_file(path) -> str:
    p = Path(path)
    if p.exists():
        raise DealError(f"{p} already exists: a key is made once")
    p.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    p.write_text(key.hex() + "\n", encoding="ascii")
    return key_id(key)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "new":
        print(f"key {new_key_file(sys.argv[2])} written to {sys.argv[2]}")
    elif len(sys.argv) in (2, 3) and sys.argv[1] == "id":
        k = load_key(sys.argv[2] if len(sys.argv) == 3 else None)
        print(key_id(k) if k else "no key")
    else:
        raise SystemExit("python -m ladder.deal new KEYFILE | id [KEYFILE]")


if __name__ == "__main__":
    main()
