"""Host stand-ins for tools/compute_noise.py (LD-57): honest strategies whose cost against the default's changes with
the position, to see the receipt's compute-ratio error for strategies other than the default with another seed.

- Adaptive: the default search, its iterations growing with how far the game is (50 at the start, +4 per card the
  opponent has shown, at most 160): cheap early, dear late, so long games cost more than short ones.
- Overhead: the default plus a fixed piece of pure-Python work before every decision (about 3 ms in the container):
  a large ratio on cheap positions, a small one on dear ones.

Measurement tools only: these say nothing about strength.
"""
from __future__ import annotations

from ladder.interface import PlayerStrategy


class Adaptive(PlayerStrategy):
    def search(self, pos):
        return {"iterations": int(min(160, 50 + 4 * len(pos.opp_log)))}


class Overhead(PlayerStrategy):
    WORK = 40000

    def act(self, pos, actions):
        x = 0
        for i in range(self.WORK):
            x = (x * 31 + i) % 1000003
        self.last_work = x
        return super().act(pos, actions)
