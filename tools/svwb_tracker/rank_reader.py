#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从结算截图里读出段位、MP、本局得分和分组（Windows 专用，用系统自带 OCR）。

存档程序在每局结算时截几张图：shots\\result-<时间>-a/b/c/d.png（a–c 是段位页，d 是最后的汇总页）。
本脚本按 <时间> 分组，逐张识别右半边面板，按文字模式取值，写到 shots\\rank.jsonl，每局一行。

用法（普通 python 运行，不能加 -I，否则找不到用户目录里的 Pillow 和 winocr）：
    python rank_reader.py --shots C:\\claude\\svwb-tracker\\shots

依赖：pip install --user pillow winocr；Windows 需装有中文 OCR 语言包（zh-Hans-CN）。
"""
import argparse
import glob
import json
import os
import re
from collections import defaultdict

from PIL import Image
import winocr

PANEL = (1000, 250, 1900, 1050)   # 1920x1200 截图里右半边面板的大致范围
OCR_LANG = "zh-Hans-CN"

# 段位：拉丁名 → 简体名。顺序要紧：GrandMaster 要先于 Master 匹配。
RANKS = [
    (r"(?:Grand\s*Master|GrandMaster|GM)", "宗师"),
    (r"M?aster", "大师"),
    (r"AA", "AA"),
    (r"A", "A"),
    (r"B", "B"),
    (r"C", "C"),
    (r"D", "D"),
    (r"Beginner", "新手"),
]
# 分组：识别出的繁体（含常见误识）里的特征字 → 简体名。
GROUPS = [
    (("藍", "蓝", "薩"), "蓝宝石"),
    (("紅", "红"), "红宝石"),
    (("鑽", "钻"), "钻石"),
    (("翡", "翠"), "翡翠"),
    (("黃", "黄"), "黄玉"),
]


def ocr_lines(path):
    """返回 [(文字, x, y, w, h)]，坐标换算回整张截图。"""
    im = Image.open(path).convert("RGB").crop(PANEL)
    res = winocr.recognize_pil_sync(im, OCR_LANG)
    out = []
    for ln in res.get("lines", []):
        ws = ln["words"]
        x0 = min(w["bounding_rect"]["x"] for w in ws)
        y0 = min(w["bounding_rect"]["y"] for w in ws)
        x1 = max(w["bounding_rect"]["x"] + w["bounding_rect"]["width"] for w in ws)
        y1 = max(w["bounding_rect"]["y"] + w["bounding_rect"]["height"] for w in ws)
        out.append((ln["text"].replace(" ", ""), x0 + PANEL[0], y0 + PANEL[1], x1 - x0, y1 - y0))
    return out


def parse_frame(lines):
    """从一张图的文字行里取 mp / next / total / rank / level / group / cum_mp，取不到的为 None。"""
    r = dict(mp=None, next=None, total=None, rank=None, level=None, group=None, cum_mp=None)
    texts = [t for t, *_ in lines]
    for t in texts:
        m = re.search(r"(?<!積)MP(\d{3,5})(?!\d)", t)
        if m and r["mp"] is None and "累" not in t:
            r["mp"] = int(m.group(1))
        m = re.search(r"(?:MP|積P)(\d{6,7})(?!\d)", t)  # OCR 有时把「累積MP」读成「累積P」
        if m and r["cum_mp"] is None:
            r["cum_mp"] = int(m.group(1))
        m = re.search(r"NEXT(\d+)", t)
        if m and r["next"] is None:  # 第一个 NEXT 属于段位条，第二个属于 Master 等级条
            r["next"] = int(m.group(1))
        m = re.search(r"獲得MP\+?(\d+)", t)  # 汇总页上的本局得分
        if m:
            r["total"] = int(m.group(1))
        if "等" not in t and "級" not in t and r["rank"] is None:
            for pat, name in RANKS:
                m = re.fullmatch(pat + r"(\d{1,2})", t)
                if m:
                    r["rank"], r["level"] = name, int(m.group(1))
                    break
        if r["group"] is None and ("寶" in t or "宝" in t or "石" in t or "翡" in t or "玉" in t):
            for chars, name in GROUPS:
                if any(c in t for c in chars):
                    r["group"] = name
                    break
    # 段位页上本局得分（TOTAL 行）是 MP 那一行上方、最靠下的那个 ±数字；
    # TOTAL 标签本身常被识别漏，所以按位置找，不靠标签。
    if r["total"] is None and r["mp"] is not None:
        mp_y = next(y for t, x, y, w, h in lines if re.search(r"MP%d" % r["mp"], t))
        cands = [(y, t) for t, x, y, w, h in lines
                 if x > 1650 and y < mp_y - 20 and re.fullmatch(r"[+\-－]\d{1,4}", t)]
        if cands:
            t = max(cands)[1]
            r["total"] = (-1 if t[0] in "-－" else 1) * int(t[1:])
    return r


def read_result(frames):
    parsed = []
    for f in sorted(frames):
        lines = ocr_lines(f)
        # 对战通行证页、宝箱页上也有 TOTAL 和数字，但跟段位无关：只用读得到 MP 的帧
        p = parse_frame(lines)
        if p["mp"] is not None:
            parsed.append((f, lines, p))
    # MP 计数动画可能还没走完：取最大的那一帧，NEXT、累积 MP 也取自同一帧
    best = max(parsed, key=lambda p: p[2]["mp"]) if parsed else None
    out = dict(rank=None, level=None, mp=None, next=None, total=None, group=None, cum_mp=None)
    if best:
        out["mp"], out["next"] = best[2]["mp"], best[2]["next"]
        out["cum_mp"] = best[2]["cum_mp"]
        if out["cum_mp"] is None:  # 这一帧累积 MP 没读出来：用别的帧补，加上两帧之间 MP 的差
            for _, _, p in parsed:
                if p["cum_mp"] is not None:
                    out["cum_mp"] = p["cum_mp"] + out["mp"] - p["mp"]
                    break
    for key in ("rank", "level", "total", "group"):
        for _, _, p in parsed:
            if p[key] is not None:
                out[key] = p[key]
                break
    out["frames_used"] = len(parsed)
    out["ok"] = out["mp"] is not None and out["total"] is not None and out["rank"] is not None
    out["raw"] = (" ".join(t for t, *_ in best[1]))[:200] if best else ""
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shots", default=r"C:\claude\svwb-tracker\shots")
    ap.add_argument("--out", default=None, help="默认写到 <shots>\\rank.jsonl")
    a = ap.parse_args()
    groups = defaultdict(list)
    for f in glob.glob(os.path.join(a.shots, "result-*.png")):
        m = re.match(r"result-(\d{8}-\d{6})-", os.path.basename(f))
        if m:
            groups[m.group(1)].append(f)
    out_path = a.out or os.path.join(a.shots, "rank.jsonl")
    with open(out_path, "w", encoding="utf-8") as fo:
        for ts in sorted(groups):
            rec = dict(ts=ts)
            rec.update(read_result(groups[ts]))
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("wrote %d results to %s" % (len(groups), out_path))


if __name__ == "__main__":
    main()
