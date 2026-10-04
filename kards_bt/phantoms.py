"""Tell series that were really played apart from results that were never played.

Organisers record no-shows, drops and disqualifications as ordinary-looking results
(a 0-3 entered seconds after the round opened, Battlefy's automatic 2-0 when one side
never readies, start.gg sets reported without game counts). Those carry no information
about skill, on either side, so the whole match is voided.

Principles (from the audits and from the players who know the scene):
* Every match gets its own verdict. A player who drops keeps the results they played
  before dropping; nothing looks at a player's win/loss record. Swiss and round-robin
  records like 2-4 or 3-3 are normal, and loss caps only exist in elimination brackets.
* Speed alone never voids a scored result between two players who were present: elimination
  matches are often arranged and played before the platform opens them, and organisers enter
  played results in batches. Timing only corroborates independent evidence that someone was
  absent (an organiser DQ/drop tag, a platform no-show flag, a missing ready-check, a player
  who never plays again).

Each verdict function returns None for a playable result, or a short reason string. Battlefy can
also return "real" for a match the platform flagged but that was demonstrably played.
"""
import re
from collections import defaultdict
from datetime import datetime, timezone

PLACEHOLDER = re.compile(r"^(bye(\d+| [a-z])?|cpu\b.*)$", re.I)
TAG = re.compile(r"\s*[\(\[](dq|cn)[\)\]]\s*", re.I)
NO_SHOW_TAG = re.compile(r"[\(\[]\s*(dq|dq'?d|disqualified|dropped|drop|no[ -]?show|forfeit(?:ed)?|ff|w/?o|withdrawn?)\s*[\)\]]",
                         re.I)
GAME_MIN = 3.0       # minutes per game the winner needed; played Bo3/Bo5 never ran faster than 4.1 min/game
BURST_MIN = 3.0      # two of one player's results this close together cannot both have been played
REWRITE_WINDOW = 5.0  # minutes around an organiser's DQ tag in which earlier results were rewritten as 0-3
NOSHOW_TIMER = (9.5, 10.5)  # Battlefy awards the readied side 2-0 ten minutes after its ready-check
PLAYED_MIN = 10.0    # a Bo3 needs at least this long after both players were ready
NOSHOW_GAME_MIN = 4.0  # swiss shutouts faster than this per game, by a loser who then disappears


def _t(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, timezone.utc)
    t = datetime.fromisoformat(v.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _min(a, b):
    return (b - a).total_seconds() / 60 if a and b else None


def series_score(scores_csv):
    """Challonge '2-1' (series) or '1-0,0-1,1-0' (per game) -> (2, 1); unparseable -> (None, None)."""
    s1 = s2 = 0
    for part in (scores_csv or "").split(","):
        m = re.match(r"^\s*(-?\d+)-(-?\d+)\s*$", part)
        if not m:
            return None, None
        a, b = int(m.group(1)), int(m.group(2))
        if "," in scores_csv:
            s1, s2 = s1 + (a > b), s2 + (b > a)
        else:
            s1, s2 = a, b
    return s1, s2


def _display(p):
    return (p or {}).get("display_name") or (p or {}).get("name") or ""


def is_placeholder(p):
    return bool(PLACEHOLDER.match(TAG.sub("", _display(p)).strip()))


# --- Challonge -------------------------------------------------------------------------------------

def challonge_verdicts(t):
    """{match id: reason} for every complete Challonge match that was not a played series."""
    part = {}
    for p in (x["participant"] for x in t.get("participants", [])):
        for pid in [p["id"]] + list(p.get("group_player_ids") or []):
            part[pid] = p
    matches = [x["match"] for x in t.get("matches", [])]
    done = sorted((m for m in matches if m.get("state") == "complete" and m.get("player1_id")
                   and m.get("player2_id") and m.get("completed_at")), key=lambda m: _t(m["completed_at"]))
    swiss = t.get("tournament_type") == "swiss"
    round_open = defaultdict(lambda: None)
    for m in matches:
        if m.get("started_at"):
            key = (m.get("group_id"), m.get("round"))
            st = _t(m["started_at"])
            round_open[key] = min(round_open[key], st) if round_open[key] else st

    # when each participant's results were entered, and whether they ever played after a given time
    entered = defaultdict(list)       # participant id -> [(completed, match id)]
    played_until = defaultdict(lambda: None)  # participant id -> latest result with a game won or a win
    ready = {}                        # match id -> when both players were free and the match was open
    last_played = {}
    verdict = {}

    def side(m, n):
        p = part.get(m[f"player{n}_id"])
        return p, (p or {}).get("id")

    for m in done:
        (p1, a), (p2, b) = side(m, 1), side(m, 2)
        end = _t(m["completed_at"])
        opened = _t(m.get("started_at") or m.get("underway_at") or t.get("started_at"))
        ready[m["id"]] = max([x for x in (opened, last_played.get(a), last_played.get(b)) if x], default=None)
        if p1 and p2 and not is_placeholder(p1) and not is_placeholder(p2):
            entered[a].append((end, m["id"]))
            entered[b].append((end, m["id"]))
            s1, s2 = series_score(m.get("scores_csv"))
            if m.get("winner_id") and not m.get("forfeited") and s1 is not None and (s1, s2) != (0, 0):
                last_played[a] = last_played[b] = end
                for pid, games in ((a, s1), (b, s2)):
                    if games > 0:
                        played_until[pid] = end

    for m in done:
        (p1, a), (p2, b) = side(m, 1), side(m, 2)
        if is_placeholder(p1) or is_placeholder(p2):
            verdict[m["id"]] = "placeholder"
            continue
        if m.get("forfeited"):
            verdict[m["id"]] = "forfeited"
            continue
        s1, s2 = series_score(m.get("scores_csv"))
        winner = 1 if m.get("winner_id") == m["player1_id"] else 2 if m.get("winner_id") == m["player2_id"] else 0
        if s1 is None:
            if winner:
                verdict[m["id"]] = "no_score"
            continue
        if min(s1, s2) < 0:
            verdict[m["id"]] = "negative_score"
            continue
        if s1 == s2 == 0:
            if winner:
                verdict[m["id"]] = "zero_zero"
            continue
        if not winner:
            continue
        loser, lost_games, won_games = (p2, s2, s1) if winner == 1 else (p1, s1, s2)
        if lost_games:
            continue  # the absent side never takes a game
        end = _t(m["completed_at"])
        if loser and NO_SHOW_TAG.search(_display(loser)):
            tagged = _t(loser.get("updated_at"))
            edited = _t(m.get("updated_at"))
            if tagged and end >= tagged:
                verdict[m["id"]] = "dq_after_tag"
            elif tagged and edited and abs(_min(tagged, edited)) <= REWRITE_WINDOW and _min(end, edited) >= 1:
                # an earlier result rewritten as a 0-3 penalty when the player was disqualified:
                # the real outcome is lost, so the match cannot be rated
                verdict[m["id"]] = "dq_rewritten"
            elif ready.get(m["id"]) and 0 <= _min(ready[m["id"]], end) < GAME_MIN * max(won_games, 1):
                verdict[m["id"]] = "dq_instant"
            elif any(mid != m["id"] and abs(_min(x, end)) <= BURST_MIN for x, mid in entered[loser["id"]]):
                verdict[m["id"]] = "dq_burst"
            continue
        # untagged swiss no-show: a shutout too fast to have been played, by a loser who never plays again
        if swiss and loser:
            opened = round_open[(m.get("group_id"), m.get("round"))]
            after = [mid for x, mid in entered[loser["id"]] if x > end]
            gone = not played_until[loser["id"]] or played_until[loser["id"]] < end
            if (opened and _min(opened, end) is not None and _min(opened, end) < NOSHOW_GAME_MIN * max(won_games, 1)
                    and gone and after and all(verdict.get(mid) in ("forfeited", "zero_zero", "no_score")
                                               or _cancelled(matches, mid) for mid in after)):
                verdict[m["id"]] = "swiss_no_show"
    return verdict


def _cancelled(matches, mid):
    m = next((x for x in matches if x["id"] == mid), {})
    s1, s2 = series_score(m.get("scores_csv"))
    return bool(m.get("forfeited")) or (s1, s2) in ((0, 0), (None, None))


# --- start.gg ---------------------------------------------------------------------------------------

def _sgg_scores(st):
    return [(((s.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value") for s in st.get("slots") or []]


def startgg_verdicts(sets):
    """{set id: reason} for one start.gg event's sets."""
    verdict = {}
    info = {}
    for st in sets:
        slots = st.get("slots") or []
        if len(slots) != 2 or any(not s.get("entrant") for s in slots):
            continue
        sc = _sgg_scores(st)
        ents = [s["entrant"]["id"] for s in slots]
        winner = 0 if not st.get("winnerId") else (1 if st["winnerId"] == ents[0] else 2 if st["winnerId"] == ents[1] else 0)
        started, done = _t(st.get("startedAt")), _t(st.get("completedAt"))
        dur = _min(started, done)
        info[st["id"]] = (ents, sc, winner, done, dur)
        if st.get("displayScore") in (None, "DQ"):
            verdict[st["id"]] = "dq"
        elif sc[0] is not None and sc[1] is not None and min(sc) < 0:
            verdict[st["id"]] = "negative_score"
        elif sc[0] is None or sc[1] is None:
            # reported as "A W - B L" without game counts: the no-show convention (WC 2022), unless
            # start.gg timed the set as running for 10+ minutes
            if not (dur is not None and dur >= PLAYED_MIN):
                verdict[st["id"]] = "no_score"

    # admin bursts: an untimed shutout whose loser had other untimed shutout losses entered within
    # minutes and nothing else in between (WC 2021 round robins: absent players cleared in seconds)
    def shutout_loss(sid):
        ents, sc, winner, done, dur = info[sid]
        if not winner or sc[0] is None or sc[1] is None:
            return None
        loser = ents[1] if winner == 1 else ents[0]
        lost_games = sc[1] if winner == 1 else sc[0]
        untimed = dur is None or dur < 2
        return loser if (lost_games == 0 and untimed) else None

    by_loser = defaultdict(list)
    results_of = defaultdict(list)
    for sid, (ents, sc, winner, done, dur) in info.items():
        for e in ents:
            if done:
                results_of[e].append((done, sid))
        lo = shutout_loss(sid)
        if lo is not None and done:
            by_loser[lo].append((done, sid))
    for lo, losses in by_loser.items():
        for done, sid in losses:
            near = [x for x in results_of[lo] if x[1] != sid and abs(_min(x[0], done)) <= BURST_MIN]
            if near and all(shutout_loss(x[1]) == lo for x in near):
                verdict.setdefault(sid, "burst_no_show")

    # a player shown absent (at least two no-show results) who never took a game in the event:
    # their remaining shutout losses are no-shows too
    for e, res in results_of.items():
        flagged = [sid for _, sid in res if verdict.get(sid) in ("burst_no_show", "no_score", "dq")]
        if len(flagged) < 2:
            continue
        took_game = False
        for _, sid in res:
            ents, sc, winner, done, dur = info[sid]
            mine = sc[0] if ents[0] == e else sc[1]
            if (mine or 0) > 0 or (winner and ents[winner - 1] == e and sid not in flagged):
                took_game = True
        if not took_game:
            for _, sid in res:
                ents, sc, winner, done, dur = info[sid]
                if winner and ents[winner - 1] != e and sid not in verdict:
                    verdict[sid] = "absent_player"
    return verdict


# --- Battlefy ---------------------------------------------------------------------------------------

def battlefy_verdict(m):
    """Reason the match was not played, "real" for a flagged match that was played, or None."""
    top, bot = m.get("top") or {}, m.get("bottom") or {}
    if m.get("doubleLoss"):
        return "double_loss"
    win, lose = (top, bot) if top.get("winner") else (bot, top) if bot.get("winner") else (None, None)
    if win is None:
        return "no_winner"
    settled = _t(m.get("updatedAt"))
    rw, rl = _t(win.get("readyAt")), _t(lose.get("readyAt"))
    dq = win.get("disqualified") or lose.get("disqualified")
    if not dq:
        # Battlefy's no-show timer: only the winner readied, the loser took no game, settled 10 min later
        gap = _min(rw, settled)
        if rw and not rl and not lose.get("score") and gap is not None and NOSHOW_TIMER[0] <= gap <= NOSHOW_TIMER[1]:
            return "no_show_timer"
        return None
    # Battlefy puts the DQ flag on a dropped player's LAST match, even when that match was played
    dq_side = win if win.get("disqualified") else lose
    if dq_side is win or (dq_side.get("score") or 0) > 0:
        return "real"  # the DQ'd side won the match or took a game: it was played (some brackets record no ready times)
    if rw and rl:
        later = max(rw, rl)
        if dq_side is win or (dq_side.get("score") or 0) > 0 or (_min(later, settled) or 0) >= PLAYED_MIN:
            return "real"
        return "dq"
    if dq_side.get("readyAt") and dq_side is lose and (_min(_t(dq_side["readyAt"]), settled) or 0) >= PLAYED_MIN:
        return "real"  # the DQ'd side readied and lost at a normal pace; the winner just never pressed ready
    return "dq"
