"""The resource-flow planner with allied countdown amulets that hit the enemy leader (search.combo tickers, opt-in:
plan(..., tickers=True), the agent's +tick / +lethal2): measured from the engine, not per card; the plain planner
unchanged."""
from svsim.cards import demo, sword
from svsim.search import combo
from svsim.tools.puzzles import play, puzzles

BANK = {name: build for name, build, _ in puzzles()}


def test_tickers_and_summons_are_measured_from_the_engine():
    assert combo.ticker_profile(sword.DREAD_PIRATES_FLAG) == combo.Ticker(spell=1, follower=0, amulet=0, pop=2)
    assert combo.ticker_profile(demo.TOTEM) is None                    # a countdown, but harmless to the leader
    assert combo.ticker_profile(sword.GILDED_BLADE) is None            # not an amulet
    flag = (sword.DREAD_PIRATES_FLAG.card_id, sword.DREAD_PIRATES_FLAG.countdown)
    assert combo.summons(sword.ROUGHWATER_FIRST_MATE) == (flag,)
    assert combo.evolve_summons(sword.ROUGHWATER_FIRST_MATE, True) == (flag,)
    assert combo.summons(demo.FOOTMAN) == ()


def test_the_flag_lethal_is_planned_and_checked_in_the_engine_and_the_setup_has_none():
    st = BANK["pirate-flags-lethal"](1)
    assert combo.tickers_of(st) == ((2, flag_id()), (5, flag_id()), (5, flag_id()))
    assert combo.plan(st, 20000).damage < 10                           # the plain model can't see it
    p = combo.plan(st, 20000, tickers=True)
    assert p.tickers and p.damage >= 10
    line = combo.realize(st, p.steps, face_first=True)
    assert line is not None and combo.verify(st, line)
    st = BANK["pirate-flags-setup"](1)
    p = combo.plan(st, 20000, tickers=True)
    line = combo.realize(st, p.steps, face_first=True) if p.damage >= st.players[1].leader_hp else None
    assert not (line and combo.verify(st, line))


def flag_id():
    return sword.DREAD_PIRATES_FLAG.card_id


def test_without_tickers_on_the_field_the_plan_is_the_plain_one():
    from helpers import give, put, set_pp, start
    s = start()
    put(s, 0, demo.LANCER)
    give(s, 0, demo.RAIDER)
    set_pp(s, 0, 3)
    a, b = combo.plan(s, 2000), combo.plan(s, 2000, tickers=True)
    assert (a.damage, a.steps, a.nodes) == (b.damage, b.steps, b.nodes) and not b.tickers


def test_the_agent_solves_the_flag_lethal_with_the_flags_on_and_lethal2_sets_its_screen():
    from svsim.tools.arena import make_agent
    for spec in ("level-strong+tick", "level-strong+lethal2"):
        end, me, _ = play(BANK["pirate-flags-lethal"], spec, 1)
        assert end.winner == me, spec
    end, me, _ = play(BANK["pirate-flags-lethal"], "level-strong", 1)
    assert end.winner != me                                            # the scoreboard's point: today it fails
    agent = make_agent("level-strong+lethal2", 0)
    assert agent.tickers and agent.search.max_nodes == 3000 and agent.search.near == (2000, 4)
    assert not make_agent("level-strong", 0).tickers
