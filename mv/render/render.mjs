#!/usr/bin/env node
// Deterministic frame-by-frame MP4 renderer for the Canvas MV (window.MV contract, STORYBOARD.md §6).
// Steps t = start + i/fps, calls MV.render(t) in headless Chromium, pipes every frame into ffmpeg/libx264.
// No frame files touch the disk. See README.md.
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import {
  MV_ROOT, DEFAULT_URL, TRANSPORTS, LOSSLESS, fmtTime, fail, sleep,
  launchBrowser, openMV, grabFrame, resolveUrl, spawnFfmpeg, run, probeFrameCount,
  encodeArgs, scaleFilter, muxAudio, parseCli, isRaw, closeSink,
} from './lib.mjs';

const DEFAULT_WORKERS = Math.max(1, Math.min(6, Math.floor(os.cpus().length / 2) + 1)); // 4 cores -> 3

const SPEC = {
  url: { default: DEFAULT_URL },
  serve: { type: 'boolean', default: false },
  root: { default: MV_ROOT },
  port: { type: 'number', default: 0 },
  start: { type: 'number', default: 0 },
  end: { type: 'number', default: undefined },
  fps: { type: 'number', default: 30 },
  out: { default: path.join(MV_ROOT, 'out', 'mv.mp4') },
  crf: { type: 'number', default: 18 },
  preset: { default: 'medium' },
  scale: { default: '1080' },
  audio: { default: undefined },
  audioOffset: { type: 'number', default: 0 },
  chunk: { type: 'number', default: 0 },
  chunkDir: { default: undefined },
  fresh: { type: 'boolean', default: false },
  transport: { default: 'raw' },
  jpegQuality: { type: 'number', default: 92 },
  workers: { type: 'number', default: DEFAULT_WORKERS },
  threads: { type: 'number', default: 0 },
  chrome: { default: undefined },
  gpu: { type: 'boolean', default: false },
  timeout: { type: 'number', default: 180 },
  allowConsoleErrors: { type: 'boolean', default: false },
  noCheck: { type: 'boolean', default: false },
  bench: { type: 'number', default: 0, optionalValue: 30 },
  help: { type: 'boolean', default: false },
};

const HELP = `Usage: node render.mjs [options]

Page
  --url <url>          page to render (default ${DEFAULT_URL})
  --serve              start a built-in static server for --root on a free port;
                       only the path+query of --url is used
  --root <dir>         directory served by --serve (default ${MV_ROOT})
  --port <n>           port for --serve (default: any free port)
Time
  --start <s>          first frame time (default 0)
  --end <s>            end time, exclusive (default MV.duration from the page)
  --fps <n>            frames per second (default 30)
Output
  --out <file>         output MP4 (default ${path.join(MV_ROOT, 'out', 'mv.mp4')})
  --crf <n>            x264 CRF (default 18)
  --preset <name>      x264 preset (default medium)
  --scale 1080|720     720 => -vf scale=1280:-2 (default 1080)
  --audio <file>       mux audio (aac 256k, -shortest)
  --audio-offset <s>   same meaning as MV.config.offset (t = audioTime + offset):
                       positive delays the audio (-itsoffset)
  --chunk <s>          render in N-second chunks to <outdir>/chunks/NNN.mp4, then concat;
                       re-running resumes (complete chunks are skipped)
  --chunk-dir <dir>    chunk directory (default <dir of --out>/chunks)
  --fresh              discard existing chunks first
Engine
  --transport <name>   ${TRANSPORTS.join(' | ')}
                       (default raw = getImageData RGBA posted to a local sink: lossless, fastest)
  --jpeg-quality <q>   for --transport jpeg, 1-100 (default 92)
  --workers <n>        parallel browser pages rendering frames (default ${DEFAULT_WORKERS})
  --threads <n>        x264 threads (default: ffmpeg auto)
  --chrome <path>      Chromium executable (default ${'/opt/pw-browsers/...'} if present, else Playwright's)
  --gpu                do not pass --disable-gpu to Chromium
  --timeout <s>        page load / MV.ready timeout (default 180)
  --allow-console-errors  log console.error instead of aborting
  --no-check           skip the start-up determinism check (all pages must render identical probe frames)
  --bench [n]          benchmark transports over n frames (default 30), no output written
`;

const opt = parseCli(process.argv.slice(2), SPEC);
if (opt.help) { process.stdout.write(HELP); process.exit(0); }
if (!(opt.fps > 0)) fail('--fps must be > 0');
if (!TRANSPORTS.includes(opt.transport)) fail(`--transport must be one of ${TRANSPORTS.join(', ')}`);
try { scaleFilter(opt.scale); } catch (e) { fail(e.message); }
if (opt.workers < 1) fail('--workers must be >= 1');
if (opt.audio && !fs.existsSync(opt.audio)) fail(`audio file not found: ${opt.audio}`);
const jpegQ = opt.jpegQuality > 1 ? opt.jpegQuality / 100 : opt.jpegQuality;
const OUT = path.resolve(opt.out);

// ------------------------------------------------------------------ lifecycle
let browser = null, server = null;
const liveFfmpeg = new Set();
let shuttingDown = false;
async function shutdown() {
  if (shuttingDown) return; shuttingDown = true;
  for (const ff of liveFfmpeg) ff.kill();
  await Promise.race([Promise.allSettled([browser?.close(), server?.close(), closeSink()]), sleep(5000)]);
}
for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, async () => { console.error(`\n${sig} — aborting (complete chunks are kept)`); await shutdown(); process.exit(130); });
}

// ------------------------------------------------------------------ progress
const prog = { total: 0, done: 0, fresh: 0, t: 0, t0: Date.now(), tRender: 0, label: '' };
function progressLine() {
  const now = Date.now();
  const el = (now - prog.t0) / 1000;
  const rate = prog.tRender ? prog.fresh / ((now - prog.tRender) / 1000) : 0;
  const eta = rate > 0 ? (prog.total - prog.done) / rate : NaN;
  const pct = prog.total ? (100 * prog.done / prog.total).toFixed(1) : '0.0';
  return `[render] ${prog.done}/${prog.total} frames (${pct}%)  t=${prog.t.toFixed(3)}s  elapsed ${fmtTime(el)}  ` +
    `${rate.toFixed(2)} fps  ETA ${fmtTime(eta)}${prog.label ? '  ' + prog.label : ''}`;
}
let progTimer = null;
const startProgress = () => { progTimer = setInterval(() => console.log(progressLine()), 2000); progTimer.unref(); };
const stopProgress = () => clearInterval(progTimer);

// ------------------------------------------------------------------ parallel in-order frame producer
/**
 * Render frames [i0, i1) on all pages in parallel, deliver them to `sink(i, buf)` strictly in order.
 * At most `ahead` frames are buffered (memory bound: ~8 MB per raw frame).
 */
async function produce(mvs, i0, i1, tOf, transport, sink, ahead = mvs.length * 2) {
  let next = i0, writeIdx = i0, failed = null;
  const ready = new Map();
  let wakeWriter = null;
  let spaceWaiters = [];
  const wakeAll = () => { const w = spaceWaiters; spaceWaiters = []; w.forEach((r) => r()); wakeWriter?.(); };
  async function worker(mv) {
    while (!failed) {
      const i = next++;
      if (i >= i1) return;
      while (i - writeIdx >= ahead && !failed) await new Promise((r) => spaceWaiters.push(r));
      if (failed) return;
      const buf = await grabFrame(mv, tOf(i), transport, jpegQ);
      ready.set(i, buf);
      wakeWriter?.();
    }
  }
  async function writer() {
    while (writeIdx < i1) {
      if (failed) return;
      if (!ready.has(writeIdx)) { await new Promise((r) => { wakeWriter = r; }); wakeWriter = null; continue; }
      const buf = ready.get(writeIdx); ready.delete(writeIdx);
      await sink(writeIdx, buf);
      writeIdx++;
      const w = spaceWaiters; spaceWaiters = []; w.forEach((r) => r());
    }
  }
  const ws = mvs.map((mv) => worker(mv).catch((e) => { failed ??= e; wakeAll(); }));
  await writer().catch((e) => { failed ??= e; wakeAll(); });
  await Promise.all(ws);
  if (failed) throw failed;
}

// ------------------------------------------------------------------ encode one range of frames into one file
async function encodeRange(mvs, info, i0, i1, tOf, file) {
  const expect = isRaw(opt.transport) ? info.width * info.height * 4 : 0;
  const ff = spawnFfmpeg(encodeArgs({
    transport: opt.transport, fps: opt.fps, width: info.width, height: info.height,
    crf: opt.crf, preset: opt.preset, scale: opt.scale, out: file, format: 'mp4', threads: opt.threads,
  }));
  liveFfmpeg.add(ff);
  try {
    await produce(mvs, i0, i1, tOf, opt.transport, async (i, buf) => {
      if (expect && buf.length !== expect) throw new Error(`raw frame ${i} has ${buf.length} bytes, expected ${expect}`);
      await ff.write(buf);
      prog.done++; prog.fresh++; prog.t = tOf(i);
    }, Math.max(2, mvs.length * 2));
    await ff.end();
  } catch (e) {
    ff.kill();
    await ff.done.catch(() => {});
    await fsp.rm(file, { force: true });
    throw e;
  } finally {
    liveFfmpeg.delete(ff);
  }
}

// ------------------------------------------------------------------ benchmark
function ffmpegDecodeRgba(buf, codec) {
  return new Promise((resolve, reject) => {
    const ch = spawn('ffmpeg', ['-v', 'error', '-f', 'image2pipe', '-c:v', codec, '-i', '-', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
      { stdio: ['pipe', 'pipe', 'pipe'] });
    const parts = []; let err = '';
    ch.stdout.on('data', (d) => parts.push(d));
    ch.stderr.on('data', (d) => { err += d; });
    ch.on('close', (c) => c === 0 ? resolve(Buffer.concat(parts)) : reject(new Error(err)));
    ch.stdin.end(buf);
  });
}
function compareRgb(a, b) { // ignore alpha (dropped by yuv420p anyway)
  if (a.length !== b.length) return { diff: -1, max: -1 };
  let diff = 0, max = 0;
  for (let i = 0; i < a.length; i++) {
    if ((i & 3) === 3) continue;
    const d = Math.abs(a[i] - b[i]);
    if (d) { diff++; if (d > max) max = d; }
  }
  return { diff, max };
}
const md5 = (b) => crypto.createHash('md5').update(b).digest('hex').slice(0, 12);

async function bench(mvs, start, end) {
  const n = opt.bench;
  const fps = opt.fps;
  const times = Array.from({ length: n }, (_, k) => Math.round((start + (k + 0.5) * (end - start) / n) * fps) / fps);
  const mv = mvs[0];
  console.log(`\nBenchmark: ${n} frames spread over [${start}, ${end}) s, canvas ${mv.info.width}x${mv.info.height}, ` +
    `gpu=${opt.gpu}, native toBase64=${mv.info.nativeBase64}\n`);
  const modes = ['none', 'raw', 'raw-cdp', 'png', 'cdp', 'cdp-fast', 'screenshot', 'jpeg'];
  for (const m of modes) for (const t of times.slice(0, 3)) await grabFrame(mv, t, m, jpegQ); // warm-up
  const rows = [];
  for (const m of modes) {
    let bytes = 0;
    const t0 = performance.now();
    for (const t of times) bytes += (await grabFrame(mv, t, m, jpegQ)).length;
    const ms = (performance.now() - t0) / n;
    rows.push({ m, ms, kb: bytes / n / 1024 });
  }
  const base = rows[0].ms;
  console.log('transport    ms/frame  (capture only)  KB/frame   kind');
  for (const r of rows) {
    const kind = r.m === 'none' ? 'MV.render(t) only' : LOSSLESS.has(r.m) ? 'lossless' : 'lossy';
    console.log(`${r.m.padEnd(12)} ${r.ms.toFixed(1).padStart(8)}  ${(r.m === 'none' ? '' : '+' + (r.ms - base).toFixed(1)).padStart(14)}  ${r.kb.toFixed(0).padStart(8)}   ${kind}`);
  }

  // pixel-exactness of each transport against getImageData
  const tc = times[Math.floor(n / 2)];
  const raw = await grabFrame(mv, tc, 'raw');
  console.log(`\nPixel check at t=${tc}s against getImageData (RGB, ${mv.info.width * mv.info.height} px):`);
  for (const m of ['raw-cdp', 'png', 'cdp', 'cdp-fast', 'screenshot', 'jpeg']) {
    if (m === 'raw-cdp') { const { diff } = compareRgb(raw, await grabFrame(mv, tc, m)); console.log(`  ${m.padEnd(11)} ${diff === 0 ? 'identical' : diff + ' differ'}`); continue; }
    const dec = await ffmpegDecodeRgba(await grabFrame(mv, tc, m, jpegQ), m === 'jpeg' ? 'mjpeg' : 'png');
    const { diff, max } = compareRgb(raw, dec);
    console.log(`  ${m.padEnd(11)} ${diff === 0 ? 'identical' : diff < 0 ? 'size mismatch' : `${diff} channel values differ (max |d|=${max})`}`);
  }

  // determinism: same t rendered after other frames and on another page
  const a = await grabFrame(mv, tc, 'raw');
  await grabFrame(mv, times[0], 'raw');
  const b = await grabFrame(mv, tc, 'raw');
  const c = mvs[1] ? await grabFrame(mvs[1], tc, 'raw') : b;
  console.log(`\nDeterminism at t=${tc}: ${md5(a)} / after seek ${md5(b)} / other page ${md5(c)} => ${md5(a) === md5(b) && md5(b) === md5(c) ? 'OK' : 'NOT DETERMINISTIC'}`);

  // parallel scaling (raw transport, no encoding)
  console.log(`\nParallel pages (transport ${opt.transport}, no encoding):`);
  for (let w = 1; w <= mvs.length; w++) {
    const t0 = performance.now();
    await produce(mvs.slice(0, w), 0, n, (i) => times[i], opt.transport, async () => {});
    const s = (performance.now() - t0) / 1000;
    console.log(`  ${w} page(s): ${(n / s).toFixed(2)} frames/s`);
  }
}

// ------------------------------------------------------------------ main
async function main() {
  const r = await resolveUrl(opt);
  server = r.server;
  const url = r.url;
  console.log(`[render] page ${url}${server ? `  (serving ${path.resolve(opt.root)})` : ''}`);
  browser = await launchBrowser({ chrome: opt.chrome, gpu: opt.gpu });
  const openOpts = { timeout: opt.timeout * 1000, allowConsoleErrors: opt.allowConsoleErrors };
  const tLoad = Date.now();
  const first = await openMV(browser, url, openOpts);
  const info = first.info;
  const workers = opt.bench ? Math.max(opt.workers, 1) : opt.workers;
  const mvs = [first, ...await Promise.all(Array.from({ length: workers - 1 }, () => openMV(browser, url, openOpts)))];
  console.log(`[render] MV ready on ${mvs.length} page(s) in ${((Date.now() - tLoad) / 1000).toFixed(1)}s — ` +
    `MV.duration=${info.duration}, canvas ${info.width}x${info.height} at (${info.rect.x},${info.rect.y})`);
  if (info.width !== 1920 || info.height !== 1080) console.warn(`warning: canvas is ${info.width}x${info.height}, expected 1920x1080`);
  if (info.fps && info.fps !== opt.fps) console.warn(`note: timeline fps is ${info.fps}, rendering at --fps ${opt.fps}`);

  const start = opt.start;
  const end = opt.end ?? info.duration;
  if (!Number.isFinite(end)) throw new Error('MV.duration is not a number; pass --end');
  if (!(end > start)) throw new Error(`--end (${end}) must be greater than --start (${start})`);
  const fps = opt.fps;
  const total = Math.round((end - start) * fps);
  const tOf = (i) => start + i / fps; // global frame index -> MV time (same in chunked and single mode)

  if (total < 1) throw new Error(`range [${start}, ${end}) contains no frame at ${fps} fps`);
  if (opt.bench) { await bench(mvs, start, end); return; }

  if (!LOSSLESS.has(opt.transport)) console.warn(`note: transport "${opt.transport}" is lossy (quality ${jpegQ})`);
  console.log(`[render] ${total} frames  t=[${start}, ${end})  ${fps} fps  transport=${opt.transport}  workers=${mvs.length}  ` +
    `x264 crf ${opt.crf} preset ${opt.preset}  scale ${opt.scale}`);

  // Guard: all worker pages must produce bit-identical pixels (catches non-pure render code, and page files
  // that changed while the workers were loading).
  if (!opt.noCheck) {
    const probes = [...new Set([tOf(0), tOf(Math.floor(total / 2)), tOf(total - 1)])];
    for (const t of probes) {
      const hashes = [];
      for (const mv of mvs) for (let k = 0; k < (mvs.length === 1 ? 2 : 1); k++) hashes.push(md5(await grabFrame(mv, t, 'raw')));
      if (new Set(hashes).size !== 1) {
        throw new Error(`determinism check failed at t=${t}: pages rendered different pixels (${hashes.join(' ')}). ` +
          'MV.render(t) must be a pure function of t (and page files must not change during load). Use --no-check to skip.');
      }
    }
    console.log(`[render] determinism check OK (${probes.length} probe frames x ${mvs.length} page(s))`);
  }

  await fsp.mkdir(path.dirname(OUT), { recursive: true });
  const silent = opt.audio ? OUT.replace(/(\.mp4)?$/i, '.silent.mp4') : OUT;
  prog.total = total; prog.t = start; prog.t0 = Date.now();
  startProgress();

  if (opt.chunk > 0) {
    const chunkFrames = Math.max(1, Math.round(opt.chunk * fps));
    const n = Math.ceil(total / chunkFrames);
    const dir = path.resolve(opt.chunkDir ?? path.join(path.dirname(OUT), 'chunks'));
    await fsp.mkdir(dir, { recursive: true });
    const u = new URL(url);
    const manifest = {
      page: u.pathname + u.search, start, fps, chunkFrames, crf: opt.crf, preset: opt.preset, scale: String(opt.scale),
      transport: LOSSLESS.has(opt.transport) ? 'lossless' : `jpeg@${jpegQ}`, width: info.width, height: info.height,
    };
    const mfile = path.join(dir, 'manifest.json');
    const chunkFiles = (await fsp.readdir(dir)).filter((f) => /^\d+\.mp4(\.part)?$/.test(f));
    if (opt.fresh) {
      for (const f of chunkFiles) await fsp.rm(path.join(dir, f), { force: true });
    } else if (fs.existsSync(mfile) && chunkFiles.length) {
      const old = JSON.parse(await fsp.readFile(mfile, 'utf8'));
      const diffs = Object.keys(manifest).filter((k) => JSON.stringify(old[k]) !== JSON.stringify(manifest[k]));
      if (diffs.length) {
        throw new Error(`existing chunks in ${dir} were rendered with different settings (` +
          diffs.map((k) => `${k}: ${JSON.stringify(old[k])} -> ${JSON.stringify(manifest[k])}`).join(', ') +
          `). Re-run with --fresh to discard them, or use --chunk-dir.`);
      }
    }
    for (const f of chunkFiles.filter((f) => f.endsWith('.part'))) await fsp.rm(path.join(dir, f), { force: true });
    await fsp.writeFile(mfile, JSON.stringify(manifest, null, 2) + '\n');

    const files = [];
    let skipped = 0;
    for (let c = 0; c < n; c++) {
      const i0 = c * chunkFrames, i1 = Math.min(total, i0 + chunkFrames);
      const file = path.join(dir, String(c).padStart(3, '0') + '.mp4');
      files.push(file);
      if (fs.existsSync(file)) {
        const have = await probeFrameCount(file);
        if (have === i1 - i0) { prog.done += i1 - i0; skipped++; continue; }
        console.warn(`[render] chunk ${path.basename(file)} has ${have} frames, expected ${i1 - i0} — re-rendering`);
        await fsp.rm(file, { force: true });
      }
      prog.label = `chunk ${c + 1}/${n}`;
      if (!prog.tRender) prog.tRender = Date.now();
      await encodeRange(mvs, info, i0, i1, tOf, file + '.part');
      await fsp.rename(file + '.part', file);
    }
    if (skipped) console.log(`[render] resumed: ${skipped}/${n} chunks already complete`);
    stopProgress();
    console.log(progressLine());
    const list = path.join(dir, 'concat.txt');
    await fsp.writeFile(list, files.map((f) => `file '${f.replace(/'/g, "'\\''")}'`).join('\n') + '\n');
    console.log(`[render] concatenating ${n} chunks -> ${silent}`);
    await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list,
      '-c', 'copy', '-movflags', '+faststart', '-f', 'mp4', silent + '.part']);
    await fsp.rename(silent + '.part', silent);
  } else {
    prog.tRender = Date.now();
    await encodeRange(mvs, info, 0, total, tOf, silent + '.part');
    await fsp.rename(silent + '.part', silent);
    stopProgress();
    console.log(progressLine());
  }

  const got = await probeFrameCount(silent);
  if (got !== total) throw new Error(`output has ${got} frames, expected ${total}`);

  if (opt.audio) {
    console.log(`[render] muxing audio ${opt.audio} (offset ${opt.audioOffset}s, start ${start}s) -> ${OUT}`);
    await muxAudio(silent, opt.audio, OUT, { offset: opt.audioOffset, start });
    await fsp.rm(silent, { force: true });
  }
  const el = (Date.now() - prog.t0) / 1000;
  const size = (await fsp.stat(OUT)).size;
  console.log(`[render] done: ${OUT}  ${total} frames, ${(size / 1048576).toFixed(1)} MB, ${fmtTime(el)} ` +
    `(${prog.fresh ? (prog.fresh / ((Date.now() - (prog.tRender || prog.t0)) / 1000)).toFixed(2) : '-'} fps rendered this run)`);
}

let code = 0;
try {
  await main();
} catch (e) {
  stopProgress();
  console.error(`\n[render] FAILED: ${e.message}`);
  code = 1;
}
await shutdown();
process.exit(code);
