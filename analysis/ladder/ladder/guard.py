"""What a game in a worker may do to the computer (eighteenth pass, LD-52): an audit hook in every runner worker.

The code reader (ladder/codecheck.py) keeps files, processes and the network out of a strategy's reach, and the
tripwire (ladder/watch.py) catches what a game leaves changed in the worker. Neither sees the computer itself: the
seventeenth pass found a pathlib object a strategy could import (ladder.base.ROOT) whose methods renamed, deleted,
made and listed folders on Salem's computer during a formal game, and nothing in the workers would have noticed.

So each worker, once it is set up, adds this hook (sys.addaudithook: it can't be taken off again). While a job runs
(a game, a puzzle answer, a resumed game; `begin` .. `end`), it refuses, with PermissionError, and writes down:
- writing, making, renaming, deleting a file or folder, changing its mode, owner, times or links, the working folder;
- starting a process or a thread, signals, the network, ctypes, the Windows registry and API, memory maps;
- the interpreter's tracing, frames of other threads, the garbage collector's object lists, building code objects
  or functions from parts, adding another audit hook;
- reading a file, or listing a folder, outside: the repository (the simulator, the host's code, the pilots' nets;
  nothing a player can't read anyway), the Python installation (standard library, site-packages), the folders on
  sys.path (listing only: the import machinery looks through them), and the job's own strategy modules (their
  .py and cached .pyc: imports, tracebacks). Another player's code, the pool's logs, the deal key, the arena's
  host files are all outside.
Anything refused during a job voids it, like a tripwire change, and the worker is replaced (runner._worker); the
reason names whose clock was on. The host's own code in a game does none of these (measured: LD-52 in LEDGER).

Cost: CPython calls the hook for every audited event, builtins.id (copy.deepcopy's memo) above all; that path is
the first test in the hook.
"""
from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent              # analysis/ladder/ladder
ROOT = HERE.parents[2]                              # the repository

BLOCK = frozenset({
    # files and folders: changes
    "os.chdir", "os.chflags", "os.chmod", "os.chown", "os.link", "os.mkdir", "os.remove", "os.rename", "os.rmdir",
    "os.symlink", "os.truncate", "os.utime", "os.setxattr", "os.removexattr", "os.getxattr", "os.listxattr",
    "os.lockf", "os.listdrives", "os.listmounts", "os.listvolumes", "os.mkfifo", "os.mknod",
    "tempfile.mkstemp", "tempfile.mkdtemp", "mmap.__new__", "setopencode",
    # processes, threads, signals, the environment
    "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile", "os.startfile/2", "os.fork", "os.forkpty",
    "os.kill", "os.killpg", "os.putenv", "os.unsetenv", "subprocess.Popen", "_posixsubprocess.fork_exec",
    "pty.spawn", "signal.pthread_kill", "resource.setrlimit", "resource.prlimit", "_thread.start_new_thread",
    "_thread.start_joinable_thread", "webbrowser.open",
    # the interpreter
    "sys.settrace", "sys.setprofile", "sys._current_frames", "sys._current_exceptions", "sys.addaudithook",
    "sys.monitoring.register_callback", "sys.remote_exec", "gc.get_objects", "gc.get_referrers",
    "gc.get_referents", "code.__new__", "function.__new__", "builtins.input", "builtins.breakpoint", "pdb.Pdb",
    "cpython.run_command", "cpython.run_file", "cpython.run_module", "cpython.run_stdin", "cpython.run_startup",
    "cpython.run_interactivehook",
})
BLOCK_PREFIX = ("shutil.", "socket.", "ctypes.", "winreg.", "_winapi.", "msvcrt.", "_wmi.", "urllib.", "http.",
                "ftplib.", "smtplib.", "poplib.", "imaplib.", "nntplib.", "telnetlib.", "sqlite3.", "syslog.",
                "fcntl.", "os.add_dll_directory")
LISTING = frozenset({"os.listdir", "os.scandir"})   # os.walk, glob, pathlib's glob go through these
CODE = (".py", ".pyc")

_on = [False]                                      # a job is running
_seen: list = []                                   # what was refused during it
_beat = [None]                                     # the runner's shared [what, since]: whose clock was on
_job_files: set = set()                            # the job's strategy modules (normalised paths)
_read_roots: tuple = ()
_list_dirs: frozenset = frozenset()
_installed = [False]


def _norm(p) -> str | None:
    try:
        return os.path.normcase(os.path.realpath(os.fsdecode(p)))
    except Exception:  # noqa: BLE001 - a path that can't be read as one is refused
        return None


def _under(q: str, roots) -> bool:
    return any(q == r or q.startswith(r.rstrip(os.sep) + os.sep) for r in roots)


def _roots() -> tuple:
    """The repository and the Python installation (its site-packages and the user's, and where numpy is: the one
    package outside the standard library strategies may use), never a folder that holds the host's or the players'
    files (a filesystem root, the home folder, or a parent of the repository)."""
    import site
    cands = {ROOT, *(sysconfig.get_paths().get(k) for k in ("stdlib", "platstdlib", "purelib", "platlib")),
             sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}
    try:
        cands.update(site.getsitepackages() + [site.getusersitepackages()])
    except Exception:  # noqa: BLE001 - a virtual environment's site may lack them
        pass
    np = sys.modules.get("numpy")
    if getattr(np, "__file__", None):
        cands.add(os.path.dirname(os.path.dirname(np.__file__)))
    too_wide = {_norm(Path.home()), _norm(Path.home().anchor)} | {_norm(p) for p in ROOT.parents}
    out = []
    for c in cands:
        q = _norm(c) if c else None
        if q and q not in too_wide and os.path.dirname(q) != q:
            out.append(q)
    return tuple(sorted(set(out)))


def _who() -> str:
    b = _beat[0]
    if b is None:
        return ""
    what, since = int(b[0]), int(b[1])
    if what in (0, 1) and since:
        return f"seat {what}'s decision: "
    if what in (2, 3) and since:
        return f"seat {what - 2}'s guess: "
    if what == -2 and since:
        return "loading the strategies: "
    return "off the strategies' clocks: "


def _refuse(what: str):
    _seen.append(_who() + what)
    raise PermissionError(13, "not allowed in a game (LD-52)", what)


def _readable(q: str) -> bool:
    if q in _job_files:
        return True
    d, name = os.path.split(q)
    if os.path.basename(d) == "__pycache__" and name.endswith(".pyc"):
        src = os.path.join(os.path.dirname(d), name.split(".")[0] + ".py")
        if src in _job_files:
            return True
    return _under(q, _read_roots)


def _hook(event, args):
    if event == "builtins.id" or not _on[0]:
        return
    if event == "open":
        p, mode, flags = (tuple(args) + (None, None, None))[:3]
        if isinstance(p, int):
            return                                  # an already open descriptor
        if isinstance(p, str) and p.startswith("<") and p.endswith(">") and "/" not in p and "\\" not in p:
            raise FileNotFoundError(2, "no such file", p)   # 3.13 formatting a traceback opens '<unknown>'
        writing = (mode is not None and any(m in str(mode) for m in "wax+")) or \
            (mode is None and isinstance(flags, int)
             and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
        q = _norm(p)
        if writing or q is None or not _readable(q):
            _refuse(f"open {os.fsdecode(p) if isinstance(p, (str, bytes)) else p!r} {mode or flags}")
        return
    if event in LISTING:
        p = args[0] if args else None
        if isinstance(p, int):
            return                                  # a descriptor: its opening was checked
        q = _norm(p if p is not None else ".")
        if q is None or not (q in _list_dirs or _under(q, _read_roots)):
            _refuse(f"{event} {p!r}")
        return
    if event in BLOCK or event.startswith(BLOCK_PREFIX):
        _refuse(event)


def install() -> None:
    """Once per worker, after it is set up (its imports, the warm-up game, the tripwire's snapshot)."""
    global _read_roots, _list_dirs
    if _installed[0]:
        return
    sys.dont_write_bytecode = True                  # an import during a game must not write a .pyc
    _read_roots = _roots()
    _list_dirs = frozenset(q for q in (_norm(x or ".") for x in sys.path) if q)
    sys.addaudithook(_hook)
    _installed[0] = True


def _module_file(spec: str) -> str | None:
    if not spec.startswith("py:"):
        return None
    import importlib.util
    try:
        s = importlib.util.find_spec(spec.split(":")[1])
    except Exception:  # noqa: BLE001 - loading it fails later, in the game, as it did before
        return None
    return _norm(s.origin) if s is not None and s.origin and s.has_location else None


def begin(job: dict | None = None, beat=None, specs=()) -> None:
    """A job starts: its strategy modules may be read (found here, before the hook is on)."""
    _seen.clear()
    _job_files.clear()
    for spec in list((job or {}).get("strategies") or []) + list(specs):
        f = _module_file(spec) if isinstance(spec, str) else None
        if f:
            _job_files.add(f)
    _beat[0] = beat
    _on[0] = _installed[0]


def end() -> list:
    """The job is over: what was refused during it, each once with how many times (empty: nothing)."""
    _on[0] = False
    _beat[0] = None
    counts: dict = {}
    for what in _seen:
        counts[what] = counts.get(what, 0) + 1
    _seen.clear()
    return [w if n == 1 else f"{w} (x{n})" for w, n in counts.items()]
