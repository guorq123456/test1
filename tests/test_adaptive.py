"""+adaptive (search.combo verify_steps, opt-in): a planner line whose fixed targets a random effect can break is kept
when the plan, realized again on each sampled outcome, still wins; the agent realizes the rest of the plan again at
every step. Without the flag nothing changes."""
import json
import os
import sys
from pathlib import Path

import pytest

MISSES = Path(__file__).resolve().parents[1] / "analysis" / "speed" / "data" / "ramp_misses.jsonl"


def test_the_flag_reaches_the_agent_and_the_plain_return_is_unchanged():
    from svsim.search import combo
    from svsim.tools.arena import make_agent
    from helpers import start
    a = make_agent("level-strong+lethal3+adaptive", 0)
    assert a.adaptive and a.plan_steps is None
    assert not make_agent("level-strong+lethal3", 0).adaptive
    s = start()
    assert len(combo.planned_lethal(s, 2000)) == 2 and len(combo.planned_lethal(s, 2000, want_plan=True)) == 3


@pytest.mark.skipif(not os.environ.get("SVSIM_STEP1_DIR"), reason="step 1's data not at hand")
def test_ramp_g109_a_random_follower_hit_is_planned_through_and_played_out():
    from svsim.core.engine import apply, legal_actions
    from svsim.search import combo
    from svsim.tools.arena import make_agent
    d = os.environ["SVSIM_STEP1_DIR"]
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    row = next(json.loads(x) for x in open(MISSES) if json.loads(x)["game"] == 109)
    s = SD._state_at(games[109], row["at"])
    kw = dict(tickers=True, fix=True, eot=True)
    assert combo.planned_lethal(s, 20000, **kw)[0] is None
    assert combo.planned_lethal(s, 20000, adaptive=True, **kw)[0]
    for seed in range(4):                          # whatever Sloth hits, the agent plays the plan to the win
        t = s.clone()
        t.rng.seed(1000 + seed)
        agent, me = make_agent("level-strong+lethal3+adaptive", seed), t.active
        while not t.over and t.active == me:
            apply(t, agent.act(t, legal_actions(t)))
        assert t.winner == me
