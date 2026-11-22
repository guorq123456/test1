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
        assert "LD-40" in r["error"] and (what in r["error"] or "+1 members" in r["error"]), r["error"]
        assert "worker_exit" not in r and "worker" not in r
    for i in (24, 26):
        r = rows[f"t-{i}"]
        assert r["result"] in ("normal", "draw") and replay_moves(r) == (True, "ok"), r.get("error")


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
