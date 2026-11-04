"""+netreply (the architecture thread 2026-10-19 00:37Z; off by default): +reply's played-out opponent turn stops at
that turn's end, where the value net scores it from the opponent's side, instead of going on into the own turn and
being scored by the in-turn linear model. Off, the search and its numbers are as before."""
import gzip
import json
from pathlib import Path

from svsim.core.engine import legal_actions
from svsim.learn import setnet as SN
from svsim.learn.model import SCALE
from svsim.learn.setpolicy import decisions
from svsim.search.evaluate import after_end_of_turn
from svsim.search.mcts import ISMCTS
from svsim.tools.arena import make_agent

ROOT = Path(__file__).resolve().parents[1]
NET = "analysis/scaling/models/net-mid-ramp-t.npz"
REC = ROOT / "analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz"
SPEC = f"mcts-reply:24+plan+learned+phased=pkg-kc-ramp-ramp+setnet={NET}+netmid"


def _states(n):
    with gzip.open(REC, "rt") as fh:
        rec = json.loads(next(fh))
    return [st.clone() for _i, st, *_ in decisions(rec)][:n]


class _Base:
    def score(self, state, player, player_moves_next=False):
        return 777.0


def test_the_opponent_s_turn_end_is_scored_by_the_net_from_the_opponent_s_side():
    net = SN.SetNet.load(ROOT / NET)
    on, off = SN.SetNetEnded(_Base(), net, mid_turn=True, reply_end=True), SN.SetNetEnded(_Base(), net, mid_turn=True)
    for st in _states(8):
        me = st.active
        ended = after_end_of_turn(st)                      # `me` ended the turn: the opponent of 1 - me moves next
        if ended.over:
            continue
        opp = 1 - me
        assert ended.active == opp and on.answers_reply(ended, opp) and not off.answers_reply(ended, opp)
        assert on.score(ended, opp, player_moves_next=True) == -SCALE * net.logit(ended, me)
        assert off.score(ended, opp, player_moves_next=True) == 777.0
        assert on.score(ended, me) == off.score(ended, me)          # everything else as before


class _Spy:
    """Weights that answer every reply, and keep the states scored with the player to move next."""
    def __init__(self):
        self.seen = []

    def answers_reply(self, state, player):
        return True

    def score(self, state, player, player_moves_next=False):
        if player_moves_next:
            self.seen.append((state.players[player].turns_taken, state.active == player))
        return 0.0


def test_the_play_out_stops_at_the_opponent_s_turn_end_only_with_the_switch():
    st = _states(1)[0]
    me = st.active
    taken = st.players[me].turns_taken
    for reply_end, want in ((True, taken), (False, taken + 1)):
        spy = _Spy()
        ISMCTS(iterations=40, seed=1, reply=True, weights=spy, reply_end=reply_end).choose(st.clone())
        assert spy.seen and all(active for _, active in spy.seen)
        assert {t for t, _ in spy.seen} == {want}           # with the switch the own turn has not started


def test_the_agent_option():
    agent = make_agent(SPEC + "+netreply", 0)
    w = agent.base.search.weights if hasattr(agent, "base") else agent.search.weights
    assert isinstance(w, SN.SetNetEnded) and w.reply_end and agent_search(agent).reply_end
    plain = make_agent(SPEC, 0)
    assert not agent_search(plain).reply_end and not agent_search(plain).weights.reply_end
    st = _states(1)[0]
    assert agent.act(st.clone(), legal_actions(st)) is not None


def agent_search(agent):
    from svsim.learn.netdata import _search
    return _search(agent)
