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


class _FakeKernel:
    """kernel32 as far as host._windows_limit uses it: a 20-CPU machine (mask 0xFFFFF)."""

    def __init__(self, set_priority_ok=True, holds=True):
        self.priority, self.mask = 0x20, 0xFFFFF                  # NORMAL_PRIORITY_CLASS
        self.set_priority_ok, self.holds = set_priority_ok, holds
        self.calls = []

    def GetCurrentProcess(self):
        return 0xFFFFFFFFFFFFFFFF                                  # the 64-bit pseudo-handle

    def SetPriorityClass(self, handle, cls):
        self.calls.append(("SetPriorityClass", handle, cls))
        if self.set_priority_ok and self.holds:
            self.priority = cls
        return int(self.set_priority_ok)

    def GetPriorityClass(self, handle):
        return self.priority

    def GetProcessAffinityMask(self, handle, process, system):
        process._obj.value, system._obj.value = self.mask, 0xFFFFF
        return 1

    def SetProcessAffinityMask(self, handle, mask):
        self.calls.append(("SetProcessAffinityMask", handle, mask))
        if self.holds:
            self.mask = mask
        return 1


def test_windows_sets_reads_back_and_never_fails_silently():
    """The settings go through the full 64-bit handle, read back as set (0xFFFFE: all but CPU0, below normal);
    a failed call raises with the error code, and settings that don't hold raise too."""
    from svsim.tools.host import BELOW_NORMAL, _windows_limit
    k = _FakeKernel()
    got = _windows_limit(True, True, kernel=k, last_error=lambda: 5)
    assert got == {"cpus": 19, "mask": 0xFFFFE, "priority": "below normal"}
    assert ("SetPriorityClass", 0xFFFFFFFFFFFFFFFF, BELOW_NORMAL) in k.calls
    assert ("SetProcessAffinityMask", 0xFFFFFFFFFFFFFFFF, 0xFFFFE) in k.calls
    with pytest.raises(OSError) as e:
        _windows_limit(True, True, kernel=_FakeKernel(set_priority_ok=False), last_error=lambda: 6)
    assert e.value.errno == 6
    with pytest.raises(RuntimeError):
        _windows_limit(True, True, kernel=_FakeKernel(holds=False), last_error=lambda: 0)


def test_the_kernel32_signatures_are_declared(monkeypatch):
    """Without argtypes / restype a 64-bit handle is passed as a 32-bit int and the calls fail silently (RC)."""
    import ctypes
    from ctypes import wintypes
    from svsim.tools import host

    class Fn:
        argtypes = restype = None

    class Lib:
        def __getattr__(self, name):
            fn = Fn()
            setattr(self, name, fn)
            return fn
    monkeypatch.setattr(ctypes, "WinDLL", lambda *a, **k: Lib(), raising=False)
    k = host._kernel32()
    assert k.GetCurrentProcess.restype is wintypes.HANDLE
    assert k.SetPriorityClass.argtypes == [wintypes.HANDLE, wintypes.DWORD]
    assert k.GetProcessAffinityMask.argtypes[0] is wintypes.HANDLE
    assert k.SetProcessAffinityMask.argtypes == [wintypes.HANDLE, ctypes.c_size_t]
    assert all(getattr(k, n).restype is not None for n in ("SetPriorityClass", "GetPriorityClass",
                                                          "GetProcessAffinityMask", "SetProcessAffinityMask"))


def test_the_launcher_stops_when_the_limits_cannot_be_set(monkeypatch, capsys):
    from svsim.tools import host

    def broken():
        raise OSError(5, "SetPriorityClass failed")
    monkeypatch.setattr(host, "limit", broken)
    monkeypatch.setattr("sys.argv", ["host", "svsim.tools.nothing"])
    with pytest.raises(SystemExit) as e:
        host.main()
    assert e.value.code == 2 and "could not be set" in capsys.readouterr().err
