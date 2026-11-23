"""The batch runner (phase 1, item 1.3): results by the rules, logs that replay, resuming.
Seeds 99001200-99001299 (host probe bank, SEEDS.md)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import os  # noqa: E402
import subprocess  # noqa: E402
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import runner  # noqa: E402
from ladder.replay import replay_decisions, replay_moves  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def job(i, s0, s1, a=1, b=4, first=None):
    return {"id": f"t-{i}", "seed": 99001200 + i, "first": first, "decks": [CODES[a], CODES[b]],
            "strategies": [s0, s1], "strategy_seeds": [i * 2 + 1, i * 2 + 2], "labels": {"test": True}}


@pytest.fixture(scope="module")
def log_path(tmp_path_factory):
    return tmp_path_factory.mktemp("runs") / "games.jsonl"


@pytest.fixture(scope="module")
def logs(log_path):
    out = log_path
    jobs = [job(0, "bot:greedy+plan", "bot:greedy+plan"),
            job(1, "bot:mcts:100+plan", "py:helpers:Random", first=0),
            job(2, "py:helpers:Random", "py:helpers:Crash"),
            job(3, "py:helpers:Illegal", "py:helpers:Random", first=0),
            job(4, "py:helpers:Random", "py:helpers:Slow", first=0),
            job(5, "py:helpers:Random", "py:helpers:Random", a=2, b=6)]
    summary = runner.run(jobs, str(out), workers=3, step_limit=5.0, quiet=True)
    assert summary["played"] == 6
    rows = {r["id"]: r for r in map(json.loads, out.read_text().splitlines())}
    again = runner.run(jobs, str(out), workers=2, step_limit=5.0, quiet=True)        # resume: nothing to do
    assert again["played"] == 0 and again["skipped"] == 6
    return rows


def test_results_follow_the_rules(logs):
    assert logs["t-0"]["result"] in ("normal", "draw")
    assert logs["t-2"]["result"] == "crash" and logs["t-2"]["loser"] == 1 and logs["t-2"]["winner"] == 0
    assert logs["t-3"]["result"] == "illegal" and logs["t-3"]["loser"] == 0
    assert logs["t-4"]["result"] == "timeout" and logs["t-4"]["loser"] == 1


def test_logs_carry_what_a_replay_needs(logs):
    r = logs["t-1"]
    for key in ("seed", "first", "decks", "strategies", "strategy_seeds", "actions", "steps", "cpu_unit",
                "provenance", "out_of_guess", "turns"):
        assert key in r, key
    assert len(r["steps"]) == len(r["actions"])
    assert r["provenance"]["python"]


@pytest.mark.parametrize("gid", ["t-0", "t-1", "t-2", "t-5"])
def test_moves_replay(logs, gid):
    ok, why = replay_moves(logs[gid])
    assert ok, why


@pytest.mark.parametrize("gid", ["t-0", "t-1", "t-5"])
def test_decisions_replay(logs, gid):
    ok, why = replay_decisions(logs[gid])
    assert ok, why


def test_replay_in_a_fresh_process(logs, log_path):
    """The replay tool alone, in a new interpreter (no search ever ran there): every logged game must replay.
    This is what caught the missing card scripts (ENVIRONMENT 9.4)."""
    r = subprocess.run([sys.executable, "-m", "ladder.replay", str(log_path)], cwd=HERE.parent,
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout.strip().splitlines()[-1]) == {"checked": 6, "failed": 0}


def test_every_card_script_is_loaded_in_a_fresh_process():
    """Importing the ladder package alone registers every class's card scripts: no baseline card plays as vanilla."""
    code = ("import sys; sys.path[:0] = [%r, %r]\n"
            "from ladder import runner, base\n"
            "codes = [l.strip().split('|')[1] for l in open(%r, encoding='utf-8') if l.strip() and l[0] != '#']\n"
            "print(sum(len(runner.unscripted(runner.load_deck(c))) for c in codes))\n"
            % (str(HERE.parent), str(ROOT), str(ROOT / "analysis/pilot/fields/bot-frozen7.txt")))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "0"


def test_a_deck_with_an_unscripted_card_is_void():
    from svsim.cards.pool import POOL
    from svsim.core.script import has_script
    no_script = next(c.card_id for c in POOL.values() if c.has_ability and not has_script(c.card_id))
    deck = [no_script] + [c.card_id for c in runner.load_deck(CODES[1])][1:]
    res = runner.play_job({"id": "t-v", "seed": 99001206, "decks": [deck, CODES[4]],
                           "strategies": ["py:helpers:Random", "py:helpers:Random"], "strategy_seeds": [1, 2]})
    assert res["result"] == "void" and "no script" in res["error"]


def test_compute_comparing_runs_need_one_core_type(monkeypatch):
    # Salem S10 (all cores) with A44: on Windows a run that compares per-step compute must give the E-core mask
    import pytest
    from ladder import runner
    assert runner.MAX_WORKERS == 23
    assert runner.one_core_type(None) is None and runner.one_core_type(runner.E_CORES) == "0x3fc3fc"
    monkeypatch.setattr(runner.os, "name", "nt")
    with pytest.raises(SystemExit):
        runner.one_core_type(None)
    assert runner.one_core_type(0x3FC3FC) == "0x3fc3fc"


def test_a_strategy_cannot_end_its_worker_to_void_a_game(tmp_path):
    # LD-36: SystemExit / KeyboardInterrupt raised by a strategy is its crash (task spec 4.2), not a dead worker
    # (which would void the game); one raised in the end-of-game guess leaves the result as it was
    jobs = [job(10, "py:helpers:Quits", "py:helpers:Random", first=0),
            job(11, "py:helpers:Random", "py:helpers:Interrupts", first=0),
            job(12, "py:helpers:QuitsInGuess", "py:helpers:Random", first=0)]
    out = tmp_path / "g.jsonl"
    res = runner.run(jobs, str(out), workers=2, step_limit=5.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text().splitlines())}
    assert res["played"] == 3 and "void" not in res["results"]
    assert rows["t-10"]["result"] == "crash" and rows["t-10"]["loser"] == 0 and "SystemExit" in rows["t-10"]["error"]
    assert rows["t-11"]["result"] == "crash" and rows["t-11"]["loser"] == 1
    assert rows["t-12"]["result"] in ("normal", "draw") and rows["t-12"]["out_of_guess"][0] is None


def test_an_engine_error_outside_a_move_is_a_void_not_a_runner_error(monkeypatch):
    from ladder import base
    real, n = base.public_position, [0]

    def flaky(*a, **kw):
        n[0] += 1
        if n[0] == 5:
            raise IndexError("simulated engine bug")
        return real(*a, **kw)

    monkeypatch.setattr(base, "public_position", flaky)
    r = runner.play_job(job(13, "py:helpers:Random", "py:helpers:Random", first=0))
    assert r["result"] == "void" and r["error"].startswith("engine error outside a move")


def test_the_referee_judges_moves_on_its_own_list(tmp_path):
    # LD-37: appending a move to the list handed over, or returning something whose comparison raises, is an illegal
    # move (a loss), not a pass and not a void; a crash message with line-separator characters stays one log line
    jobs = [job(14, "py:helpers:AppendsIllegal", "py:helpers:Random", first=0),
            job(15, "py:helpers:ReturnsArray", "py:helpers:Random", first=0),
            job(16, "py:helpers:OddMessage", "py:helpers:Random", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=2, step_limit=5.0, quiet=True)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    rows = {r["id"]: r for r in map(json.loads, lines)}
    assert rows["t-14"]["result"] == "illegal" and rows["t-14"]["loser"] == 0
    assert rows["t-15"]["result"] == "illegal" and rows["t-15"]["loser"] == 0
    assert rows["t-16"]["result"] == "crash" and "x\u2028y" in rows["t-16"]["error"]
    assert runner.run(jobs, str(out), workers=2, step_limit=5.0, quiet=True)["played"] == 0    # resume sees all 3


def test_the_hosts_ctrl_c_stops_a_game_played_in_its_own_process():
    # a replay or a submission check plays in the host's process: a real Ctrl+C there stops it (LD-37) and the
    # handler is put back afterwards
    import signal
    before = signal.getsignal(signal.SIGINT)
    with pytest.raises(KeyboardInterrupt):
        runner.play_job(job(17, "py:helpers:HostCtrlC", "py:helpers:Random", first=1))
    assert signal.getsignal(signal.SIGINT) is before


def test_a_strategys_own_keyboard_interrupt_replays_as_its_crash(tmp_path):
    # fourth pass: in the host's process too, a KeyboardInterrupt the strategy raised is its crash, so the crash the
    # runner logged replays decision for decision (a replay, submit's determinism check) instead of stopping the tool
    r = runner.play_job(job(18, "py:helpers:Interrupts", "py:helpers:Random", first=1))
    assert r["result"] == "crash" and r["loser"] == 0
    out = tmp_path / "g.jsonl"
    runner.run([job(18, "py:helpers:Interrupts", "py:helpers:Random", first=1)], str(out), workers=1, quiet=True)
    log = json.loads(out.read_text(encoding="utf-8"))
    assert log["result"] == "crash" and log["loser"] == 0
    assert replay_moves(log) == (True, "ok") and replay_decisions(log) == (True, "ok")


def test_the_strategy_never_holds_the_referees_moves(tmp_path):
    # fourth pass: rewriting a handed move in place (frozen dataclass __init__) is an illegal move, not a pass or a
    # void; a returned object whose comparison never ends is a timeout for its side; a lone surrogate in a crash
    # message doesn't stop the log write
    jobs = [job(19, "py:helpers:Rewrites", "py:helpers:Random", first=0),
            job(20, "py:helpers:HangsWhenJudged", "py:helpers:Random", first=0),
            job(21, "py:helpers:Surrogate", "py:helpers:Random", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=3, step_limit=2.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    assert len(rows) == 3
    assert rows["t-19"]["result"] == "illegal" and rows["t-19"]["loser"] == 0
    assert rows["t-20"]["result"] == "timeout" and rows["t-20"]["loser"] == 0
    assert rows["t-21"]["result"] == "crash" and "lost anyway \ufffd" in rows["t-21"]["error"]


def test_arena_continuations_judge_like_the_runner():
    # fourth pass: the practice arena's continuation games (run in pool workers that don't ignore Ctrl+C) count a
    # strategy's own KeyboardInterrupt as its crash instead of stopping the whole resume run, and hand out copies
    from ladder import arena
    src = runner.play_job(job(22, "py:helpers:Random", "py:helpers:Random", first=0))
    base = {"decks": src["decks"], "seed": src["seed"], "deal": src.get("deal"), "first_arg": src["first_arg"],
            "prefix": src["actions"][:4], "prefix_steps": src["steps"][:4], "cont": None, "strategy_seeds": [1, 2]}
    r = arena._from_position(dict(base, id="c-1", strategies=["py:helpers:Interrupts", "py:helpers:Interrupts"]))
    assert r["result"] == "crash"
    r = arena._from_position(dict(base, id="c-2", strategies=["py:helpers:Rewrites", "py:helpers:Rewrites"]))
    assert r["result"] == "illegal"


def test_a_change_to_the_simulator_voids_the_game_and_replaces_the_worker(tmp_path):
    # LD-40 (fifth pass): strategy code shares its worker with later games. A game after which the shared card
    # definitions or a script class differ is void (the original result kept as voided_result), and the worker is
    # replaced: the next game in the same slot starts from a clean simulator and replays in a fresh process
    jobs = [job(23, "py:helpers:ChangesCards", "py:helpers:Random", first=0),
            job(24, "py:helpers:Random", "py:helpers:Random", first=0),
            job(25, "py:helpers:PatchesScripts", "py:helpers:Random", first=0),
            job(26, "py:helpers:Random", "py:helpers:Random", first=1)]
    out = tmp_path / "g.jsonl"
    res = runner.run(jobs, str(out), workers=1, step_limit=10.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    assert res["played"] == 4 and len(rows) == 4
    for i, what in ((23, "'cost'"), (25, "patched_by_a_strategy")):
        r = rows[f"t-{i}"]
        assert r["result"] == "void" and r["voided_result"] in ("normal", "draw") and r["winner"] is None
        assert "voided_winner" in r
        assert "LD-40" in r["error"] and (what in r["error"] or "+1 members" in r["error"]), r["error"]
        assert "worker_exit" not in r and "worker" not in r
    for i in (24, 26):
        r = rows[f"t-{i}"]
        assert r["result"] in ("normal", "draw") and replay_moves(r) == (True, "ok"), r.get("error")


def test_a_grown_registry_or_a_renamed_class_voids_the_game_too(tmp_path):
    # LD-41 (sixth pass): the tripwire also follows a module global's set (the scripts' listener registries), a
    # class's name and bases, and it sees a change made in a worker's first game (the warm-up game comes before the
    # snapshot)
    jobs = [job(29, "py:helpers:GrowsRegistry", "py:helpers:Random", first=0),
            job(30, "py:helpers:RenamesAMove", "py:helpers:Random", first=0),
            job(31, "py:helpers:Random", "py:helpers:Random", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=10.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    for i, what in ((29, "LISTEN_IN_HAND"), (30, "Evolve")):
        r = rows[f"t-{i}"]
        assert r["result"] == "void" and "voided_result" in r and what in r["error"], r.get("error")
    assert rows["t-31"]["result"] in ("normal", "draw") and replay_moves(rows["t-31"]) == (True, "ok")


def test_the_watch_follows_registries_and_names_and_lets_the_caches_fill_and_empty():
    from ladder import watch
    from svsim.core import script
    from svsim.core.actions import Evolve
    from svsim.search import combo, formula
    watch.preload()
    snap = watch.snapshot()
    assert watch.changes(snap) == []
    script.LISTEN_IN_HAND.add(987654321)
    try:
        assert any("LISTEN_IN_HAND" in line for line in watch.changes(snap))
    finally:
        script.LISTEN_IN_HAND.discard(987654321)
    name = Evolve.__name__
    Evolve.__name__ = "Evolved"
    try:
        assert any("Evolve" in line for line in watch.changes(snap))
    finally:
        Evolve.__name__ = name
    assert watch.changes(snap) == []
    # the memo caches fill up and are emptied at their size limits during a game: no false alarm (LD-41)
    formula._NEXT[("probe",)] = 1
    combo._NEXT_TURN[("probe",)] = 1
    assert watch.changes(snap) == []
    watch.reset_caches(snap)
    assert ("probe",) not in formula._NEXT and ("probe",) not in combo._NEXT_TURN
    assert watch.changes(snap) == []


def test_the_new_snapshot_is_taken_on_the_clock():
    beat, seen = [0, 0], []

    class Watch:
        def snapshot(self):
            seen.append((beat[0], beat[1] != 0))
            return "snap"
    assert runner._resnap(Watch(), beat) == "snap" and seen == [(runner.HOST, True)] and beat[1] == 0


def test_a_hung_guess_or_load_stops_by_the_clock(tmp_path):
    # LD-40: the end-of-game guess is on the step clock (a hang there loses by timeout instead of stalling the run);
    # building the strategies is on a longer clock (a hang there: void, like a strategy that fails to load)
    jobs = [job(27, "py:helpers:HangsInGuess", "py:helpers:Random", first=0),
            job(28, "py:helpers:Random", "py:helpers:HangsOnLoad", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=2, step_limit=1.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    assert rows["t-27"]["result"] == "timeout" and rows["t-27"]["loser"] == 0 and "guess" in rows["t-27"]["error"]
    assert rows["t-28"]["result"] == "void" and "to load" in rows["t-28"]["error"]


def test_guarded_map_keeps_each_task_to_itself():
    # LD-40: puzzles and the arena's resume ask strategies through guarded_map: a hang is stopped by the clock, a dead
    # worker or a raise is that task's alone, and a task that changes the simulator is marked and its worker replaced,
    # so the next task (same slot, one worker) sees the clean definitions again
    got = runner.guarded_map("helpers:task", ["ok", "change", "ok", "hang", "ok", "die", "raise", "ok"], workers=1,
                             step_limit=1.0)
    assert [("value" in g, "changed" in g) for g in got[:3]] == [(True, False), (True, True), (True, False)]
    assert got[0]["value"]["costs"] == got[2]["value"]["costs"] == got[4]["value"]["costs"]
    assert got[1]["value"]["costs"] == got[0]["value"]["costs"] + 1
    assert got[1]["value"]["pid"] != got[2]["value"]["pid"]
    assert got[3]["timeout"] == 1 and got[5] == {"died": 3}
    assert "task failed" in got[6]["error"] and "value" in got[7]


def test_code_left_running_off_the_clock_is_stopped(tmp_path):
    # LD-42: a generator's finally runs when the strategy is freed after the game, on no clock; the idle watchdog
    # ends that worker (the game is void, nobody's loss) and the next game plays in a new one; guarded_map likewise
    jobs = [job(37, "py:helpers:Lingers", "py:helpers:Random", first=0),
            job(38, "py:helpers:Random", "py:helpers:Random", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=5.0, idle_limit=3.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    assert rows["t-37"]["result"] == "void" and "nothing ran on any clock" in rows["t-37"]["error"]
    assert rows["t-38"]["result"] in ("normal", "draw")
    got = runner.guarded_map("helpers:task", ["linger", "ok"], workers=1, step_limit=5.0, idle_limit=3.0)
    assert got[0]["timeout"] == runner.IDLE and "value" in got[1]



def test_copying_the_position_is_not_a_change(tmp_path):
    # LD-43: copy.copy / deepcopy store __slotnames__ in a class the first time one of its objects is copied (ladder.base
    # PublicPosition, GameState, collections.ChainMap...); the snapshot fills that cache first, so copying voids nothing
    jobs = [job(39, "py:helpers:CopiesPosition", "py:helpers:Random", first=0),
            job(40, "py:helpers:Random", "py:helpers:CopiesPosition", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=30.0, quiet=True)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [r["result"] for r in rows] != [] and all(r["result"] in ("normal", "draw") for r in rows), rows

def test_copying_an_iterator_is_not_a_change(tmp_path):
    # LD-44: copying an itertools object warns from copy.py (ignored), and CPython then keeps copy.__warningregistry__;
    # the snapshot makes that registry in every module it follows first and holds it by identity, so nothing is voided
    jobs = [job(41, "py:helpers:CopiesIterators", "py:helpers:Random", first=0),
            job(42, "py:helpers:Random", "py:helpers:CopiesIterators", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=30.0, quiet=True)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2 and all(r["result"] in ("normal", "draw") for r in rows), rows


def test_reading_annotations_is_not_a_change(tmp_path):
    # LD-45: a runtime-checkable Protocol's isinstance and functools.cache(K) read K.__annotations__, which stores an
    # empty one in K; the snapshot reads it first in every class it follows, so nothing is voided
    jobs = [job(43, "py:helpers:ChecksProtocols", "py:helpers:Random", first=0),
            job(44, "py:helpers:Random", "py:helpers:ChecksProtocols", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=30.0, quiet=True)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2 and all(r["result"] in ("normal", "draw") for r in rows), rows


def test_an_abc_registration_voids_the_game_and_numpy_used_plainly_does_not(tmp_path):
    # LD-46: ABCMeta.register changes isinstance for the whole process (typing.Hashable.register(list) broke another
    # player's later games); the tripwire compares the ABC registry's counter. numpy's own Generator, linalg and
    # errstate change nothing process-wide
    jobs = [job(45, "py:helpers:RegistersAbc", "py:helpers:Random", first=0),
            job(46, "py:helpers:UsesNumpy", "py:helpers:Random", first=0),
            job(47, "py:helpers:Random", "py:helpers:UsesNumpy", first=0)]
    out = tmp_path / "g.jsonl"
    runner.run(jobs, str(out), workers=1, step_limit=30.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    assert rows["t-45"]["result"] == "void" and "abc.register" in rows["t-45"]["error"], rows["t-45"]
    assert all(rows[i]["result"] in ("normal", "draw") for i in ("t-46", "t-47")), rows


def test_the_watch_sees_a_dataclass_field_and_numpys_settings():
    # LD-46: @dataclass rewrites a Field it finds as a class attribute in place (one taken from
    # dataclasses.fields(PlayCard) dropped `targets` from every later game); numpy's settings and global RandomState
    # are the whole process's; LD-47: so are the arrays and plain values numpy's modules and classes hold
    import dataclasses

    import numpy

    from ladder import watch
    from svsim.core.actions import PlayCard
    watch.preload()
    snap = watch.snapshot()
    assert watch.changes(snap) == []
    f = next(x for x in dataclasses.fields(PlayCard) if x.name == "targets")
    kept, err, state = f.type, numpy.geterr(), numpy.random.get_state()
    window = numpy.polynomial.Polynomial.window
    was, style = window.copy(), numpy.polynomial.Polynomial._use_unicode
    try:
        f.type = int
        assert any("__dataclass_fields__" in line and "targets" in line for line in watch.changes(snap))
        f.type = kept
        numpy.seterr(all="raise")
        assert any("numpy.geterr" in line for line in watch.changes(snap))
        numpy.seterr(**err)
        numpy.random.seed(5)
        assert any("numpy.random" in line for line in watch.changes(snap))
        numpy.random.set_state(state)
        assert watch.changes(snap) == []
        numpy.copyto(window, [0, 3], casting="unsafe")         # LD-47: numpy's own arrays, written through an out
        assert any("Polynomial.window" in line for line in watch.changes(snap))
        numpy.copyto(window, was)
        numpy.polynomial.set_default_printstyle("ascii" if style else "unicode")
        assert any("_use_unicode" in line for line in watch.changes(snap))
    finally:
        f.type = kept
        numpy.seterr(**err)
        numpy.random.set_state(state)
        numpy.copyto(window, was)
        numpy.polynomial.set_default_printstyle("unicode" if style else "ascii")
    assert watch.changes(snap) == []


def test_the_watch_follows_the_standard_library_and_what_an_lru_cache_wraps():
    # LD-42: random.Random's methods (the deal and the search shuffle with it), a class or function of an allowed
    # standard module, and the function under an lru_cache are followed
    import random
    import statistics

    from ladder import watch
    from svsim.search import combo
    watch.preload()
    snap = watch.snapshot()
    assert watch.changes(snap) == []
    shuffle, code, wrapped = random.Random.shuffle, statistics.median_low.__code__, combo.profile.__wrapped__
    kept = wrapped.__code__

    def other(defn, fused=False):
        return ()
    try:
        random.Random.shuffle = lambda self, x: None
        assert any("random.Random" in line for line in watch.changes(snap))
        random.Random.shuffle = shuffle
        statistics.median_low.__code__ = other.__code__
        assert any("median_low" in line for line in watch.changes(snap))
        statistics.median_low.__code__ = code
        wrapped.__code__ = other.__code__
        assert any("__wrapped__" in line for line in watch.changes(snap))
    finally:
        random.Random.shuffle, statistics.median_low.__code__, wrapped.__code__ = shuffle, code, kept
    assert watch.changes(snap) == []


def test_the_pilots_model_caches_may_grow():
    # LD-42: the host's pilot games load a model once per process (svsim.learn's caches gain an entry) and the net
    # memoizes and adds rows for cards it meets: neither is a change; anything else in the net is
    from ladder import watch
    from svsim.learn import setnet
    watch.preload()
    net = object.__new__(setnet.SetNet)
    net.__dict__.update(slope=0.1, _live_hits=0)
    key = ("test-net-ld42",)
    setnet._CACHE[key] = net
    try:
        snap = watch.snapshot()
        setnet._CACHE[("test-net-ld42", 2)] = object()
        net._live_hits, net._pool, net.card_ids = 5, {1: 2}, [1, 2]
        assert watch.changes(snap) == [] and watch.stale(snap)
        net.slope = 0.2
        assert any("slope" in line for line in watch.changes(snap))
    finally:
        setnet._CACHE.pop(key, None)
        setnet._CACHE.pop(("test-net-ld42", 2), None)


def test_every_module_a_strategy_may_import_is_loaded_before_the_snapshot():
    # LD-42: a module first loaded during a game used to enter the next snapshot with whatever that game did to it
    code = ("import sys; sys.path[:0] = [sys.argv[1], sys.argv[2]]\n"
            "from ladder import watch, codecheck\n"
            "watch.preload(['ladder.puzzles'])\n"
            "import pkgutil, svsim\n"
            "names = [m.name for m in pkgutil.walk_packages(svsim.__path__, 'svsim.')\n"
            "         if codecheck.module_problem(m.name) is None]\n"
            "missing = [n for n in names if n not in sys.modules]\n"
            "snap = watch.snapshot()\n"
            "print(missing, 'ladder.puzzles' in snap.modules, 'statistics' in snap.modules)\n")
    out = subprocess.run([sys.executable, "-c", code, str(HERE.parent), str(HERE.parents[2])], capture_output=True,
                         text=True, timeout=300)
    assert out.stdout.strip() == "[] True True", out.stderr[-2000:]


def test_watch_sees_a_rewritten_definition_and_its_undoing():
    from ladder import watch
    from svsim.cards.pool import POOL
    watch.preload()
    snap = watch.snapshot()
    assert watch.changes(snap) == []
    d = next(iter(POOL.values()))
    cost = d.cost
    object.__setattr__(d, "cost", cost + 7)
    try:
        assert any("'cost'" in line for line in watch.changes(snap))
    finally:
        object.__setattr__(d, "cost", cost)
    assert watch.changes(snap) == []
