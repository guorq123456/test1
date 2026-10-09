"""Run a tool by Salem's rules for his computer (2026-10-09): at most 12 processes in all, never on CPU0, below
normal priority.

    python -m svsim.tools.host <module> [its arguments...]      e.g. python -m svsim.tools.host svsim.tools.gate ...

`limit()` puts this process below normal priority and off CPU0 (Linux: nice 10 and the affinity; Windows: the
below-normal priority class and the affinity mask, through the system's own calls, no dependency). Worker
processes started afterwards (multiprocessing) inherit both. The launcher then caps the tool's --workers at
MAX_WORKERS (and at the CPUs left) and runs the module as `python -m` would. Every tool's own default is 4 workers
or fewer already.
"""
from __future__ import annotations

import os
import runpy
import sys

MAX_WORKERS = 12


def _windows_limit(skip_cpu0: bool, low_priority: bool) -> int:
    import ctypes
    kernel = ctypes.windll.kernel32
    handle = kernel.GetCurrentProcess()
    if low_priority:
        kernel.SetPriorityClass(handle, 0x00004000)           # BELOW_NORMAL_PRIORITY_CLASS
    process, system = ctypes.c_size_t(), ctypes.c_size_t()
    kernel.GetProcessAffinityMask(handle, ctypes.byref(process), ctypes.byref(system))
    mask = process.value
    if skip_cpu0 and mask & ~1:
        mask &= ~1
        kernel.SetProcessAffinityMask(handle, ctypes.c_size_t(mask))
    return bin(mask).count("1")


def limit(skip_cpu0: bool = True, low_priority: bool = True) -> int:
    """Below normal priority and off CPU0 for this process and the ones it starts; the CPUs left."""
    if os.name == "nt":
        return _windows_limit(skip_cpu0, low_priority)
    if low_priority and hasattr(os, "nice"):
        try:
            os.nice(10)
        except OSError:
            pass
    if hasattr(os, "sched_getaffinity"):
        cpus = set(os.sched_getaffinity(0))
        if skip_cpu0 and len(cpus) > 1 and 0 in cpus:
            cpus.discard(0)
            os.sched_setaffinity(0, cpus)
        return len(cpus)
    return os.cpu_count() or 1


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
    cpus = limit()
    capped = cap_workers(args, cpus)
    if capped != args:
        print(f"host: --workers capped at {workers(10 ** 6, cpus)} ({cpus} CPUs off CPU0)", file=sys.stderr)
    sys.argv = [module] + capped
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
