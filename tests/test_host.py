"""svsim.tools.host: Salem's computer's rules (at most 12 processes, not CPU0, below normal priority)."""
import os
import subprocess
import sys

import pytest


def test_workers_are_capped_at_twelve_and_the_cpus_left():
    from svsim.tools.host import cap_workers, workers
    assert workers(16, 31) == 12 and workers(4, 31) == 4 and workers(8, 3) == 3 and workers(0, 4) == 1
    assert cap_workers(["x", "--workers", "16", "--seed", "16"], 31) == ["x", "--workers", "12", "--seed", "16"]
    assert cap_workers(["--workers=20"], 7) == ["--workers=7"]
    assert cap_workers(["--games", "16"], 31) == ["--games", "16"]


@pytest.mark.skipif(not hasattr(os, "sched_getaffinity") or len(os.sched_getaffinity(0)) < 2,
                    reason="needs Linux affinity and two CPUs")
def test_the_launcher_runs_a_module_off_cpu0_below_normal_priority(tmp_path):
    """The module runs as with python -m, with CPU0 out of its affinity and a higher nice value, inherited by the
    processes it starts."""
    probe = tmp_path / "probe_mod.py"
    probe.write_text(
        "import os, sys\n"
        "from multiprocessing import Pool\n"
        "def f(_):\n"
        "    return sorted(os.sched_getaffinity(0)), os.nice(0)\n"
        "if __name__ == '__main__':\n"
        "    with Pool(2) as p:\n"
        "        kids = p.map(f, range(2))\n"
        "    print(repr((sorted(os.sched_getaffinity(0)), os.nice(0), kids, sys.argv[1:])))\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=f"{tmp_path}{os.pathsep}{os.getcwd()}")
    out = subprocess.run([sys.executable, "-m", "svsim.tools.host", "probe_mod", "--workers", "99", "a"],
                         capture_output=True, text=True, env=env, check=True)
    mine, nice, kids, argv = eval(out.stdout.strip())
    base = os.nice(0)
    assert 0 not in mine and nice == min(base + 10, 19)
    assert all(0 not in k[0] and k[1] == nice for k in kids)
    assert argv == ["--workers", str(min(12, len(mine))), "a"]
