"""Every test starts from the same import paths. The tools put the received code where workers import it (sys.path and
LADDER_EXTRA_PATH: submit, gate, anchors, the arena), and in production one command is one process with one ledger,
so a module name (sub_S0001, arena_jia_<hash>) means one file. In one pytest process many temporary ledgers reuse those
names; without this, a later test's workers could import an earlier test's sub_S0001 (11-23: the compute-cap test got
the previous test's class)."""
import os
import sys

import pytest


@pytest.fixture(autouse=True)
def _strategy_paths_per_test():
    path, extra = list(sys.path), os.environ.get("LADDER_EXTRA_PATH")
    before = set(sys.modules)
    yield
    sys.path[:] = path
    if extra is None:
        os.environ.pop("LADDER_EXTRA_PATH", None)
    else:
        os.environ["LADDER_EXTRA_PATH"] = extra
    for name in set(sys.modules) - before:
        if name.startswith(("sub_", "arena_")):
            del sys.modules[name]
