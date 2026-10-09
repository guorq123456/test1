"""Run a tool by Salem's rules for his computer (2026-10-09): at most 12 processes in all, never on CPU0, below
normal priority.

    python -m svsim.tools.host <module> [its arguments...]      e.g. python -m svsim.tools.host svsim.tools.gate ...

`limit()` puts this process below normal priority and off CPU0 (Linux: nice 10 and the affinity; Windows: the
below-normal priority class and the affinity mask, through kernel32 with its signatures declared, no
dependency), reads both back and stops (exit 2) if either didn't hold; it prints what it read. This runs in the
interpreter that runs the tool (a venv's python.exe is a launcher that starts the real one: the settings are made
in the real one), before any worker starts, so worker processes (multiprocessing) inherit both. The launcher then
caps the tool's --workers at MAX_WORKERS (and at the CPUs left) and runs the module as `python -m` would. Every tool's own default is 4 workers
or fewer already.
"""
from __future__ import annotations

import os
import runpy
import sys

MAX_WORKERS = 12


BELOW_NORMAL = 0x00004000                         # BELOW_NORMAL_PRIORITY_CLASS


def _kernel32():
    """kernel32 with the signatures declared: without them a 64-bit process handle goes through as a 32-bit int
    and every call fails without a word (RC on Salem's machine, 2026-10-09)."""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.argtypes, k.GetCurrentProcess.restype = [], wintypes.HANDLE
    k.SetPriorityClass.argtypes, k.SetPriorityClass.restype = [wintypes.HANDLE, wintypes.DWORD], wintypes.BOOL
    k.GetPriorityClass.argtypes, k.GetPriorityClass.restype = [wintypes.HANDLE], wintypes.DWORD
    k.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t),
                                         ctypes.POINTER(ctypes.c_size_t)]
    k.GetProcessAffinityMask.restype = wintypes.BOOL
    k.SetProcessAffinityMask.argtypes, k.SetProcessAffinityMask.restype = [wintypes.HANDLE, ctypes.c_size_t], \
        wintypes.BOOL
    return k


def _windows_limit(skip_cpu0: bool, low_priority: bool, kernel=None, last_error=None) -> dict:
    """Set, then read back: {"cpus", "mask", "priority"}; OSError on a failed call, RuntimeError if what reads
    back isn't what was set."""
    import ctypes
    k = kernel if kernel is not None else _kernel32()
    err = last_error if last_error is not None else ctypes.get_last_error
    handle = k.GetCurrentProcess()
    if low_priority and not k.SetPriorityClass(handle, BELOW_NORMAL):
        raise OSError(err(), "SetPriorityClass failed")

    def mask():
        process, system = ctypes.c_size_t(), ctypes.c_size_t()
        if not k.GetProcessAffinityMask(handle, ctypes.byref(process), ctypes.byref(system)):
            raise OSError(err(), "GetProcessAffinityMask failed")
        return process.value
    m = mask()
    if skip_cpu0 and m & ~1 and m & 1:
        if not k.SetProcessAffinityMask(handle, m & ~1):
            raise OSError(err(), "SetProcessAffinityMask failed")
    got, priority = mask(), k.GetPriorityClass(handle)
    if (low_priority and priority != BELOW_NORMAL) or (skip_cpu0 and got & 1 and got & ~1):
        raise RuntimeError(f"the settings didn't hold: priority class {priority:#x}, affinity {got:#x}")
    return {"cpus": bin(got).count("1"), "mask": got, "priority": "below normal" if priority == BELOW_NORMAL
            else f"{priority:#x}"}


def limit(skip_cpu0: bool = True, low_priority: bool = True) -> dict:
    """Below normal priority and off CPU0 for this process and the ones it starts, read back and checked:
    {"cpus": the CPUs left, "mask" or "affinity", "priority"}. Raises if a setting didn't hold."""
    if os.name == "nt":
        return _windows_limit(skip_cpu0, low_priority)
    out = {}
    if low_priority and hasattr(os, "nice"):
        before = os.nice(0)
        after = os.nice(10)
        if after < min(before + 10, 19):
            raise RuntimeError(f"nice didn't hold: {after}")
    out["priority"] = f"nice {os.nice(0)}" if hasattr(os, "nice") else "unchanged"
    if hasattr(os, "sched_getaffinity"):
        cpus = set(os.sched_getaffinity(0))
        if skip_cpu0 and len(cpus) > 1 and 0 in cpus:
            os.sched_setaffinity(0, cpus - {0})
        got = set(os.sched_getaffinity(0))
        if skip_cpu0 and len(got) > 1 and 0 in got:
            raise RuntimeError(f"the affinity didn't hold: {sorted(got)}")
        out.update(cpus=len(got), affinity=sorted(got))
    else:
        out["cpus"] = os.cpu_count() or 1
    return out


def workers(requested: int, cpus: int) -> int:
    """At most MAX_WORKERS, and no more than the CPUs left."""
    return max(1, min(requested, MAX_WORKERS, cpus))


def cap_workers(argv: list, cpus: int) -> list:
    """argv with any --workers N (or --workers=N) capped by `workers`."""
    out, i = list(argv), 0
    while i < len(out):
        a = out[i]
        if a == "--workers" and i + 1 < len(out) and out[i + 1].isdigit():
            out[i + 1] = str(workers(int(out[i + 1]), cpus))
            i += 2
            continue
        if a.startswith("--workers=") and a.split("=", 1)[1].isdigit():
            out[i] = f"--workers={workers(int(a.split('=', 1)[1]), cpus)}"
        i += 1
    return out


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    module, args = sys.argv[1], sys.argv[2:]
    try:
        got = limit()
    except (OSError, RuntimeError) as e:            # never go on silently at normal priority on CPU0
        print(f"host: the limits could not be set: {e}", file=sys.stderr)
        raise SystemExit(2)
    cpus = got["cpus"]
    where = f"mask {got['mask']:#x}" if "mask" in got else f"CPUs {got.get('affinity')}"
    print(f"host: priority {got['priority']}, {where}, {cpus} CPUs", file=sys.stderr)
    capped = cap_workers(args, cpus)
    if capped != args:
        print(f"host: --workers capped at {workers(10 ** 6, cpus)} ({cpus} CPUs off CPU0)", file=sys.stderr)
    sys.argv = [module] + capped
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
