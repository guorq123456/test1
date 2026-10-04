"""Import OCC Top 8 results we do not have from the community OCC results sheet.

Sheet: https://docs.google.com/spreadsheets/d/1CobCsBB-q7t8fOzROVqJguYX9QIKpWb4ccCmMib3CrI (tab "OCC Results"),
which lists every OCC Top 8 bracket match (OCC #1, June 2020, to #54, November 2024) with series scores.
Checked against our Challonge data for #12-#54: 311 matches agree, none with the winner reversed.

Imported (written to data/occ_sheet_matches.csv, loaded like data/manual_matches.csv):
* OCC #1-#11 (2020-06 .. 2021-04), whose brackets are not on Challonge;
* 3rd-place matches the Challonge brackets lack.
Rows without a score (two in OCC #1-#11) are treated as unplayed and skipped.
The sheet gives only the month: Top 8 is dated on the 19th at 13:00 UTC (the median of the 2021-2022 Top 8s),
rounds an hour apart. Names are mapped to existing accounts (exact name, or the account the overlap shows
in that bracket slot); players never seen elsewhere get an "occsheet:" account.

    python3 import_occ_sheet.py   (needs network and openpyxl)
"""
import csv
import io
import os
import re
import urllib.request
from collections import defaultdict

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
URL = "https://docs.google.com/spreadsheets/d/1CobCsBB-q7t8fOzROVqJguYX9QIKpWb4ccCmMib3CrI/export?format=xlsx"
SOURCE = "https://docs.google.com/spreadsheets/d/1CobCsBB-q7t8fOzROVqJguYX9QIKpWb4ccCmMib3CrI (OCC Results)"

# sheet name -> account, where the sheet's English name differs from the platform name (checked on #12-#54)
ACCOUNTS = {
    "Huihui": "bf:5fa3973bf8fc171ea9f68255",          # 辉辉呀
    "Tiger": "bf:673f9e78237e35004096e4c6",           # 老虎不发猫
    "BlueCCG": "bf:5eb62f23aefaaf170fa23f33",         # Blue_Blast (same slots in OCC 2021-07/11/12)
    "Cappuccino": "sgg:2519403",                      # 我开天王炸
    "Artemisia": "sgg:2388207",                       # 百里蒿
    "Head": None, "Noein5": None,                     # exact names
}
# 3rd-place matches missing from the Challonge Top 8 brackets: (sheet tournament, winner, loser)
THIRD_PLACE = {("OCC 15", "Cappuccino", "Noein5"), ("OCC 41", "Head", "Artemisia")}


def month_of(t):
    n = int(re.match(r"OCC (\d+)$", t).group(1))
    k = (2021 * 12 + 4) + (n - 12) if n <= 41 else (2023 * 12 + 10) + (n - 42)  # Ultimates sit between #41 and #42
    return k // 12, k % 12 + 1


def norm(s):
    return re.sub(r"[\s_.\-·]", "", str(s).lower())


def main():
    wb = openpyxl.load_workbook(io.BytesIO(urllib.request.urlopen(URL).read()), data_only=True)
    sheet = []
    for r in wb["OCC Results"].iter_rows(min_row=2, values_only=True):
        # rows without a score (forfeits) are kept so the remaining matches keep their bracket position
        if len(r) > 15 and r[11] and r[12] and r[13] and r[11] != "Tournament":
            sheet.append((str(r[11]), str(r[12]).strip(), str(r[13]).strip(),
                          None if r[14] is None else int(r[14]), None if r[15] is None else int(r[15])))

    by_name = defaultdict(set)
    for p in csv.DictReader(open(os.path.join(DATA, "players.csv"))):
        for n in [p["name"]] + p["aliases"].split(" / "):
            by_name[norm(n)].add(p["player_id"])
    acc_of_pid = {p["player_id"]: p["accounts"].split()[0] for p in csv.DictReader(open(os.path.join(DATA, "players.csv")))}

    def account(name):
        if ACCOUNTS.get(name):
            return ACCOUNTS[name]
        hits = by_name.get(norm(name), set())
        if len(hits) == 1:
            return acc_of_pid[next(iter(hits))]
        return "occsheet:" + norm(name)

    # where the 3rd-place matches go: right after that month's last Challonge Top 8 match
    last = {}
    for r in csv.DictReader(open(os.path.join(DATA, "matches.csv"))):
        if re.search(r"top|final", r["stage"] or "", re.I):
            last[r["event"]] = max(last.get(r["event"], ""), r["time"])

    out = []
    per_event = defaultdict(list)
    for t, w, l, ws, ls in sheet:
        if re.match(r"OCC (\d+)$", t):
            per_event[t].append((w, l, ws, ls))
    for t, ms in per_event.items():
        n = int(t.split()[1])
        y, mo = month_of(t)
        event = f"OCC {y}-{mo:02d}"
        if n <= 11:
            rounds = ["Quarterfinal"] * 4 + ["Semifinal"] * 2 + (["3rd place"] if len(ms) == 8 else []) + ["Final"]
            assert len(ms) in (7, 8), (t, len(ms))
            hour = {"Quarterfinal": 13, "Semifinal": 14, "3rd place": 15, "Final": 16}
            for (w, l, ws, ls), rd in zip(ms, rounds):
                if ws is None:
                    continue  # no score: not played
                out.append((event, rd, f"{y}-{mo:02d}-19T{hour[rd]}:00:00Z", w, l, ws, ls))
        for w, l, ws, ls in ms:
            if (t, w, l) in THIRD_PLACE:
                tm = last[event][:-1].replace("T", " ")
                hh = int(tm[11:13]) + 1
                out.append((event, "3rd place", f"{tm[:10]}T{hh:02d}{tm[13:]}Z", w, l, ws, ls))

    with open(os.path.join(DATA, "occ_sheet_matches.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["event", "stage", "stage_type", "round", "time", "p1", "p1_account", "p2", "p2_account", "s1", "s2", "source"])
        for event, rd, tm, w, l, ws, ls in sorted(out, key=lambda x: x[2]):
            wr.writerow([event, "Top 8", "single elimination", rd, tm, w, account(w), l, account(l), ws, ls, SOURCE])
    new = sorted({a for row in out for a in (account(row[3]), account(row[4])) if a.startswith("occsheet:")})
    print(f"data/occ_sheet_matches.csv: {len(out)} matches, {len(new)} new players: {', '.join(new)}")


if __name__ == "__main__":
    main()
