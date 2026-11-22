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
    # a replay or a submission check plays in the host's process: Ctrl+C there is not the strategy's crash (LD-37)
    with pytest.raises(KeyboardInterrupt):
        runner.play_job(job(17, "py:helpers:Interrupts", "py:helpers:Random", first=1))
