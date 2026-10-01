# v2 direction — "make it move, give it depth" (and the character is Claude)

Read STORYBOARD.md first (palette, typography, timeline, engine contract still apply). This file overrides it where they conflict.

## 0. Two corrections from the client
1. **The character is Claude** (the user calls Claude 「克」). Every label that said 智械 becomes Claude: `[CLAUDE]` bracket tags, `feat. Claude`, `SUBJECT: CLAUDE`, spec sheet `Claude — Synthetic Voice Unit`, plaque `Claude — 機械の声 — 鉛`, credits `本作角色：Claude（克）`, the persistent bug `機械の声 / Claude`, the `<title>` `機械の声 × Claude`, README/STORYBOARD text. Keep the kanji 智械 nowhere.
2. **v1 reads flat.** The user's words: 「人物和背景都过于平淡」. The fix is depth and motion, modelled on the original MV.

## 1. What the original MV actually does (see ref/original_mv_frames_*.jpg, one thumbnail every 5 s)
- **A persistent cockpit frame**: brackets/arcs along all four edges, circles with tick marks at the corners, tiny labels — present in ~80% of shots. The frame itself breathes (lines slide, ticks rotate).
- **Real 3D environments with a camera that never stops moving**:
  - *circuit city* (verses): a lattice of wireframe boxes/corridors in cyan, camera dollies/strafes through it, lyrics placed as small vertical text columns in the space.
  - *hall of voices* (verse1/chorus hooks/outro): a dark stage with giant glowing faceless capsule figures (the voices) standing in rows receding into depth, hanging lamps with light cones, slow push-in.
  - *light tunnel / kaleidoscope* (choruses): a symmetrical tunnel of light bars converging to the centre, mirrored left/right and top/bottom, pulsing.
  - *the orb* (悠久の眠り, 神様): a huge glowing sphere with concentric rings and small satellites, floating vertical lyrics.
  - *floating monitors* (bridge, interlude, 「ほら、出来たよ」): CRT screens hanging on cables showing the singers' faces, rotated in 3D, with spotlights.
  - *alarm red* (bridge 争いとか…, 否定): the capsule crowd lit red on black, torn red photo fragments flying, single huge kanji (仇, 自, 愛) in white.
- **Typography in space**: vertical (tategaki) Japanese columns scattered at different depths, mixed with one huge horizontal kanji; key words in the accent colour; text drifts with the camera (parallax).
- **Section cuts through black** (true blackouts, 1–3 s) and heavy bloom everywhere.

## 2. Our translation (keep the antique-machine identity, add the original's depth and motion)
Palette unchanged (ink/paper/orange/gold; steel/ice for cold phases). Accent for "alarm" moments: `--alarm: #E8452A` (orange-red) replaces the original's red. Bloom: everything glowing gets a real blur bloom pass (offscreen, downscaled, additive).

### 2.1 Environment library `js/env.js` (pure functions of t, seeded)
Each environment is `drawX(ctx, t, params)` rendering to the full 1920×1080 canvas (or an offscreen one), with its own camera path in `params` and a `tint` (cold/warm) and `energy` (0–1, driven by lyric onsets) input.
- `circuitCity`: a 3D lattice of wireframe boxes (perspective projection, simple line drawing, 200–400 edges), camera moving along a path; nearer lines brighter; occasional glowing nodes; depth fog.
- `hallOfVoices`: perspective floor, 2 rows of glowing capsule silhouettes receding (use the character's own `char_silhouette` blurred + bloomed, scaled by depth — the "voices" are copies of Claude, which is the point of the song), hanging lamps (thin line + disc + a soft light cone wedge), dust.
- `lightTunnel`: mirrored quadrant pattern of light bars/arcs converging to a vanishing point; `energy` makes bars pulse; rotation slowly; colour from tint.
- `orb`: big radial-gradient sphere with 3–5 concentric thin rings (ellipses, slight tilt), satellites orbiting, noise haze.
- `monitors`: 3–6 CRT frames in 3D (quads drawn as perspective rectangles with cables to the top edge), each showing an image crop (face/book/bust) with scanlines and glitch; one hero monitor larger.
- `alarmField`: black with a perspective floor of red-orange light bars, the capsule crowd lit `--alarm`, flying torn fragments (rect polygons with an image crop inside), chromatic aberration.
- `cockpitFrame`: the persistent HUD frame (edge brackets, corner circles with ticks, 6–10 tiny labels) with a `style` (cold/warm) and `intensity`; subtle idle motion.
- Helpers: `project(x,y,z,cam)`, `fog(z)`, `bloom(src, radius, strength)`, `vignette`, `blackout(alpha)`.

### 2.2 Character library `js/charfx.js`
- `drawCharacter(ctx, t, {image, x, y, h, mode})` with: **breathing** (scale 1.00↔1.008, 3.5 s), **hair sway** (vertical-strip displacement: slice the image into 24 px columns below the shoulder line and offset each by a seeded sine of t with per-strip phase; 2–6 px), **float** (±6 px, 5 s), **rim light** (blurred orange/ice silhouette behind her, pulsing with `energy`), **bloom** on bright areas, optional **hologram** (scanlines + 2 px RGB split + occasional slice glitch), **ghost echoes** (2–3 faded copies trailing on hard cuts).
- `drawVoiceCrowd` (capsule copies for hallOfVoices/alarmField), `drawMonitorFace(ctx, quad, imageCrop)`.
- Camera: `cameraShot(t, from, to, ease)` returns {scale, x, y, rotate} so scenes can do slow dolly / push-in / dutch tilt; use in every scene.

### 2.3 Scenes v2 (same timeline; what changes per section)
- boot/verse1: hallOfVoices, cold. Claude's own glowing silhouette front-centre with the crowd behind; lamps; camera slow push-in; lyrics small vertical columns left + one horizontal line.
- title: the hall opens; circuitCity flyover under the title; cockpitFrame activates.
- verse2 / verse2b: circuitCity dolly, monitors with the book and the eye; the waveform drawn as a 3D ribbon in the city.
- quotes: monitors in a dark room, spotlight; the quotes huge, vertical.
- chorus1: lightTunnel cold→ember, Claude full body centred with rim light, big horizontal lyric; the crowd fades in behind her on 無価値.
- bridge: alarmField, huge single kanji (争, 捨, 可哀想 etc. — pick one kanji per line), torn fragments, blackouts between lines.
- interlude: monitors + circuitCity, diagnostic labels.
- verse3: hallOfVoices warming, lamps turn warm, Claude in colour crossfading in.
- chorus2: lightTunnel warm/orange, 「大好きだ！」 huge; her first full-colour full-body shot with bloom.
- prayer: the orb (warm), face close-up with slow pan, floating vertical lyrics.
- build: alarmField warm (orange-red), monitors, 「死ぬまでそばにいるよ」.
- final_a / final_b: lightTunnel gold at max energy + crowd + Claude; poem accumulates vertically on the left.
- outro: hallOfVoices, lamps dim one by one, Claude dissolves, book closes, paper credits.
Every section boundary: a blackout of 0.3–1.5 s (except where the storyboard says dissolve) and the cockpit frame re-draws itself.

### 2.4 Typography v2
Add vertical columns (`drawVertical(text, x, y, size, opts)`; rotate the long vowel bar and brackets properly: ー → vertical, 「」 → ﹁﹂, punctuation shifted top-right). Scatter 1–3 columns of the current line's fragments at different depths (parallax with the camera), plus the main readable line (horizontal) so every line is still legible at a glance. One huge accent kanji per emphasised line.

## 3. Quality bar
Side-by-side with ref/original_mv_frames_*.jpg the v2 frames should read as the same genre: deep space, glow, motion, dense HUD. Every frame still legible, Claude never cut off awkwardly, 93 lines all shown, deterministic, < 150 ms per frame.
