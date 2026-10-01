// Shared helpers for render.mjs and sheet.mjs (no external deps besides Playwright).
import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const RENDER_DIR = path.dirname(fileURLToPath(import.meta.url));
export const MV_ROOT = path.resolve(RENDER_DIR, '..');
export const DEFAULT_URL = 'http://localhost:8765/index.html?render=1';
export const DEFAULT_CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PW_FALLBACK = '/opt/node-tools/node_modules/playwright/index.mjs';

// ---------------------------------------------------------------- misc utils
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function fmtTime(sec) {
  if (!Number.isFinite(sec)) return '--:--';
  sec = Math.max(0, sec);
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.floor(sec % 60);
  return (h ? h + ':' + String(m).padStart(2, '0') : String(m).padStart(2, '0')) + ':' + String(s).padStart(2, '0');
}

/** mm:ss.ff timecode (ff = hundredths) */
export function timecode(t) {
  const m = Math.floor(t / 60), s = t - m * 60;
  return String(m).padStart(2, '0') + ':' + s.toFixed(2).padStart(5, '0');
}

export function fail(msg, code = 2) {
  console.error(`error: ${msg}`);
  process.exit(code);
}

// ---------------------------------------------------------------- playwright
export async function loadChromium() {
  try {
    return (await import('playwright')).chromium;
  } catch { /* fall through */ }
  try {
    return (await import(pathToFileURL(PW_FALLBACK).href)).chromium;
  } catch (e) {
    throw new Error(`Playwright not found. Run "npm install" in ${RENDER_DIR} (or install playwright globally). (${e.message})`);
  }
}

export async function launchBrowser({ chrome, gpu = false } = {}) {
  const chromium = await loadChromium();
  let executablePath = chrome;
  if (!executablePath && fs.existsSync(DEFAULT_CHROME)) executablePath = DEFAULT_CHROME;
  const args = [
    '--no-sandbox',
    '--force-color-profile=srgb', // identical colours in screenshots / pixel reads
    '--hide-scrollbars',
    '--mute-audio',
    // parallel workers are separate tabs; keep all of them at full speed
    '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding',
    '--disable-backgrounding-occluded-windows',
  ];
  if (!gpu) args.push('--disable-gpu'); // software canvas: faster readback in headless, see README
  return chromium.launch({ executablePath, args, headless: true });
}

/**
 * Open the MV page, wait for MV.ready, install the in-page frame grabber.
 * Returns { context, page, cdp, errors, warnings, info }.
 * `errors` collects page errors / console errors / failed requests; callers must check it.
 */
export async function openMV(browser, url, { timeout = 180000, allowConsoleErrors = false, log = (s) => console.error(s) } = {}) {
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  const warnings = [];
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.stack || e.message || e}`));
  const isFavicon = (u) => /\/favicon\.ico(\?|$)/.test(u || ''); // browser-initiated, irrelevant to frames
  page.on('console', (m) => {
    const type = m.type();
    if (type === 'error') {
      const loc = m.location();
      if (isFavicon(loc && loc.url)) return;
      const s = `console.error: ${m.text()}${loc && loc.url ? ` (${loc.url}:${loc.lineNumber})` : ''}`;
      if (allowConsoleErrors) { warnings.push(s); log(`[page] ${s}`); } else errors.push(s);
    } else if (type === 'warning') {
      warnings.push(`console.warn: ${m.text()}`);
    }
  });
  page.on('crash', () => errors.push('page crashed (renderer process died — out of memory?)'));
  page.on('requestfailed', (r) => {
    const why = r.failure()?.errorText || '';
    const s = `request failed: ${r.url()} (${why})`;
    if (/ERR_ABORTED/.test(why)) warnings.push(s); else errors.push(s);
  });
  page.on('response', (r) => { if (r.status() >= 400 && !isFavicon(r.url())) errors.push(`HTTP ${r.status()}: ${r.url()}`); });

  try {
    await page.goto(url, { waitUntil: 'load', timeout });
  } catch (e) {
    const hint = /ERR_CONNECTION_REFUSED/.test(e.message) ? ' — is a server running? Use --serve to start one.' : '';
    throw new Error(`cannot load ${url}: ${e.message.split('\n')[0]}${hint}`);
  }
  try {
    await page.waitForFunction(() => window.MV && window.MV.ready && typeof window.MV.render === 'function', null, { timeout });
  } catch {
    throw new Error(`window.MV (with .ready and .render) did not appear within ${timeout / 1000}s` + (errors.length ? `\n  ${errors.join('\n  ')}` : ''));
  }
  const r = await page.evaluate((ms) => Promise.race([
    Promise.resolve(window.MV.ready).then(() => 'ok', (e) => 'rejected: ' + (e && (e.stack || e.message) || e)),
    new Promise((res) => setTimeout(() => res('timeout'), ms)),
  ]), timeout);
  if (r !== 'ok') throw new Error(`MV.ready ${r === 'timeout' ? `did not resolve within ${timeout / 1000}s` : r}`);

  const info = await page.evaluate(() => {
    const MV = window.MV;
    const c = (MV.canvas instanceof HTMLCanvasElement && MV.canvas) || document.querySelector('canvas');
    if (!c) return { error: 'no <canvas> found on the page' };
    window.__mvCanvas = c;
    const rect = c.getBoundingClientRect();
    // in-page grabber: render frame t then return the frame in the requested encoding
    const b64 = (u8) => {
      if (typeof u8.toBase64 === 'function') return u8.toBase64();
      let s = '';
      for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      return btoa(s);
    };
    let ctx2d;
    window.__mvGrab = async (t, mode, quality) => {
      const ret = MV.render(t);
      if (ret && typeof ret.then === 'function') await ret;
      if (mode === 'none') return null;
      if (mode === 'png') return c.toDataURL('image/png');
      if (mode === 'jpeg') return c.toDataURL('image/jpeg', quality);
      if (mode === 'raw' || mode === 'post') {
        if (ctx2d === undefined) {
          ctx2d = c.getContext('2d');
          if (!ctx2d) { // WebGL canvas: copy into a 2D helper in the same task
            const h = document.createElement('canvas'); h.width = c.width; h.height = c.height;
            ctx2d = { helper: h.getContext('2d', { willReadFrequently: true }) };
          }
        }
        let d;
        if (ctx2d.helper) { ctx2d.helper.clearRect(0, 0, c.width, c.height); ctx2d.helper.drawImage(c, 0, 0); d = ctx2d.helper.getImageData(0, 0, c.width, c.height).data; }
        else d = ctx2d.getImageData(0, 0, c.width, c.height).data;
        const u8 = new Uint8Array(d.buffer, d.byteOffset, d.byteLength);
        if (mode === 'raw') return b64(u8);
        // binary side channel: POST the pixels to the renderer's frame sink (no base64, no CDP payload)
        // (a Blob body is ~10x faster than a typed-array body, which Chromium copies through the DevTools network layer)
        await fetch(quality, { method: 'POST', body: new Blob([u8]), mode: 'no-cors', cache: 'no-store' });
        return u8.length;
      }
      throw new Error('unknown grab mode ' + mode);
    };
    const meta = (MV.timeline && MV.timeline.meta) || {};
    return {
      duration: Number(MV.duration),
      width: c.width, height: c.height,
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      fps: meta.fps || null,
      sections: Array.isArray(MV.timeline && MV.timeline.sections)
        ? MV.timeline.sections.map((s) => ({ id: s.id, start: s.start, end: s.end })) : [],
      nativeBase64: typeof Uint8Array.prototype.toBase64 === 'function',
    };
  });
  if (info.error) throw new Error(info.error);
  if (errors.length) throw new Error(`page reported errors while loading:\n  ${errors.join('\n  ')}`);
  const cdp = await context.newCDPSession(page);
  return { context, page, cdp, errors, warnings, info };
}

// ---------------------------------------------------------------- frame transports
// Lossless: raw (getImageData RGBA POSTed to a local sink), raw-cdp (same pixels as base64 through CDP),
//           png (canvas.toDataURL), cdp / cdp-fast (Page.captureScreenshot), screenshot (page.screenshot)
// Lossy:    jpeg (canvas.toDataURL jpeg)
export const TRANSPORTS = ['raw', 'raw-cdp', 'png', 'cdp', 'cdp-fast', 'screenshot', 'jpeg'];
export const LOSSLESS = new Set(['raw', 'raw-cdp', 'png', 'cdp', 'cdp-fast', 'screenshot']);
export const isRaw = (tr) => tr === 'raw' || tr === 'raw-cdp';

// Frame sink: tiny HTTP server receiving raw RGBA bodies from the page (POST /f/<id>).
let sinkPromise = null;
function getSink() {
  sinkPromise ??= new Promise((resolve, reject) => {
    const received = new Map();
    const server = http.createServer((req, res) => {
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Private-Network', 'true');
      if (req.method === 'OPTIONS') { res.setHeader('Access-Control-Allow-Methods', 'POST'); res.writeHead(204); return res.end(); }
      const m = /^\/f\/([\w-]+)$/.exec(req.url);
      if (req.method !== 'POST' || !m) { res.writeHead(404); return res.end(); }
      const len = +req.headers['content-length'];
      const chunks = []; let got = 0;
      req.on('data', (d) => { chunks.push(d); got += d.length; });
      req.on('end', () => {
        received.set(m[1], chunks.length === 1 ? chunks[0] : Buffer.concat(chunks, got));
        if (len && got !== len) received.set(m[1], new Error(`short upload ${got}/${len}`));
        res.writeHead(204); res.end();
      });
    });
    server.keepAliveTimeout = 60000;
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve({
      url: `http://127.0.0.1:${server.address().port}/f/`,
      take(id) { const b = received.get(id); received.delete(id); return b; },
      close: () => new Promise((r) => { server.closeAllConnections?.(); server.close(() => r()); }),
    }));
  });
  return sinkPromise;
}
export async function closeSink() { if (sinkPromise) { const s = await sinkPromise; sinkPromise = null; await s.close(); } }
let frameSeq = 0;

const dataUrlToBuffer = (s) => Buffer.from(s.slice(s.indexOf(',') + 1), 'base64');

/** Render frame t on `mv` (result of openMV) and return it as a Buffer in the transport's format. */
export async function grabFrame(mv, t, transport, jpegQuality = 0.92) {
  try {
    return await grabFrameInner(mv, t, transport, jpegQuality);
  } catch (e) {
    if (/^page error at t=/.test(e.message)) throw e;
    const msg = String(e.message || e).replace(/^page\.evaluate: /, '').split('\n')
      .filter((l) => !/UtilityScript|eval at evaluate|__mvGrab/.test(l)).slice(0, 8).join('\n    ');
    const extra = mv.errors.length ? `\n  ${mv.errors.join('\n  ')}` : '';
    throw new Error(`frame t=${t.toFixed(3)} failed (MV.render or capture threw):\n    ${msg}${extra}`);
  }
}

async function grabFrameInner(mv, t, transport, jpegQuality) {
  const { page, cdp, info } = mv;
  let buf;
  switch (transport) {
    case 'raw': {
      const sink = await getSink();
      const id = String(++frameSeq);
      await page.evaluate(([t, u]) => window.__mvGrab(t, 'post', u), [t, sink.url + id]);
      buf = sink.take(id);
      if (!buf) throw new Error(`frame t=${t} was not received by the frame sink`);
      if (buf instanceof Error) throw buf;
      break;
    }
    case 'raw-cdp':
      buf = Buffer.from(await page.evaluate(([t]) => window.__mvGrab(t, 'raw'), [t]), 'base64');
      break;
    case 'png':
      buf = dataUrlToBuffer(await page.evaluate(([t]) => window.__mvGrab(t, 'png'), [t]));
      break;
    case 'jpeg':
      buf = dataUrlToBuffer(await page.evaluate(([t, q]) => window.__mvGrab(t, 'jpeg', q), [t, jpegQuality]));
      break;
    case 'none':
      await page.evaluate(([t]) => window.__mvGrab(t, 'none'), [t]);
      buf = Buffer.alloc(0);
      break;
    case 'cdp':
    case 'cdp-fast': {
      await page.evaluate(([t]) => window.__mvGrab(t, 'none'), [t]);
      const { x, y, width, height } = info.rect;
      const { data } = await cdp.send('Page.captureScreenshot', {
        format: 'png', clip: { x, y, width, height, scale: 1 }, captureBeyondViewport: false,
        optimizeForSpeed: transport === 'cdp-fast',
      });
      buf = Buffer.from(data, 'base64');
      break;
    }
    case 'screenshot': {
      await page.evaluate(([t]) => window.__mvGrab(t, 'none'), [t]);
      buf = await page.screenshot({ type: 'png', clip: info.rect, animations: 'allow', caret: 'initial', scale: 'css' });
      break;
    }
    default:
      throw new Error(`unknown transport "${transport}" (choose: ${TRANSPORTS.join(', ')})`);
  }
  if (mv.errors.length) throw new Error(`page error at t=${t.toFixed(3)}:\n  ${mv.errors.join('\n  ')}`);
  return buf;
}

// ---------------------------------------------------------------- static server
const MIME = {
  '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8', '.md': 'text/markdown; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.flac': 'audio/flac',
  '.mp4': 'video/mp4', '.webm': 'video/webm',
};

/** Minimal static file server (GET/HEAD, single Range). Resolves { port, close }. */
export function startServer(root, { port = 0, host = '127.0.0.1' } = {}) {
  root = path.resolve(root);
  const server = http.createServer(async (req, res) => {
    try {
      const u = new URL(req.url, 'http://localhost');
      let p = decodeURIComponent(u.pathname);
      if (p === '/favicon.ico') { res.writeHead(204); return res.end(); }
      if (p.endsWith('/')) p += 'index.html';
      const fp = path.resolve(root, '.' + p);
      if (fp !== root && !fp.startsWith(root + path.sep)) { res.writeHead(403); return res.end('forbidden'); }
      let st = await fsp.stat(fp).catch(() => null);
      if (st && st.isDirectory()) { res.writeHead(301, { Location: u.pathname + '/' + u.search }); return res.end(); }
      if (!st) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('not found'); }
      const headers = {
        'Content-Type': MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-store', 'Accept-Ranges': 'bytes',
      };
      let start = 0, end = st.size - 1, status = 200;
      const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
      if (m && (m[1] || m[2])) {
        if (m[1]) { start = +m[1]; if (m[2]) end = Math.min(+m[2], end); } else { start = Math.max(0, st.size - +m[2]); }
        if (start > end) { res.writeHead(416, { 'Content-Range': `bytes */${st.size}` }); return res.end(); }
        status = 206; headers['Content-Range'] = `bytes ${start}-${end}/${st.size}`;
      }
      headers['Content-Length'] = end - start + 1;
      res.writeHead(status, headers);
      if (req.method === 'HEAD') return res.end();
      fs.createReadStream(fp, { start, end }).on('error', () => res.destroy()).pipe(res);
    } catch (e) {
      res.writeHead(500); res.end(String(e));
    }
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, () => {
      const p = server.address().port;
      resolve({ port: p, host, close: () => new Promise((r) => { server.closeAllConnections?.(); server.close(() => r()); }) });
    });
  });
}

/** Resolve the page URL; with --serve start our own server and keep only path+query of --url. */
export async function resolveUrl({ url = DEFAULT_URL, serve = false, root = MV_ROOT, port = 0 } = {}) {
  let server = null;
  if (serve) {
    server = await startServer(root, { port });
    const u = new URL(url, 'http://localhost/');
    url = `http://${server.host}:${server.port}${u.pathname}${u.search}`;
  }
  if (!/[?&]render=1\b/.test(url)) console.warn(`warning: URL has no "render=1" parameter — the page may show UI / run its own animation loop: ${url}`);
  return { url, server };
}

// ---------------------------------------------------------------- ffmpeg helpers
/** Spawn ffmpeg with a writable stdin. Returns { child, stdin, done: Promise, stderr() }. */
export function spawnFfmpeg(args) {
  const child = spawn('ffmpeg', args, { stdio: ['pipe', 'ignore', 'pipe'] });
  let err = '';
  child.stderr.on('data', (d) => { err += d; if (err.length > 20000) err = err.slice(-20000); });
  let exited = null;
  const done = new Promise((resolve, reject) => {
    child.on('error', (e) => { exited = e; reject(new Error(`cannot start ffmpeg: ${e.message}`)); });
    child.on('close', (code, sig) => {
      exited = code ?? sig;
      if (code === 0) resolve(); else reject(new Error(`ffmpeg exited with ${code ?? sig}\n${err.trim()}`));
    });
  });
  done.catch(() => {}); // observed by callers
  child.stdin.on('error', () => {}); // EPIPE surfaces through `done`
  return {
    child, done,
    get exited() { return exited; },
    stderr: () => err,
    /** write with backpressure */
    async write(buf) {
      if (exited !== null) { await done; throw new Error('ffmpeg already exited'); }
      if (!child.stdin.write(buf)) {
        await new Promise((resolve, reject) => {
          const ok = () => { cleanup(); resolve(); };
          const bad = () => { cleanup(); done.then(() => reject(new Error('ffmpeg closed stdin')), reject); };
          const cleanup = () => { child.stdin.off('drain', ok); child.off('close', bad); };
          child.stdin.once('drain', ok); child.once('close', bad);
        });
      }
    },
    async end() { child.stdin.end(); await done; },
    kill() { try { child.kill('SIGKILL'); } catch { /* */ } },
  };
}

/** Run a command to completion; resolves stdout, rejects with stderr. */
export function run(cmd, args, { quiet = true } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { err += d; if (!quiet) process.stderr.write(d); });
    child.on('error', (e) => reject(new Error(`cannot run ${cmd}: ${e.message}`)));
    child.on('close', (code) => code === 0 ? resolve(out) : reject(new Error(`${cmd} exited with ${code}\n${err.trim().slice(-4000)}`)));
  });
}

/** Number of video packets (= frames) in a file, or -1 if unreadable. Fast: no decoding. */
export async function probeFrameCount(file) {
  try {
    const out = await run('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_packets',
      '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', file]);
    const n = parseInt(out.trim(), 10);
    return Number.isFinite(n) ? n : -1;
  } catch { return -1; }
}

/** libx264 encoder args for a frame stream on stdin. */
export function encodeArgs({ transport, fps, width, height, crf, preset, scale, out, format, threads }) {
  const input = isRaw(transport)
    ? ['-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${width}x${height}`, '-framerate', String(fps), '-i', '-']
    : ['-f', 'image2pipe', '-framerate', String(fps), '-c:v', transport === 'jpeg' ? 'mjpeg' : 'png', '-i', '-'];
  return [
    '-hide_banner', '-nostats', '-loglevel', 'error', '-y',
    ...input,
    '-an', '-vf', scaleFilter(scale),
    '-c:v', 'libx264', '-preset', preset, '-crf', String(crf), '-pix_fmt', 'yuv420p',
    ...(threads ? ['-threads', String(threads)] : []),
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-movflags', '+faststart',
    ...(format ? ['-f', format] : []),
    out,
  ];
}

/** RGB -> BT.709 limited-range YUV 4:2:0, optionally downscaled. --scale 720 => scale=1280:-2 */
export function scaleFilter(scale) {
  const cs = 'out_color_matrix=bt709:out_range=tv';
  const s = String(scale || '1080');
  if (s === '1080') return `scale=${cs}:flags=bicubic+accurate_rnd,format=yuv420p`;
  if (s === '720') return `scale=1280:-2:${cs}:flags=lanczos+accurate_rnd,format=yuv420p`;
  if (/^\d+$/.test(s)) return `scale=-2:${s}:${cs}:flags=lanczos+accurate_rnd,format=yuv420p`;
  throw new Error(`--scale must be 1080, 720 or a pixel height, got "${scale}"`);
}

/** Audio input args so that video time 0 (= MV time `start`) lines up with MV's `t = audioTime + offset`. */
export function audioInputArgs(audio, { offset = 0, start = 0 }) {
  const shift = offset - start; // >0: audio starts later than video; <0: skip into the audio
  if (Math.abs(shift) < 1e-6) return ['-i', audio];
  if (shift > 0) return ['-itsoffset', shift.toFixed(6), '-i', audio];
  return ['-ss', (-shift).toFixed(6), '-i', audio];
}

export async function muxAudio(video, audio, out, { offset = 0, start = 0 } = {}) {
  await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', video, ...audioInputArgs(audio, { offset, start }),
    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest',
    '-movflags', '+faststart', out]);
}

/** Simple --flag value parser on top of util.parseArgs semantics, with typed defaults. */
export function parseCli(argv, spec) {
  const out = {};
  for (const [k, v] of Object.entries(spec)) out[k] = v.default;
  for (let i = 0; i < argv.length; i++) {
    let a = argv[i];
    if (!a.startsWith('--')) fail(`unexpected argument "${a}" (see --help)`);
    a = a.slice(2);
    let val;
    const eq = a.indexOf('=');
    if (eq >= 0) { val = a.slice(eq + 1); a = a.slice(0, eq); }
    const key = a.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const s = spec[key];
    if (!s) fail(`unknown option --${a} (see --help)`);
    if (s.type === 'boolean') {
      out[key] = val === undefined ? true : !/^(0|false|no)$/i.test(val);
      continue;
    }
    if (val === undefined) {
      if (s.optionalValue && (i + 1 >= argv.length || argv[i + 1].startsWith('--'))) { out[key] = s.optionalValue; continue; }
      if (i + 1 >= argv.length) fail(`--${a} needs a value`);
      val = argv[++i];
    }
    if (s.type === 'number') {
      const n = Number(val);
      if (!Number.isFinite(n)) fail(`--${a} expects a number, got "${val}"`);
      out[key] = n;
    } else out[key] = val;
  }
  return out;
}
