"""The arena's lock taken in turns (11-24, before period 2): the host first, then the player served longest ago,
that player's oldest command; a ticket left untouched is cleared. No games, no seeds."""
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import arena  # noqa: E402


def _ticket(a: Path, ns: int, who: str, age: float = 0.0) -> Path:
    q = a / "host" / "queue"
    q.mkdir(parents=True, exist_ok=True)
    t = q / f"{ns:020d}-{1000 + ns}-{who}.t"
    t.touch()
    if age:
        old = time.time() - age
        os.utime(t, (old, old))
    return t


def test_the_host_goes_first_then_the_player_served_longest_ago(tmp_path):
    a = tmp_path
    _ticket(a, 1, "astra")
    _ticket(a, 2, "astra")
    _ticket(a, 3, "fable-ultracode")
    _ticket(a, 4, "sol")
    assert arena._ticket_who(arena._queue_next(a)) == "astra"           # nobody served: the oldest ticket
    (a / "host" / "served.json").write_text(json.dumps({"astra": 50.0, "fable-ultracode": 10.0}), encoding="utf-8")
    assert arena._queue_next(a).endswith("-sol.t")                     # never served beats served long ago
    (a / "host" / "served.json").write_text(json.dumps({"astra": 50.0, "fable-ultracode": 10.0, "sol": 60.0}),
                                            encoding="utf-8")
    assert arena._queue_next(a).endswith("-fable-ultracode.t")
    _ticket(a, 9, "host")
    assert arena._queue_next(a).endswith("-host.t")                     # collecting, gating, the close: first


def test_a_players_own_commands_go_oldest_first(tmp_path):
    a = tmp_path
    _ticket(a, 7, "opus")
    _ticket(a, 5, "opus")
    assert arena._queue_next(a) == f"{5:020d}-1005-opus.t"


def test_a_ticket_nobody_touches_is_cleared(tmp_path):
    a = tmp_path
    gone = _ticket(a, 1, "sol", age=arena.QUEUE_FRESH + 5)
    _ticket(a, 2, "astra")
    assert arena._queue_next(a).endswith("-astra.t")
    assert not gone.exists()
    assert arena._queue_next(tmp_path / "nowhere") is None


def test_a_broken_served_file_only_skews_the_turns(tmp_path):
    a = tmp_path
    _ticket(a, 1, "fable")
    (a / "host").mkdir(exist_ok=True)
    (a / "host" / "served.json").write_text("{half", encoding="utf-8")
    assert arena._queue_next(a).endswith("-fable.t")


def _waiter(a: str, who: str, log: str, hold: float):
    arena.QUEUE_POLL = 0.05
    f = arena._lock(Path(a), who)
    with open(log, "a", encoding="utf-8") as out:
        out.write(who + "\n")
    time.sleep(hold)
    arena._unlock(f)


def test_waiters_take_turns_across_processes(tmp_path):
    a, log = tmp_path / "arena", tmp_path / "order.txt"
    a.mkdir()
    holder = arena._lock(a, "astra")                     # a run going on while the others queue
    ctx = mp.get_context("spawn")
    who = ["astra", "astra", "astra", "sol", "fable", "host"]
    procs = []
    for w in who:                                         # queued in this order, a little apart
        p = ctx.Process(target=_waiter, args=(str(a), w, str(log), 0.3))
        p.start()
        procs.append(p)
        deadline = time.time() + 30
        while len(list((a / "host" / "queue").glob("*.t"))) < len(procs) and time.time() < deadline:
            time.sleep(0.05)
    arena._unlock(holder)
    for p in procs:
        p.join(60)
        assert p.exitcode == 0
    order = log.read_text(encoding="utf-8").split()
    # the host first; astra was just served, so sol and fable (never served) before astra's other commands;
    # then astra's three in turn (nobody else is waiting)
    assert order == ["host", "sol", "fable", "astra", "astra", "astra"]
    assert not list((a / "host" / "queue").glob("*.t"))   # every ticket taken away
    served = json.loads((a / "host" / "served.json").read_text(encoding="utf-8"))
    assert set(served) == {"astra", "sol", "fable", "host"}


def test_a_waiter_stopped_by_ctrl_c_leaves_no_ticket(tmp_path, monkeypatch):
    a = tmp_path
    holder = arena._lock(a, "opus")
    calls = []

    def stop(_):
        calls.append(1)
        raise KeyboardInterrupt
    monkeypatch.setattr(arena.time, "sleep", stop)
    try:
        arena._lock(a, "sol")
    except KeyboardInterrupt:
        pass
    assert calls and not list((a / "host" / "queue").glob("*.t"))
    arena._unlock(holder)
