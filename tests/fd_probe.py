"""Shared by the checkpoint tests: is a file still open in this process when it is replaced? (Windows refuses
os.replace onto a file another handle holds: WinError 5, Codex 2026-10-31; Linux allows it, so the tests look at
/proc/self/fd at the moment of the replace instead.)"""
import os


def open_handles(path) -> int:
    target = os.path.realpath(path)
    n = 0
    for fd in os.listdir("/proc/self/fd"):
        try:
            if os.path.realpath(os.readlink(f"/proc/self/fd/{fd}")) == target:
                n += 1
        except OSError:
            pass
    return n


def watch_replace(monkeypatch) -> list:
    """os.replace that records, for each call, how many handles of this process were open on the destination."""
    real, seen = os.replace, []

    def checked(src, dst, *a, **k):
        seen.append(open_handles(dst))
        return real(src, dst, *a, **k)
    monkeypatch.setattr(os, "replace", checked)
    return seen
