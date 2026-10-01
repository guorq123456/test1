# MV render pipeline

Deterministic, frame-by-frame MP4 renderer for the Canvas music video in `../index.html`
(contract: `STORYBOARD.md` §6). For every frame `i` it sets `t = start + i / fps`, calls
`MV.render(t)` in headless Chromium (`index.html?render=1`), reads the canvas pixels and pipes
them straight into ffmpeg/libx264. No frame files are written to disk.

| file | purpose |
|---|---|
| `render.mjs` | MP4 renderer (single pass or resumable chunks, optional audio mux, transport benchmark) |
| `sheet.mjs` | QA: PNG frames at chosen times + labelled contact sheet (ImageMagick `montage`) |
| `lib.mjs` | shared code: static server, browser/page setup, frame transports, ffmpeg helpers |

Requirements: Node ≥ 18.17, `ffmpeg`/`ffprobe` on PATH, ImageMagick `montage` (sheets only), Playwright.
In this sandbox Playwright and Chromium are preinstalled (`/opt/node-tools/...`, `/opt/pw-browsers/chromium-1194`).
On your own machine run `npm install && npx playwright install chromium` in this folder; the scripts fall back to
Playwright's bundled Chromium when the sandbox path does not exist (or pass `--chrome <path>`).

## Quick start

```bash
cd mv/render

# full 400 s render, 1080p30 -> ../out/mv.mp4 (built-in static server, no other setup)
node render.mjs --serve

# same, but resumable in 20 s chunks (re-run the identical command after a crash)
node render.mjs --serve --chunk 20

# 720p preview
node render.mjs --serve --scale 720 --out ../out/mv_720p.mp4

# with the song muxed in (see "Audio" below for --audio-offset)
node render.mjs --serve --chunk 20 --audio ../assets/song.mp3 --out ../out/mv_with_audio.mp4

# a 10 s excerpt
node render.mjs --serve --start 30 --end 40 --out ../out/test_30_40.mp4

# QA contact sheet: one frame every 10 s -> ./sheet/contact.jpg (+ PNGs)
node sheet.mjs --serve --every 10
node sheet.mjs --serve --times 5,35,120,245,360 --out-dir sheet_test
```

npm equivalents: `npm run render`, `npm run render:720`, `npm run render:chunked`, `npm run sheet`,
`npm run bench`; append extra flags after `--`, e.g. `npm run render -- --start 30 --end 40`.

Without `--serve` the page is loaded from `--url` (default `http://localhost:8765/index.html?render=1`),
so any static server you already run on port 8765 works too. With `--serve` only the path + query of `--url`
are used (e.g. `--url 'index.html?render=1&foo=1'`). Relative `--out` paths are relative to your
current directory; the default is `mv/out/mv.mp4`.

## render.mjs options

| option | default | |
|---|---|---|
| `--url` | `http://localhost:8765/index.html?render=1` | page to render |
| `--serve` / `--root` / `--port` | off / `mv/` / free port | built-in static server (Node `http`, no deps) |
| `--start`, `--end` | `0`, `MV.duration` | seconds; `--end` is exclusive. Frames = `round((end-start)*fps)` |
| `--fps` | `30` | |
| `--out` | `mv/out/mv.mp4` | written as `<out>.part`, renamed when complete |
| `--crf`, `--preset` | `18`, `medium` | libx264 |
| `--scale` | `1080` | `720` → `-vf scale=1280:-2` (lanczos) |
| `--audio`, `--audio-offset` | –, `0` | mux AAC 256k, `-shortest`; offset semantics = `MV.config.offset` |
| `--chunk <s>` | off | render `<outdir>/chunks/NNN.mp4`, then concat (demuxer, stream copy) |
| `--chunk-dir`, `--fresh` | `<outdir>/chunks`, off | chunk location; `--fresh` discards existing chunks |
| `--transport` | `raw` | `raw`, `raw-cdp`, `png`, `cdp`, `cdp-fast`, `screenshot`, `jpeg` (see below) |
| `--jpeg-quality` | `92` | only for `--transport jpeg` (lossy) |
| `--workers` | `cores/2 + 1` (3 on 4 cores, max 6) | parallel browser pages rendering different frames |
| `--threads` | ffmpeg auto | x264 threads |
| `--chrome`, `--gpu` | sandbox Chromium, off | Chromium binary; `--gpu` drops `--disable-gpu` |
| `--timeout` | `180` | seconds for page load + `MV.ready` |
| `--allow-console-errors` | off | log `console.error` instead of aborting |
| `--no-check` | off | skip the start-up determinism check |
| `--bench [n]` | – | benchmark all transports over n frames, check pixel equality + determinism, no output |

Progress is printed every 2 s: `frames done/total, t, elapsed, fps, ETA` (+ chunk number).

**Fail-fast**: any `pageerror`, `console.error`, failed request or HTTP ≥ 400 (except `/favicon.ico`), an exception
thrown by `MV.render`, a renderer crash or an ffmpeg error aborts the render with exit code 1 and prints the
messages. The partial `.part` file is deleted; completed chunks are kept. Bad arguments exit with code 2.

**Determinism check**: before rendering, every worker page renders the first, middle and last frame of the range
and the pixel hashes must be identical (a single page renders them twice). This catches non-pure `MV.render`
code (unseeded `Math.random`, `Date.now`, state carried between frames) and page files that changed while the
workers were loading.

### Chunks and resume

`--chunk 20` splits the range into 20 s pieces (`000.mp4`, `001.mp4`, …, 600 frames each at 30 fps). Each chunk is
encoded to `NNN.mp4.part` and renamed only when ffmpeg finished. On a re-run a chunk is skipped when its file
exists and `ffprobe -count_packets` reports exactly the expected number of frames; anything else is re-rendered.
`manifest.json` records page path, start, fps, chunk length, crf, preset, scale, transport kind and canvas size;
re-using chunks rendered with different settings is refused (use `--fresh` or another `--chunk-dir`). Changing only
`--end` is fine: the last chunk is re-rendered if its length changed. If the page code changed, use `--fresh`.
Chunks are kept after the final concat (≈ the size of the final video); delete `out/chunks/` when done.

## Audio

`--audio song.mp3` muxes the song while rendering (AAC 256 kb/s, `-shortest`). `--audio-offset` has the same meaning
as `MV.config.offset` in the page (`t = audio.currentTime + offset`): positive values make the sound start later.
`--start` is accounted for automatically (an excerpt from 30 s gets the audio from 30 s).

To mux an audio file into an already rendered silent MP4 (no re-encode of the video):

```bash
ffmpeg -i mv.mp4 -i song.mp3 -c:v copy -c:a aac -b:a 256k -shortest mv_with_audio.mp4
```

Shifting the timing — `-itsoffset` applies to the input that **follows** it:

```bash
# sound comes 0.25 s too early -> delay the audio by 0.25 s
ffmpeg -i mv.mp4 -itsoffset 0.25 -i song.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest mv_with_audio.mp4
# sound comes 0.25 s too late -> negative offset (or equivalently skip into the audio with -ss 0.25 before -i song.mp3)
ffmpeg -i mv.mp4 -itsoffset -0.25 -i song.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest mv_with_audio.mp4
```

## Frame transport (why `raw`)

`node render.mjs --serve --bench 24 --workers 4` on the real page (4-core sandbox VM, software canvas).
"ms/frame" is `MV.render(t)` + capture + delivery to Node as a Buffer, sequential on one page:

| transport | how | ms/frame | capture overhead | lossless |
|---|---|---:|---:|---|
| (none) | `MV.render(t)` only | 47 | – | |
| **raw** | `getImageData` → `fetch` POST of a `Blob` to a local Node sink → ffmpeg `-f rawvideo -pix_fmt rgba` | **94** | **+47** | yes |
| raw-cdp | `getImageData` → base64 string returned through CDP | 308 | +261 | yes |
| png | `canvas.toDataURL('image/png')` → base64 → Buffer | 244 | +196 | yes |
| cdp-fast | CDP `Page.captureScreenshot` png, `optimizeForSpeed` | 219 | +171 | yes |
| cdp | CDP `Page.captureScreenshot` png | 769 | +722 | yes |
| screenshot | Playwright `page.screenshot({type:'png', clip})` | 837 | +789 | yes |
| jpeg | `canvas.toDataURL('image/jpeg', q)` | 94 | +46 | **no** |

All lossless transports were verified pixel-identical to `getImageData` (RGB). Moving 8 MB through CDP costs
~190 ms (JSON/base64), so the default `raw` transport sends the bytes on a side channel: the page POSTs them as a
`Blob` to a tiny HTTP sink in the render process (a typed-array body is ~10× slower because Chromium copies it through
the DevTools network layer). `--disable-gpu` is the default: same speed as SwiftShader here and bit-stable.

Colour: RGB → BT.709 limited-range YUV 4:2:0 (`scale=out_color_matrix=bt709:out_range=tv`), stream tagged
`bt709` (primaries/trc/matrix) so players show the canvas colours. Canvas alpha is ignored (the page is opaque).

## Throughput (measured in this sandbox: 4 vCPU, shared with another agent's build)

| content | settings | end-to-end |
|---|---|---|
| real MV page, t=30–40 / 245–250 | 1080p, crf 18, medium, 3 workers | **10–12 frames/s** (12.0 when the box was quiet) |
| real MV page, t=245–250 | 720p, crf 18, medium, 3 workers | 12.9 frames/s |
| stub page (simple), no grain | 1080p, crf 18, medium, 3 workers | 16–17 frames/s |
| stub page with full-frame random grain | 1080p, medium | 7 frames/s (x264-bound, ~90 Mb/s) |

Breakdown for the real page: page side alone (render + raw capture, no encoding) reaches ~19 frames/s with
3–4 pages; libx264 `medium` alone encodes ~24 frames/s on all 4 cores; together they share the CPU → ~10 fps.
**Full MV: 12,000 frames ≈ 17–20 min at 1080p** (≈ 15 min at 720p) on this box; proportionally faster on more cores
(raise `--workers`). Heavy per-frame grain raises x264 time and file size a lot.

## Troubleshooting

* `ERR_CONNECTION_REFUSED` – no server on `--url`; add `--serve`.
* `MV.ready did not resolve` – fonts/images failed; open the page without `?render=1` and check the console.
* `determinism check failed` – something in `MV.render` depends on wall-clock time, randomness or render history,
  or the page files were edited while loading; re-run, or fix the page (seeded PRNG keyed by t).
* Out of disk: nothing per-frame is written; chunks ≈ final size.
