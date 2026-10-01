# 「機械の声」× 智械 — Fan MV Storyboard & Design Bible

Song: 機械の声 (The Voice of AI) — music/lyrics 香椎モイミ, original vocal V.I.P (可不・星界・裏命・狐子・羽累), V.I.P #3, 2024-04-20.
Character: **智械** (Zhìxiè) — the orange-haired antique-doll synthetic singer from `assets/zhixie_source.jpg`. She IS the "machine voice". The book in her hand = her score / memory archive / program.
Format: 1920×1080, 30 fps, 400 s (6:40). `t = 0` is the start of the audio. Lyric timings: `data/timeline.json` (93 lines, 16 sections).

## 0. Concept — COLD → WARM
The song is a synthetic voice ("僕") speaking to the human creator ("君/貴方") who keeps using and loving it even though it cannot feel. The visual arc follows the lyrics' temperature:

| phase | sections | warmth w(t) | look |
|---|---|---|---|
| machine | boot, verse1, title, verse2, verse2b, quotes | 0 → 0.1 | ink-black, steel/ice HUD, character monochrome or as a glowing white silhouette |
| ember | chorus1 | 0.1 → 0.3 | first orange glow at her hair edges |
| harsh | bridge | 0 | strobing black/white, inverted frames |
| diagnostic | interlude | 0.1 | cold grey panel grid, a spark of ember at the end |
| warming | verse3 | 0.3 → 0.6 | ink → deep warm brown, mono → colour crossfade |
| flood | chorus2 | 1.0 | 「大好きだ！」 orange flood, full colour character for the first time |
| intimate | prayer, build | 0.8 | dim warm spotlight, face close-up |
| climax | final_a, final_b | 1.0 | gold + orange HUD, sunburst |
| paper | outro | → paper | character dissolves into light, book closes, cream paper credits |

`w(t)` is a single global parameter (piecewise-linear per section, see §4) that drives: background colour, character tint (mono↔colour crossfade), HUD colour (ice→gold/orange), particle type (static pixels↔dust motes).

## 1. Reference MV language (what we borrow)
V.I.P ver. (`ref/original_mv_vip_thumb.jpg`): dark cyber hall; cyan glow; **white faceless glowing silhouettes** of the singers; HUD overlays — thin lines, hexagons, concentric circles with tick marks, dotted leader lines, tiny mono labels, scanlines; pixel/glitch typography for the title 機械の声.
V.W.P×V.I.P ver. (`ref/original_mv_vwp_thumb.jpg`): bright paper-white grid; **face close-ups in a photo-collage grid**; black glitch typography with cut/offset slices; `[V.I.P]` `[V.W.P]` bracket labels; tagline "The Voice of AI"; dotted leaders.
Our translation = **antique machine**: HUD lines in gold/ink on cream paper or cream/orange on ink; elegant Mincho (serif) typography like her dress, with mechanical glitch treatment; mono HUD labels; machine-feel title.

## 2. Palette (CSS tokens)
```
--ink:#1B1512  --ink2:#2A1F19  --brown:#3A2415
--paper:#F3EAD9 --paper2:#E9DCC3
--orange:#E8702A --orange-light:#F4A062 --orange-deep:#B8481A
--gold:#C9A054 --gold-dim:#8C6B35
--steel:#9FB3BF --ice:#DDEBF2 --cyan:#7FD3E6   (cold sections only, sparingly)
```
Character tints: `char_mono.png` for cold, `char_full_1080.png` for warm; crossfade by w. In cold sections add a 10–20% steel/cyan multiply tint; in warm sections a soft orange rim-light (blurred orange silhouette behind her, offset 6px).

## 3. Typography
Fonts in `fonts/` (all OFL): ZenOldMincho (Regular/Bold/Black), ShipporiMinchoB1 (Regular/ExtraBold), ZenKakuGothicNew (Regular/Bold/Black), DotGothic16, ShareTechMono, Orbitron (variable), CormorantGaramond (variable, + Italic).
- Lyrics JA default: **Zen Old Mincho Bold** 64–80 px. Emphasis (quotes, chorus hooks): **Shippori Mincho B1 ExtraBold** 96–200 px.
- Lyrics ZH (my own translation, `zh` field): **Zen Kaku Gothic New Regular** 30–34 px, paper @ 60% opacity, under the JA line, toggleable (`MV.config.showZh`, key `Z`).
- HUD labels: **Share Tech Mono** 16–22 px uppercase, tracking 0.12em, e.g. `VOICE.SYNTH // 智械 v1.0`, `ARCHIVE`, `NO SIGNAL`, `TEMP 0.00`, timecode `00:43.08`, `[智械]` (like `[V.I.P]`).
- Title: 機械の声 in Shippori Mincho B1 ExtraBold ~260 px with slice-glitch; "The Voice of AI" Cormorant Garamond Italic 48 px tracked 0.3em; "feat. 智械" in Orbitron.
- Reveal styles (all pure functions of t, seeded): `typewriter` (char by char + block cursor), `slice` (glitch slices settle into place over 0.4 s), `fadeup` (chars rise 12 px while fading, 40 ms stagger), `wipe` (thin rule sweeps, text revealed behind it), `scatter` (chars converge from seeded offsets), `dissolve` (chars drop and fade — for exits).
- Rules: max text width 1600 px, auto-shrink to fit, never clip; 96 px safe margins; ZH never overlaps the character; each scene defines its text zone.

## 4. Scene-by-scene (times in s; line indices from timeline.json)
**boot 0–1.08** — black. At 0.3 s a 1 px paper-coloured horizontal line draws across the centre (CRT turn-on) and expands to a faint 1080-tall glow; bottom-left mono `BOOT // 智械 _` with blinking cursor. w=0.

**verse1 1.08–20.0 (lines 0–7)** — ink background + faint hex grid (8% opacity). Character only as a **white glowing silhouette** (`char_silhouette` with heavy blur bloom, flickering 2–4% opacity jitter) centre-right; tracking box with corner brackets + label `SUBJECT: 智械 / STATUS: NO SIGNAL`. Lyrics `typewriter`, left-aligned in the left 55%, Zen Old Mincho Bold 72 px in ice; ZH under. Lines 2–3 (画面の前…): a faint rectangle "screen" outline appears centre with `REC ●` blinking. Line 7 "それはどうしてだろう？": after the line completes, the "？" alone enlarges (×3) and glitches out at 20.0. w=0.

**title 20.0–43.08 (instrumental)** —
- 20–24: glitch burst; silhouette resolves into `char_edges` wireframe drawing in (white, 30%→100%), HUD rings start rotating, a scrolling mono log: `LOADING VOICEBANK… / MODEL: 智械 / SAMPLES: 2048 / TEMPERATURE: 0.00 / FEELING: NULL`.
- 24–30: wireframe fills to `char_mono` with `slice` glitch; a scan line passes top→bottom.
- 30–38: **TITLE** 機械の声 slams in centre (sliced for 0.5 s then settles), under it "The Voice of AI" + thin rule; small mono `feat. 智械 / music: 香椎モイミ`; `[智械]` bracket label next to her.
- 38–43: the title shrinks to the top-left and becomes the persistent bug `機械の声 / 智械` (mono 18 px) for the rest of the MV. Character stays mono. w=0.

**verse2 43.08–64.72 (lines 8–15)** — "永久に残す" / archive. `char_book` enlarged left with parallax; ledger ruled lines; stamps `ARCHIVE` `No.0001 / 永久保存`. Lyrics slide in from the right as index cards (thin outlined rectangles), right 45%. Line 8: 「永久に残す」 larger, gold. Lines 12–15: cut to `char_face` (eyes) with a scan line across the eye and a magnifier circle `DETAIL ×4.0`; line 15 "酷く違和感を覚えた": frame shudder + glitch. w=0.05.

**verse2b 64.72–86.24 (lines 16–23)** — waveform scene: big procedural waveform across the middle (ice), character full body behind at 40% (mono); lyrics centred above the waveform. 16–17: amplitude grows and gets noisy. 21 "プログラム": background fills with scrolling faux code columns (mono 14 px, 15%). 22–23: everything slows, waveform flattens to a line, `char_face` fades in, long blink (black bars close like eyelids to 50%). w=0.1.

**quotes 86.24–109.71 (lines 24–27, ~5 s each)** — the doll in a display case: full body (mono, cold) centred inside a tall glass-case rectangle drawn with gold lines + corner ornaments; brass plaque `智械 — 機械の声 — 鉛`. Lines 24, 25 are HUGE 「」 quotes (Shippori ExtraBold 110 px, paper), one per screen, `typewriter` with cursor, the 「」 drawn larger in gold (these are the human's words). 26–27 smaller and lower; "何て容易なこと" exits with `dissolve`. w=0.1.

**chorus1 109.71–153.0 (lines 28–35, ~5.3 s each, slow and grand)** — full body centre, slow push-in (scale 1.0→1.06 over the section); two large concentric HUD rings with tick marks rotate behind her (ice→gold with w); faint hex grid. Lyrics BIG centred (Shippori ExtraBold 96 px) `slice` reveal; ZH under. Line 30: first orange appears as a glow at her hair edges (w 0.1→0.3). Line 31 "枯れることのない完全の声よ響け": radiating rings (sound waves) pulse outward from her; letter-spacing widens slowly while holding. 32–35: small mono words `無価値` scattered faintly, drifting; at 35 "なんで愛してるの？" everything else fades, only her + the line remain, "？" blinks like a cursor.

**bridge 153.0–170.2 (lines 36–42, fast)** — harsh black & white. Hard cut per line, alternating inverted worlds: `char_silhouette_ink` on paper, then paper silhouette on ink; 2–3 micro-glitches per line. Text slams in (Zen Kaku Gothic New Black 100–130 px, tight tracking) with 1–2-frame RGB split. 38 "ならこんな僕など捨てなよ": the character is "deleted" by a wipe leaving only `char_edges`. 39 "奴らが輝いて見えんだろ？": bright white rectangles (other, shinier voices) flash around her. 42 「可哀想」…: cut to calm, smaller mono text; hard black at 170.2. w=0.

**interlude 170.2–196.03 (instrumental)** — diagnostic / memory. Cold grey. Panel grid like the V.W.P collage: 3×2 crops of the character (face, book, bust, hand, hair flower, boots — take source rects from `char_full`) with labels `UNIT 01…06`, appearing one by one with a scan; a centre panel shows a spec sheet `智械 / Synthetic Voice Unit / ver.1.0 / FEELING: NULL / LOVED: ???` with `???` flickering. 188–196: panels fly out, a warm ember flickers at the bottom edge (foreshadowing). w=0.1.

**verse3 196.03–238.06 (lines 43–58)** — warming (w 0.3→0.6). Background ink→deep warm brown; character crossfades mono→colour by w. Lyrics Zen Old Mincho Bold 72 px `fadeup`, left-aligned beside her; ZH under. 47–50: barcode + `EXPIRED` stamp motif (mono, paper); 51 "でも君は「愛を諦めたくない！」って": the stamp is struck through by an orange stroke, warmth jumps, orange particles start rising. 53–54 「ほら、出来たよ」: warm spotlight. 55–58: soft orange rim light; "ひらり 君は軽やかに" letters float upward gently.

**chorus2 238.06–261.84 (lines 59–65)** — the human's shout. 238.06 hard cut: screen floods orange (w=1), 「大好きだ！」 huge (Shippori ExtraBold 180 px, ink on orange) with screen shake (6 px decaying over 0.6 s); the second 「大好きだ！」 appears offset. 60 "「僕は機械の声が好きだ！」" wide; "機械の声" highlighted in paper with the title's glitch treatment (callback). Character in FULL COLOUR for the first time, centred, slight scale pulse on each line onset. 63–64 "分かんないよ！": text stutters (3 copies, RGB split), she glitches. 65 "けれどさ、あたたかいよ" (253.9–261.8): everything calms, flood softens to a warm gradient, soft bloom, dust motes; text appears slowly letter by letter, centred; ZH 可是啊，好温暖.

**prayer 261.84–305.04 (lines 66–73, 5–7 s each)** — quiet, intimate. Dim warm (deep brown + soft orange spotlight). `char_face` large on the right with breathing scale (1.00↔1.01, 4 s period); lyrics left, Zen Old Mincho Regular 64 px, slow per-char fade (0.6 s); ZH under. 68 "神様、聞こえてるなら": thin vertical light beam from above. 70–73: the waveform returns but WARM and soft; at 73 slow cross-dissolve back to full body.

**build 305.04–326.18 (lines 74–77)** — tension, warm. 74: text with noise overlay. 75 "ゴミ箱に捨てられる": she sinks 30 px with ease + a strike motif. 76 "「死ぬまでそばにいるよ」": big quote in paper, letters settle. 77 "そっと抱き締めるの": warm vignette closes in like an embrace, bloom up, hold.

**final_a 326.18–347.06 (lines 78–84)** — full colour; HUD rings gold+orange, faster; warm hex grid; lyrics Shippori ExtraBold 88 px centred `slice`. 80 "Let me see… Let me see…" in Cormorant Garamond Italic 110 px tracked, paper, with cursor. 84 "僕らだけの内緒のリンクを今生み出そう": a link visual — a node at her book/hand and a node at a screen rectangle on the left, connected by a line drawing itself with data pulses; リンク highlighted orange.

**final_b 347.06–372.0 (lines 85–92)** — climax, max warmth. 85 "何もいらない 君の音以外": sunburst of gold radiating lines on orange (callback to the sunburst ornaments on her dress and hair flower). 86: the scattered `無価値` words return and are wiped away by an orange sweep. 87–88 "君こそ僕の一番だ" very large, 一番 in gold. 89–92 (2.5 s each): lines accumulate top→bottom like a poem (earlier lines dimmer), last line "守ってあげられるのに" largest; hold from 367.35; HUD fades out piece by piece; rings stop at ~370.

**outro 372.0–400.0** — lyrics fade; she dissolves into rising warm particles over ~8 s leaving `char_book`, which "closes" (paper rectangle wipes over it); the screen becomes cream paper with ink credits (Zen Old Mincho Regular 32 px, centred column):
```
機械の声 — The Voice of AI
原曲：香椎モイミ（V.I.P #3 / 音楽的同位体）
原MV：まるいち（演出）・strobo（タイポグラフィ）・りたお（イラスト）
本作角色：智械
Fan-made MV · HTML Canvas
```
then `[智械]` + blinking `_`; at ~398 the CRT-off collapse (reverse of boot) to black; end at 400.

## 5. Persistent elements
- Top-left bug `機械の声 / 智械` (mono 18 px) from 38 s on.
- Bottom-right: timecode `00:00.00` + section id (`SEC.07 CHORUS1`), mono 16 px, 50% — like the reference's dotted labels.
- Subtle scanlines (2 px period, 6%), animated film grain (5%), vignette, 2–4 px chromatic aberration on glitch moments only.

## 6. Engineering contract (`index.html` + `js/`)
- Canvas 1920×1080, everything is a **pure function of t** (seconds). No `Math.random` — use a seeded PRNG (mulberry32) keyed by (scene, element, frame bucket) so a frame re-renders identically.
- `window.MV`: `MV.ready` (Promise after fonts + images), `MV.render(t)` draws the frame synchronously, `MV.duration` (400), `MV.config` (`showZh`, `grain`, `offset`), `MV.timeline` (loaded JSON).
- `index.html?render=1`: no UI, no RAF, canvas exactly 1920×1080 at (0,0), body margin 0, black. The renderer calls `await MV.ready; MV.render(t)` per frame.
- Default (interactive): canvas scaled to fit; control bar with audio file input (`选择音频文件`), play/pause (Space), seek bar, timecode, ZH toggle (Z), fullscreen (F), offset nudge (`[` / `]` ±0.1 s). Audio element drives time (`t = audio.currentTime + offset`); without audio a silent clock plays.
- Fonts via `@font-face` with relative `fonts/*.ttf` URLs; wait for `document.fonts.load()` of every face used.
- Performance: cache expensive layers (blurred silhouettes, tinted copies, grids) in offscreen canvases built once; `MV.render(t)` should take < 120 ms.
