// engine.js — loader, timeline, time→scene dispatch, global warmth w(t), persistent overlays, player.
import * as fx from './fx.js';
import { SCENES, TRANSITIONS, prepareScenes, drawBug } from './scenes.js';

const { W, H, P, clamp, lerp, inv, smooth, ease } = fx;
const MV = window.MV || (window.MV = { duration: 400, config: { showZh: true, grain: true, offset: 0 } });
MV.duration = 400;
MV.config = Object.assign({ showZh: true, grain: true, offset: 0 }, MV.config || {});
const RENDER = new URLSearchParams(location.search).get('render') === '1';

const canvas = document.getElementById('mv');
canvas.width = W; canvas.height = H;
// In render mode every frame is read back (toDataURL / screenshots). Chrome migrates a canvas from GPU to CPU
// raster after a few readbacks, which changes anti-aliasing slightly — so pin the CPU backend from frame 0 for
// bit-identical frames regardless of render order.
const ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: RENDER });
fx.setCanvasOptions(RENDER ? { willReadFrequently: true } : {});
let TL = null, A = null, SECS = [], LINES = [];
let ready = false;
const dissolveBuf = fx.makeCanvas(W, H);
const dctx = dissolveBuf.getContext('2d', { alpha: false, willReadFrequently: RENDER });

/* ------------------------------------------------------------ warmth w(t) */
// piecewise-linear keypoints [t, w] (STORYBOARD §0/§4)
const WK = [
  [0, 0], [43.08, 0], [43.09, 0.05], [64.71, 0.05], [64.72, 0.1],
  [120.4, 0.1], [126.0, 0.3], [152.99, 0.3], [153.0, 0], [170.19, 0], [170.2, 0.1],
  [193.0, 0.1], [196.02, 0.18], [196.03, 0.3], [217.1, 0.4], [217.7, 0.52], [238.06, 0.6],
  [238.065, 1.0], [253.9, 1.0], [261.8, 0.85], [261.84, 0.8], [326.18, 0.8], [326.19, 1.0], [400, 1.0],
];
export function warmth(t) {
  if (t <= WK[0][0]) return WK[0][1];
  for (let i = 1; i < WK.length; i++) {
    if (t <= WK[i][0]) { const [t0, w0] = WK[i - 1], [t1, w1] = WK[i]; return lerp(w0, w1, (t - t0) / (t1 - t0)); }
  }
  return WK[WK.length - 1][1];
}

/* ---------------------------------------------------------------- loading */
function loadImage(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error('image failed: ' + src));
    im.src = src;
  });
}
const FONT_FACES = [
  ['400 32px "Zen Old Mincho"', '機械の声'], ['700 32px "Zen Old Mincho"', '機械の声'], ['900 32px "Zen Old Mincho"', '機械の声'],
  ['400 32px "Shippori Mincho B1"', '機械の声'], ['800 32px "Shippori Mincho B1"', '機械の声'],
  ['400 32px "Zen Kaku Gothic New"', '機械の声'], ['700 32px "Zen Kaku Gothic New"', '機械の声'], ['900 32px "Zen Kaku Gothic New"', '機械の声'],
  ['400 32px "DotGothic16"', '智械 BOOT'], ['400 32px "Share Tech Mono"', 'BOOT 0123'],
  ['700 32px "Orbitron"', 'feat'], ['400 32px "Orbitron"', 'feat'],
  ['400 32px "Cormorant Garamond"', 'Voice'], ['italic 400 32px "Cormorant Garamond"', 'The Voice of AI'],
  ['400 32px "MV Noto Sans SC"', '机械的声音'],
];
async function loadFonts() {
  const out = await Promise.all(FONT_FACES.map(([f, s]) => document.fonts.load(f, s).then((r) => [f, r.length])));
  const missing = out.filter(([, n]) => !n).map(([f]) => f);
  if (missing.length) console.warn('fonts not matched:', missing);
  await document.fonts.ready;
}

async function loadAssets() {
  const names = ['char_full', 'char_full_1080', 'char_mono', 'char_silhouette', 'char_silhouette_ink', 'char_edges', 'char_face', 'char_bust', 'char_book'];
  const imgs = {};
  await Promise.all(names.map(async (n) => {
    try { imgs[n] = await loadImage(`assets/${n}.png`); } catch (e) { imgs[n] = null; }
  }));
  if (!imgs.char_full) {
    // scaffold fallback: derive a cutout from the source jpg (white background keyed out)
    const src = await loadImage('assets/zhixie_source.jpg');
    imgs.char_full = keyOutWhite(src);
  }
  return imgs;
}
function keyOutWhite(img) {
  const c = fx.makeCanvas(img.width, img.height), x = c.getContext('2d');
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height), p = d.data;
  for (let i = 0; i < p.length; i += 4) {
    const m = Math.min(p[i], p[i + 1], p[i + 2]);
    if (m > 236) p[i + 3] = Math.max(0, 255 - (m - 236) * 13);
  }
  x.putImageData(d, 0, 0);
  return c;
}

/** build all cached layers (offscreen canvases) once */
function buildCaches(im) {
  const full = im.char_full;
  const ASP = full.width / full.height;
  const h = 1000, w = Math.round(h * ASP);
  const scaleTo = (img) => { const c = fx.makeCanvas(w, h), x = c.getContext('2d'); x.imageSmoothingQuality = 'high'; x.drawImage(img, 0, 0, w, h); return c; };
  const derive = (fn) => { const c = fx.makeCanvas(full.width, full.height), x = c.getContext('2d'); fn(x, c); return c; };
  const mono = im.char_mono || derive((x) => { x.filter = 'grayscale(1) contrast(1.05)'; x.drawImage(full, 0, 0); });
  const sil = im.char_silhouette || fx.tinted(full, '#ffffff');
  const silInk = im.char_silhouette_ink || fx.tinted(full, P.ink);
  const edges = im.char_edges || derive((x) => { x.filter = 'grayscale(1) invert(1) contrast(3)'; x.drawImage(full, 0, 0); });
  const c = {};
  c.ASP = ASP; c.w = w; c.h = h;
  c.col = im.char_full_1080 && Math.abs(im.char_full_1080.height - h) < 2 ? im.char_full_1080 : scaleTo(full);
  c.mono = scaleTo(mono);
  // cold mono: 18% steel multiply, alpha restored
  c.monoCold = (() => {
    const k = fx.makeCanvas(w, h), x = k.getContext('2d');
    x.drawImage(c.mono, 0, 0);
    x.globalCompositeOperation = 'multiply'; x.fillStyle = fx.rgba(fx.mix('#ffffff', P.steel, 0.55)); x.fillRect(0, 0, w, h);
    x.globalCompositeOperation = 'destination-in'; x.drawImage(c.mono, 0, 0);
    return k;
  })();
  c.sil = scaleTo(sil); c.silInk = scaleTo(silInk); c.edges = scaleTo(edges);
  c.edgesWarm = fx.tinted(c.edges, P.gold);
  c.bloomS = fx.blurred(c.sil, 10, 60);
  c.bloomL = fx.blurred(c.sil, 36, 150);
  c.rim = fx.blurred(c.sil, 7, 40, P.orange);
  c.warmGlow = fx.blurred(c.sil, 46, 180, P.orangeL);
  c.paperGlow = fx.blurred(c.sil, 30, 140, P.paper);
  // hi-res sources for large draws
  c.hi = { col: full, mono, monoCold: null, sil, silInk, edges };
  // face / bust crops from the full-res cutout (feathered where the crop cuts through content)
  const fr = { x: 300, y: 0, w: 540, h: 560 };
  c.face = fx.featherCrop(full, fr.x, fr.y, fr.w, fr.h, { l: 50, r: 50, b: 160 });
  c.faceMono = fx.featherCrop(mono, fr.x, fr.y, fr.w, fr.h, { l: 50, r: 50, b: 160 });
  c.faceRect = fr;
  const br = { x: 200, y: 0, w: 700, h: 860 };
  c.bust = fx.featherCrop(full, br.x, br.y, br.w, br.h, { l: 30, r: 30, b: 200 });
  c.bustMono = fx.featherCrop(mono, br.x, br.y, br.w, br.h, { l: 30, r: 30, b: 200 });
  c.bustRect = br;
  c.book = im.char_book;
  const bk = { x: 236, y: 392, w: 230, h: 300 };
  c.bookCrop = fx.featherCrop(full, bk.x, bk.y, bk.w, bk.h, { r: 40, b: 40 });
  c.bookCropMono = fx.featherCrop(mono, bk.x, bk.y, bk.w, bk.h, { r: 40, b: 40 });
  c.bookRect = bk;
  c.full = full; c.monoFull = mono;
  // particle sample of the 1000-high colour cutout (for the outro dissolve)
  const sx = fx.makeCanvas(w, h).getContext('2d', { willReadFrequently: true });
  sx.drawImage(c.col, 0, 0);
  const data = sx.getImageData(0, 0, w, h);
  c.colData = data;
  const r = fx.rng('dissolve-sample');
  const pts = [];
  let guard = 0;
  while (pts.length < 2600 && guard < 400000) {
    guard++;
    const px = Math.floor(r() * w), py = Math.floor(r() * h);
    const i = (py * w + px) * 4;
    if (data.data[i + 3] > 200) pts.push({ x: px, y: py, c: [data.data[i], data.data[i + 1], data.data[i + 2]], r: r() });
  }
  c.pts = pts;
  // the book (+ the hand holding it) as a soft-masked cutout, used once she has dissolved
  const BOOK_POLY = [[244, 430], [350, 386], [384, 396], [442, 612], [436, 628], [372, 656], [368, 688], [300, 694], [258, 672], [256, 604], [288, 560], [292, 532], [258, 462]];
  const bb = { x: 236, y: 378, w: 214, h: 324 };
  c.bookOnly = (() => {
    const k = fx.makeCanvas(bb.w, bb.h), x = k.getContext('2d');
    x.filter = 'blur(1.5px)'; x.fillStyle = '#000';
    x.beginPath(); BOOK_POLY.forEach(([px, py], i) => (i ? x.lineTo(px - bb.x, py - bb.y) : x.moveTo(px - bb.x, py - bb.y))); x.closePath(); x.fill();
    x.filter = 'none'; x.globalCompositeOperation = 'source-in';
    x.drawImage(full, bb.x, bb.y, bb.w, bb.h, 0, 0, bb.w, bb.h);
    return k;
  })();
  c.bookOnlyRect = bb;
  // erosion threshold map: top→bottom sweep + 2-octave lattice noise; the book polygon is excluded
  const sF = h / full.height;
  const pm = fx.makeCanvas(w, h).getContext('2d', { willReadFrequently: true });
  pm.fillStyle = '#000'; pm.beginPath();
  BOOK_POLY.forEach(([px, py], i) => (i ? pm.lineTo(px * sF, py * sF) : pm.moveTo(px * sF, py * sF))); pm.closePath(); pm.fill();
  const pmd = pm.getImageData(0, 0, w, h).data;
  const lattice = (cell, seed) => {
    const gw = Math.ceil(w / cell) + 2, gh = Math.ceil(h / cell) + 2, g = new Float32Array(gw * gh), r = fx.rng('lat', seed);
    for (let i = 0; i < g.length; i++) g[i] = r();
    return (x, y) => {
      const fx0 = x / cell, fy0 = y / cell, ix = Math.floor(fx0), iy = Math.floor(fy0), u = fx0 - ix, v = fy0 - iy;
      const su = u * u * (3 - 2 * u), sv = v * v * (3 - 2 * v);
      const a = g[iy * gw + ix], b2 = g[iy * gw + ix + 1], c2 = g[(iy + 1) * gw + ix], d = g[(iy + 1) * gw + ix + 1];
      return (a + (b2 - a) * su) * (1 - sv) + (c2 + (d - c2) * su) * sv;
    };
  };
  const n1 = lattice(22, 1), n2 = lattice(7, 2), n3 = lattice(3, 3);
  const thr = new Float32Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const n = n1(x, y) * 0.55 + n2(x, y) * 0.3 + n3(x, y) * 0.15;
      let v = (y / h) * 0.7 + n * 0.3;
      if (pmd[(y * w + x) * 4 + 3] > 128) v = 2;
      thr[y * w + x] = v;
    }
  }
  c.thr = thr;
  return c;
}

/* --------------------------------------------------------------- timeline */
function sectionIndexAt(t) {
  for (let i = SECS.length - 1; i >= 0; i--) if (t >= SECS[i].start) return i;
  return 0;
}
const fmtTC = (t) => {
  t = Math.max(0, t);
  const m = Math.floor(t / 60), s = Math.floor(t % 60), cs = Math.floor((t * 100) % 100);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(cs).padStart(2, '0')}`;
};

/* ----------------------------------------------------------------- render */
function sceneCtx(c, si, t) {
  const sec = SECS[si];
  const w = warmth(t);
  return {
    ctx: c, t, lt: t - sec.start, sec, si, p: clamp((t - sec.start) / (sec.end - sec.start)),
    w, A, TL, LINES, cfg: MV.config, fx, W, H,
  };
}
function drawScene(c, si, t) {
  fx.reset(c);
  const S = sceneCtx(c, si, t);
  const fn = SCENES[S.sec.id];
  let out = null;
  try { out = fn ? fn(S) : null; } catch (e) { console.error('scene', S.sec.id, e); }
  fx.reset(c);
  return out || {};
}

function render(t) {
  if (!ready) throw new Error('MV not ready');
  t = clamp(Number(t) || 0, 0, MV.duration);
  fx.reset(ctx);
  const si = sectionIndexAt(t);
  const sec = SECS[si];
  let opts = drawScene(ctx, si, t);
  const tr = TRANSITIONS[sec.id] || { type: 'cut' };
  const since = t - sec.start;
  // cross-dissolve: previous scene (rendered at the same t) fades out over the new one
  if (tr.type === 'dissolve' && si > 0 && since < tr.d) {
    drawScene(dctx, si - 1, t);
    const k = ease.inOutSine(clamp(since / tr.d));
    fx.blit(ctx, dissolveBuf, 0, 0, W, H, 1 - k);
  }
  // persistent overlays
  drawOverlays(t, si, opts);
  // designed hard cut: glitch burst + 2-frame flash
  if (tr.type === 'cut' && si > 0) cutFX(t, sec.start, tr, si);
  // inner cuts requested by the scene (e.g. bridge per-line hard cuts)
  if (opts.cuts) for (const cu of opts.cuts) cutFX(t, cu.t, cu, si * 100 + (cu.id || 0));
  if (opts.glitch) {
    const g = opts.glitch;
    if (g.slice) fx.sliceGlitch(ctx, g.slice, fx.hash('og', si, fx.bucket(t, 30)), g.sliceOpts || {});
    if (g.rgb) fx.rgbSplit(ctx, g.rgb);
  }
  // post: scanlines, grain, vignette
  fx.reset(ctx);
  const vig = opts.vignette == null ? 0.75 : opts.vignette;
  if (vig > 0) fx.vignette(ctx, vig);
  if (opts.warmVignette) fx.vignette(ctx, opts.warmVignette, opts.warmVignetteColour || P.brown);
  fx.scanlines(ctx, opts.scan == null ? 0.06 : opts.scan);
  if (MV.config.grain) fx.grain(ctx, t, opts.grain == null ? 0.05 : opts.grain);
  if (opts.after) { fx.reset(ctx); opts.after(ctx); }
  fx.reset(ctx);
}

function cutFX(t, t0, tr, seed) {
  const dt = t - t0;
  if (dt < -0.1 || dt > 0.42) return;
  // 2-frame flash (frames 0 and 1 at 30 fps)
  if (dt >= 0 && dt < 2 / 30) {
    const a = dt < 1 / 30 ? 0.85 : 0.4;
    ctx.save(); ctx.globalAlpha = a * (tr.flashA == null ? 1 : tr.flashA);
    ctx.fillStyle = tr.flash || P.paper; ctx.fillRect(0, 0, W, H); ctx.restore();
  }
  const k = dt < 0 ? (dt + 0.1) / 0.1 * 0.5 : Math.pow(1 - dt / 0.42, 1.6);
  const inten = k * (tr.glitch == null ? 1 : tr.glitch);
  if (inten > 0.02) {
    fx.sliceGlitch(ctx, inten, fx.hash('cut', seed, fx.bucket(t, 30)), { amp: 140, n: 18 });
    fx.rgbSplit(ctx, Math.round(2 + 7 * inten));
  }
}

function drawOverlays(t, si, opts) {
  const sec = SECS[si];
  const light = opts.tone === 'light';
  const w = warmth(t);
  const hud = light ? P.ink : fx.rgba(fx.mix(P.ice, P.gold, smooth(0.15, 0.8, w)));
  // top-left bug (from 43.085 on; the title scene animates it into place)
  const bugA = (opts.bugAlpha == null ? 1 : opts.bugAlpha) * (t >= 43.085 ? 1 : 0);
  // soft shadow keeps the persistent HUD legible over imagery
  ctx.save();
  ctx.shadowColor = light ? 'rgba(243,234,217,0.9)' : 'rgba(0,0,0,0.9)'; ctx.shadowBlur = 8;
  if (bugA > 0.01 && !opts.hideBug) drawBug(ctx, hud, bugA);
  // bottom-right timecode + section id
  const tcA = (opts.tcAlpha == null ? 1 : opts.tcAlpha) * smooth(1.0, 1.6, t) * (1 - smooth(395.5, 397.5, t));
  if (tcA > 0.01 && !opts.hideTC) {
    const lbl = `SEC.${String(si + 1).padStart(2, '0')} ${sec.id.toUpperCase()}`;
    ctx.save();
    ctx.globalAlpha = 0.5 * tcA;
    fx.label(ctx, fmtTC(t), W - 96, H - 96, { size: 16, align: 'right', color: hud, track: 0.1 });
    fx.label(ctx, lbl, W - 96, H - 96 - 24, { size: 14, align: 'right', color: hud, track: 0.16 });
    ctx.globalAlpha = 0.35 * tcA;
    ctx.fillStyle = hud;
    // dotted leader to the left of the timecode
    for (let i = 0; i < 16; i++) ctx.fillRect(W - 96 - 132 - i * 7, H - 96 - 6, 2, 2);
    ctx.fillRect(W - 96 - 132 - 16 * 7 - 6, H - 96 - 9, 8, 8);
    ctx.restore();
  }
  ctx.restore();
}


/* ---------------------------------------------------------------- startup */
async function init() {
  try {
    TL = await fetch('data/timeline.json').then((r) => r.json());
    MV.timeline = TL;
    SECS = TL.sections; LINES = TL.lines;
    const [imgs] = await Promise.all([loadAssets(), loadFonts()]);
    A = buildCaches(imgs);
    fx.buildPost();
    prepareScenes({ A, TL, LINES, SECS, warmth });
    MV.render = (t) => render(t);
    MV.warmth = warmth;
    MV.sections = SECS;
    ready = true;
    render(0);
    MV.__resolve && MV.__resolve(true);
    if (!RENDER) startPlayer();
    const ld = document.getElementById('loading'); if (ld) ld.remove();
  } catch (e) {
    console.error('MV init failed', e);
    MV.__reject && MV.__reject(e);
  }
}

/* ----------------------------------------------------------------- player */
function startPlayer() {
  const $ = (id) => document.getElementById(id);
  const ui = $('ui'); ui.hidden = false;
  const audio = $('audio');
  const seek = $('seek'), tc = $('tc'), play = $('play'), zh = $('zh'), off = $('off'), src = $('src');
  let hasAudio = false, dragging = false;
  const clock = { playing: false, base: 0, start: 0 };
  const media = () => (hasAudio ? audio.currentTime : clock.playing ? clock.base + (performance.now() - clock.start) / 1000 : clock.base);
  const isPlaying = () => (hasAudio ? !audio.paused : clock.playing);
  const setMedia = (m) => {
    m = clamp(m, 0, MV.duration);
    if (hasAudio) audio.currentTime = Math.min(m, audio.duration || m);
    else { clock.base = m; clock.start = performance.now(); }
  };
  const toggle = () => {
    if (hasAudio) { if (audio.paused) audio.play(); else audio.pause(); }
    else {
      if (clock.playing) { clock.base = media(); clock.playing = false; }
      else { if (clock.base >= MV.duration - 0.05) clock.base = 0; clock.start = performance.now(); clock.playing = true; }
    }
    refreshButtons();
  };
  const refreshButtons = () => {
    play.textContent = isPlaying() ? '❚❚' : '▶';
    zh.classList.toggle('on', MV.config.showZh);
    zh.textContent = MV.config.showZh ? '中 ON' : '中 OFF';
    const o = MV.config.offset;
    off.textContent = (o >= 0 ? '+' : '−') + Math.abs(o).toFixed(1) + 's';
  };
  const nudge = (d) => { MV.config.offset = Math.round((MV.config.offset + d) * 10) / 10; refreshButtons(); };
  const fullscreen = () => {
    const el = document.documentElement;
    if (!document.fullscreenElement) (el.requestFullscreen ? el.requestFullscreen() : Promise.resolve()).catch(() => {});
    else document.exitFullscreen();
  };
  MV.player = { toggle, nudge, fullscreen, seek: (t) => setMedia(t - MV.config.offset), media, isPlaying, now: () => media() + MV.config.offset };

  $('file').addEventListener('change', (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const cur = media();
    audio.src = URL.createObjectURL(f);
    hasAudio = true;
    clock.playing = false;
    audio.addEventListener('loadedmetadata', () => { audio.currentTime = Math.min(cur, audio.duration || cur); refreshButtons(); }, { once: true });
    src.textContent = f.name;
    refreshButtons();
  });
  audio.addEventListener('play', refreshButtons);
  audio.addEventListener('pause', refreshButtons);
  play.addEventListener('click', toggle);
  zh.addEventListener('click', () => { MV.config.showZh = !MV.config.showZh; refreshButtons(); });
  $('offm').addEventListener('click', () => nudge(-0.1));
  $('offp').addEventListener('click', () => nudge(0.1));
  $('fs').addEventListener('click', fullscreen);
  seek.addEventListener('input', () => { dragging = true; setMedia(parseFloat(seek.value) - MV.config.offset); });
  seek.addEventListener('change', () => { dragging = false; });
  window.addEventListener('keydown', (e) => {
    if (e.target && e.target.tagName === 'INPUT' && e.target.type !== 'range') return;
    const k = e.key;
    if (k === ' ' || e.code === 'Space') { e.preventDefault(); toggle(); }
    else if (k === 'z' || k === 'Z') { MV.config.showZh = !MV.config.showZh; refreshButtons(); }
    else if (k === 'f' || k === 'F') fullscreen();
    else if (k === '[') nudge(-0.1);
    else if (k === ']') nudge(0.1);
    else if (k === 'ArrowLeft') { e.preventDefault(); setMedia(media() - 5); }
    else if (k === 'ArrowRight') { e.preventDefault(); setMedia(media() + 5); }
    else if (k === 'Home') setMedia(0);
  });
  // auto-hide the bar while playing
  let lastMove = performance.now();
  window.addEventListener('mousemove', () => { lastMove = performance.now(); ui.classList.remove('idle'); });
  refreshButtons();
  let lastT = '';
  const loop = () => {
    let m = media();
    if (!hasAudio && clock.playing && m >= MV.duration) { clock.base = MV.duration; clock.playing = false; refreshButtons(); m = MV.duration; }
    const t = clamp(m + MV.config.offset, 0, MV.duration);
    const sig = t + '|' + MV.config.showZh + '|' + MV.config.grain;
    if (sig !== lastT) { render(t); lastT = sig; }
    tc.textContent = fmtTC(t);
    if (!dragging) seek.value = String(t);
    ui.classList.toggle('idle', isPlaying() && performance.now() - lastMove > 2600);
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}

init();
