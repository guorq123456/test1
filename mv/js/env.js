// env.js — environment / background library for 機械の声 × Claude (STORYBOARD_V2 §2.1).
//
// Every environment is a pure function of t (seconds) + params; randomness is seeded (fx.rng / fx.rnd).
// All drawing is in a 1920×1080 coordinate space (the ctx's current transform is respected, so a scene
// may shake / scale the whole environment).
//
//   drawX(ctx, t, { tint, energy, cam, seed, alpha, bloom, ... })  → returns { cam } (the resolved camera)
//     tint   0..1   0 = cold (cyan/steel/ice), 1 = warm (gold/orange/paper)
//     energy 0..1   driven by lyric onsets: pulses lights, glow, data traffic
//     seed          world seed (number|string); same seed + t → identical frame
//     alpha  0..1   composite opacity (≠1 → drawn into a pooled offscreen layer, then composited)
//     bloom         false | { radius, strength, threshold } — overrides the env's default bloom pass
//     cam           camera override, see resolveCam() below
//
// Camera override (`cam`) — two ways, combinable:
//   • progress / offset API (applied on top of the env's default slow path):
//       { dolly, strafe, rise }  world-unit offsets along the camera's forward / right / world-up
//       { yaw, pitch, roll }     radians added to the default orientation
//       { zoom }                 focal multiplier (2 = twice as close-up; fov is narrowed)
//       { speed, offset }        path clock = t*speed + offset (speed 0 freezes the default path)
//   • absolute: { pos:[x,y,z], target:[x,y,z], roll, fov } — replaces the default path entirely
//       (roll is then absolute; dolly/strafe/yaw/... still apply on top).
//
// Helpers: project(p, cam) → {x, y, scale, depth, visible}; makeCam(); fog(depth, far, near, power);
//          bloom(canvas, radius, strength); bloomLayer(ctx, drawFn, opts); blackout(ctx, alpha);
//          vignette(ctx, a); chromatic(ctx, px); envPalette(tint, alarm); loadEnvAssets(); setEnvAssets().

import {
  W, H, TAU, clamp, lerp, fract, rng, rnd, bucket, P, mix, rgba, ramp,
  makeCanvas, tinted, label, ring,
} from './fx.js';

export const ALARM = '#E8452A';

/* ================================================================ assets */
const A = { silhouette: null, face: null, book: null, bust: null, full: null };
const ASSET_FILES = {
  silhouette: 'char_silhouette.png', face: 'char_face.png', book: 'char_book.png',
  bust: 'char_bust.png', full: 'char_full.png',
};
const ALIASES = { char_silhouette: 'silhouette', char_face: 'face', char_book: 'book', char_bust: 'bust', char_full: 'full' };
/** inject already-loaded images: { silhouette, face, book, bust, full } (engine-style keys char_xxx accepted too) */
export function setEnvAssets(o = {}) {
  for (const [k, v] of Object.entries(o)) { const key = ALIASES[k] || k; if (key in A && v) A[key] = v; }
  spriteCache.clear(); grayCache.clear(); duoCache.clear();
}
/** load the five images this library uses; resolves when decoded */
export async function loadEnvAssets(base = new URL('../assets/', import.meta.url).href) {
  const load = (f) => new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => (im.decode ? im.decode().then(() => res(im), () => res(im)) : res(im));
    im.onerror = () => rej(new Error('env: failed to load ' + f));
    im.src = base + f;
  });
  const out = {};
  await Promise.all(Object.entries(ASSET_FILES).map(async ([k, f]) => { out[k] = await load(f); }));
  setEnvAssets(out);
  return out;
}

/* ================================================================ palette */
/** colours ([r,g,b]) for a tint (0 cold → 1 warm) and optional alarm amount (0..1) */
export function envPalette(tint = 0, alarm = 0) {
  const k = clamp(tint);
  let line = ramp([[0, '#56C6DB'], [0.4, P.steel], [0.7, P.gold], [1, P.orange]], k);
  let hot = ramp([[0, P.ice], [0.55, P.paper], [1, '#FFE2C2']], k);
  let glow = ramp([[0, '#23A6C4'], [0.45, '#7895A3'], [0.7, P.gold], [1, P.orange]], k);
  let bg = ramp([[0, '#020608'], [1, '#0A0604']], k);
  let haze = ramp([[0, '#0B2B36'], [0.5, '#1B1E21'], [1, '#3A1B0B']], k);
  if (alarm > 0) {
    const a = clamp(alarm);
    line = mix(line, ALARM, a); glow = mix(glow, ALARM, a); hot = mix(hot, '#FFE6DE', a);
    bg = mix(bg, '#040101', a); haze = mix(haze, '#2C0705', a);
  }
  return { line, hot, glow, bg, haze, k };
}
const ck = (c) => ((c[0] >> 3) << 10 | (c[1] >> 3) << 5 | (c[2] >> 3)); // 15-bit colour key for caches

/* ================================================================ camera / projection */
/** build a camera from position / target / roll (rad) / vertical fov (deg) */
export function makeCam({ pos, target, roll = 0, fov = 60, near = 0.12, cx = W / 2, cy = H / 2 }) {
  let fx = target[0] - pos[0], fy = target[1] - pos[1], fz = target[2] - pos[2];
  const fl = Math.hypot(fx, fy, fz) || 1; fx /= fl; fy /= fl; fz /= fl;
  let rx = fz, ry = 0, rz = -fx; // right = worldUp × fwd
  const rl = Math.hypot(rx, rz) || 1; rx /= rl; rz /= rl;
  if (rl < 1e-6) { rx = 1; rz = 0; }
  let ux = fy * rz - fz * ry, uy = fz * rx - fx * rz, uz = fx * ry - fy * rx; // up = fwd × right
  if (roll) {
    const c = Math.cos(roll), s = Math.sin(roll);
    const nrx = rx * c + ux * s, nry = ry * c + uy * s, nrz = rz * c + uz * s;
    ux = ux * c - rx * s; uy = uy * c - ry * s; uz = uz * c - rz * s;
    rx = nrx; ry = nry; rz = nrz;
  }
  const f = (H / 2) / Math.tan((fov * Math.PI) / 360);
  return { pos: pos.slice(), target: target.slice(), roll, fov, near, f, cx, cy,
    px: pos[0], py: pos[1], pz: pos[2], fx, fy, fz, rx, ry, rz, ux, uy, uz };
}
/** apply a `cam` override (see header) to a default camera {pos,target,roll,fov} */
export function resolveCam(base, o) {
  o = o || {};
  const abs = !!o.pos;
  const pos = (o.pos || base.pos).slice(), target = (o.target || base.target).slice();
  let roll = abs ? (o.roll || 0) : (base.roll || 0) + (o.roll || 0);
  let fov = o.fov || base.fov || 60;
  let fx = target[0] - pos[0], fy = target[1] - pos[1], fz = target[2] - pos[2];
  const len = Math.hypot(fx, fy, fz) || 1; fx /= len; fy /= len; fz /= len;
  if (o.yaw) { const c = Math.cos(o.yaw), s = Math.sin(o.yaw); const nx = fx * c + fz * s; fz = -fx * s + fz * c; fx = nx; }
  if (o.pitch) {
    const hl = Math.hypot(fx, fz) || 1e-6, el = Math.atan2(fy, hl) + o.pitch;
    const k = Math.cos(el) / hl; fx *= k; fz *= k; fy = Math.sin(el);
  }
  let rx = fz, rz = -fx; const rl = Math.hypot(rx, rz) || 1; rx /= rl; rz /= rl;
  const d = o.dolly || 0, s = o.strafe || 0, r = o.rise || 0;
  pos[0] += fx * d + rx * s; pos[1] += fy * d + r; pos[2] += fz * d + rz * s;
  const tg = [pos[0] + fx * len, pos[1] + fy * len, pos[2] + fz * len];
  if (o.zoom && o.zoom !== 1) fov = (2 * Math.atan(Math.tan((fov * Math.PI) / 360) / o.zoom) * 180) / Math.PI;
  return makeCam({ pos, target: tg, roll, fov });
}
const pathT = (t, o) => t * (o && o.speed != null ? o.speed : 1) + ((o && o.offset) || 0);

/** world point → screen. p = [x,y,z] | {x,y,z}; also project(x, y, z, cam). */
export function project(p, cam, z3, cam4) {
  let x, y, z;
  if (typeof p === 'number') { x = p; y = cam; z = z3; cam = cam4; }
  else if (Array.isArray(p)) { [x, y, z] = p; } else { ({ x, y, z } = p); }
  const o = [0, 0, 0, 0];
  const vis = pc(cam, x, y, z, o);
  return { x: o[0], y: o[1], scale: o[3], depth: o[2], visible: vis };
}
/** fast projection into o = [sx, sy, depth, scale]; returns visible (depth > near) */
function pc(c, x, y, z, o) {
  const dx = x - c.px, dy = y - c.py, dz = z - c.pz;
  const X = dx * c.rx + dy * c.ry + dz * c.rz, Y = dx * c.ux + dy * c.uy + dz * c.uz, Z = dx * c.fx + dy * c.fy + dz * c.fz;
  const zz = Z < c.near ? c.near : Z, s = c.f / zz;
  o[0] = c.cx + X * s; o[1] = c.cy - Y * s; o[2] = Z; o[3] = s;
  return Z > c.near;
}
function cs(c, x, y, z, o) { // camera space
  const dx = x - c.px, dy = y - c.py, dz = z - c.pz;
  o[0] = dx * c.rx + dy * c.ry + dz * c.rz; o[1] = dx * c.ux + dy * c.uy + dz * c.uz; o[2] = dx * c.fx + dy * c.fy + dz * c.fz;
}
const _a = [0, 0, 0], _b = [0, 0, 0];
/** append a near-clipped 3D segment to the current path; returns false if fully behind */
function seg3(g, c, ax, ay, az, bx, by, bz) {
  cs(c, ax, ay, az, _a); cs(c, bx, by, bz, _b);
  const n = c.near;
  if (_a[2] < n && _b[2] < n) return false;
  if (_a[2] < n) { const k = (n - _a[2]) / (_b[2] - _a[2]); _a[0] += (_b[0] - _a[0]) * k; _a[1] += (_b[1] - _a[1]) * k; _a[2] = n; }
  else if (_b[2] < n) { const k = (n - _b[2]) / (_a[2] - _b[2]); _b[0] += (_a[0] - _b[0]) * k; _b[1] += (_a[1] - _b[1]) * k; _b[2] = n; }
  g.moveTo(c.cx + (c.f * _a[0]) / _a[2], c.cy - (c.f * _a[1]) / _a[2]);
  g.lineTo(c.cx + (c.f * _b[0]) / _b[2], c.cy - (c.f * _b[1]) / _b[2]);
  return true;
}
/** visibility factor 1 (clear) → 0 (fully fogged into the background colour) */
export function fog(depth, far = 60, near = 0, power = 1.4) {
  return Math.pow(1 - clamp((depth - near) / (far - near)), power);
}
function hull(pts) { // Andrew monotone chain on [[x,y],...]
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const p of pts) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (let i = pts.length - 1; i >= 0; i--) { const p = pts[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  up.pop(); lo.pop();
  return lo.concat(up);
}

/* ================================================================ scratch canvases, bloom, layers */
const scratchMap = new Map();
function scratch(key, w, h) {
  let c = scratchMap.get(key);
  if (!c || c.width !== w || c.height !== h) { c = makeCanvas(w, h); scratchMap.set(key, c); }
  return c;
}
function prep(x) { x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.filter = 'none'; x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'low'; }

/**
 * Additive bloom, in place on `src` (a canvas): ½ → ¼ box-downscale, blur at ¼ (radius/4 px) plus a wider
 * ⅛-res pass, upscale with 'lighter'. Cost ≈ 3–6 ms at 1920×1080 in software canvas.
 * o: { threshold 0..0.45 (soft knee via contrast), wide 0..1 (wide-halo weight, default 0.7) }
 */
export function bloom(src, radius = 24, strength = 0.8, o = {}) {
  if (!src || strength <= 0) return src;
  addGlow(src.getContext('2d'), bloomGlow(src, radius, o), src.width, src.height, strength);
  return src;
}
/** build the blurred ¼-res glow canvas of src (scratch — valid until the next bloom call) */
function bloomGlow(src, radius, o = {}) {
  const w = src.width, h = src.height;
  const w2 = Math.ceil(w / 2), h2 = Math.ceil(h / 2), w4 = Math.ceil(w / 4), h4 = Math.ceil(h / 4), w8 = Math.ceil(w / 8), h8 = Math.ceil(h / 8);
  const c2 = scratch('bl2', w2, h2), c4 = scratch('bl4', w4, h4), c4b = scratch('bl4b', w4, h4), c8 = scratch('bl8', w8, h8), c8b = scratch('bl8b', w8, h8);
  let x = c2.getContext('2d'); prep(x); x.globalCompositeOperation = 'copy'; x.drawImage(src, 0, 0, w2, h2);
  x = c4.getContext('2d'); prep(x); x.globalCompositeOperation = 'copy';
  if (o.threshold > 0) x.filter = `contrast(${(0.5 / (0.5 - Math.min(0.45, o.threshold))).toFixed(3)})`;
  x.drawImage(c2, 0, 0, w4, h4); x.filter = 'none';
  const r4 = Math.max(0.5, radius / 4);
  x = c4b.getContext('2d'); prep(x); x.globalCompositeOperation = 'copy'; x.filter = `blur(${r4.toFixed(2)}px)`; x.drawImage(c4, 0, 0); x.filter = 'none';
  const wide = o.wide == null ? 0.7 : o.wide;
  if (wide > 0) {
    let y = c8.getContext('2d'); prep(y); y.globalCompositeOperation = 'copy'; y.drawImage(c4, 0, 0, w8, h8);
    y = c8b.getContext('2d'); prep(y); y.globalCompositeOperation = 'copy'; y.filter = `blur(${r4.toFixed(2)}px)`; y.drawImage(c8, 0, 0); y.filter = 'none';
    x.globalCompositeOperation = 'lighter'; x.globalAlpha = wide; x.drawImage(c8b, 0, 0, w4, h4); x.globalAlpha = 1;
  }
  return c4b;
}
function addGlow(s, glowC, w, h, strength, alpha = 1) {
  // ¼ → ½ bilinear (cheap), ½ → full nearest: the glow is smooth, 2×2 blocks are invisible, and this halves
  // the cost of the only full-resolution pass (bilinear full-res upscale ≈ 10 ms in software canvas).
  const up = scratch('blUp', Math.ceil(w / 2), Math.ceil(h / 2)), ux = up.getContext('2d');
  prep(ux); ux.globalCompositeOperation = 'copy'; ux.drawImage(glowC, 0, 0, up.width, up.height);
  s.save(); s.setTransform(1, 0, 0, 1, 0, 0); s.filter = 'none';
  s.globalCompositeOperation = 'lighter'; s.imageSmoothingEnabled = false;
  let left = clamp(strength, 0, 4) * alpha;
  while (left > 0.002) { s.globalAlpha = Math.min(1, left); s.drawImage(up, 0, 0, w, h); left -= 1; }
  s.restore();
}

const layerPool = []; let layerDepth = 0;
function acquireLayer(w, h) {
  let c = layerPool[layerDepth];
  if (!c || c.width !== w || c.height !== h) { c = makeCanvas(w, h); layerPool[layerDepth] = c; }
  layerDepth++;
  return c;
}
function releaseLayer() { layerDepth = Math.max(0, layerDepth - 1); }

/**
 * Draw `drawFn(layerCtx)` into a pooled transparent full-size layer, bloom it, composite onto ctx.
 * o: { radius=24, strength=0.8, threshold, wide, alpha=1, op='source-over', bloomOnly=false }
 * (bloomOnly: composite only the glow, not the sharp layer — e.g. to add glow to text already drawn.)
 */
export function bloomLayer(ctx, drawFn, o = {}) {
  const cw = ctx.canvas.width, chh = ctx.canvas.height;
  const L = acquireLayer(cw, chh), g = L.getContext('2d');
  try {
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
    g.clearRect(0, 0, cw, chh);
    g.setTransform(ctx.getTransform());
    g.save(); drawFn(g); g.restore();
    const alpha = o.alpha == null ? 1 : o.alpha, strength = o.strength == null ? 0.8 : o.strength;
    const glowC = bloomGlow(L, o.radius == null ? 24 : o.radius, o);
    if (!o.bloomOnly) {
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = alpha; ctx.globalCompositeOperation = o.op || 'source-over';
      ctx.drawImage(L, 0, 0); ctx.restore();
    }
    addGlow(ctx, glowC, cw, chh, strength, alpha);
  } finally { releaseLayer(); }
}

/**
 * common env wrapper: direct draw (alpha 1) or pooled layer; body(g, q) draws sharp content on g and soft light
 * (haze, cones, halos, reflections) on q — a ¼-resolution additive buffer in the same 1920×1080 coordinates.
 * q is merged into the bloom glow so the frame pays for exactly one full-resolution upscale.
 */
function envRun(ctx, p, defBloom, body) {
  const alpha = p.alpha == null ? 1 : p.alpha;
  if (alpha <= 0.001) return null;
  const useLayer = alpha < 0.999 || p.layer === true || (p.op && p.op !== 'source-over');
  const cw = ctx.canvas.width, chh = ctx.canvas.height;
  let g = ctx, L = null;
  if (useLayer) {
    L = acquireLayer(cw, chh); g = L.getContext('2d');
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cw, chh);
    g.setTransform(ctx.getTransform());
  }
  const w4 = Math.ceil(cw / 4), h4 = Math.ceil(chh / 4);
  const Q = scratch('envQ' + layerDepth, w4, h4), q = Q.getContext('2d');
  prep(q); q.globalCompositeOperation = 'copy'; q.fillStyle = 'rgba(0,0,0,0)'; q.fillRect(0, 0, w4, h4);
  q.globalCompositeOperation = 'lighter';
  const T = ctx.getTransform(); q.setTransform(0.25, 0, 0, 0.25, 0, 0); q.transform(T.a, T.b, T.c, T.d, T.e, T.f);
  g.save();
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none'; g.setLineDash([]);
  g.lineCap = 'butt'; g.lineJoin = 'miter'; g.shadowBlur = 0;
  let out;
  try {
    out = body(g, q) || {};
  } finally { g.restore(); }
  const bl = p.bloom === false ? null : Object.assign({}, defBloom, p.bloom || {});
  let glowC = Q;
  if (bl && bl.strength > 0) {
    const c4b = bloomGlow(g.canvas, bl.radius, bl);
    const comb = scratch('envComb', w4, h4), cx = comb.getContext('2d');
    prep(cx);
    let st = bl.strength * (1 + 0.35 * clamp(p.energy || 0));
    cx.globalCompositeOperation = 'copy'; cx.globalAlpha = Math.min(1, st); cx.drawImage(c4b, 0, 0); st -= 1;
    cx.globalCompositeOperation = 'lighter';
    while (st > 0.002) { cx.globalAlpha = Math.min(1, st); cx.drawImage(c4b, 0, 0); st -= 1; }
    cx.globalAlpha = 1; cx.drawImage(Q, 0, 0);
    if (out.fringe) out.fringe(cx, c4b, w4, h4);
    glowC = comb;
  }
  addGlow(g, glowC, cw, chh, 1);
  if (out.post) out.post(g);
  if (useLayer) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = alpha; ctx.globalCompositeOperation = p.op || 'source-over';
    ctx.drawImage(L, 0, 0); ctx.restore();
    releaseLayer();
  }
  return out;
}

/* ================================================================ small drawing helpers */
const glowCache = new Map();
/** soft radial glow sprite (128²) in colour c (quantised cache) */
function glowSprite(c) {
  const key = ck(c);
  let s = glowCache.get(key);
  if (!s) {
    if (glowCache.size > 256) glowCache.clear();
    s = makeCanvas(128, 128); const x = s.getContext('2d');
    const g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, rgba(c, 1)); g.addColorStop(0.12, rgba(c, 0.75)); g.addColorStop(0.35, rgba(c, 0.25));
    g.addColorStop(0.7, rgba(c, 0.06)); g.addColorStop(1, rgba(c, 0));
    x.fillStyle = g; x.fillRect(0, 0, 128, 128);
    glowCache.set(key, s);
  }
  return s;
}
function blob(g, spr, x, y, rx, ry, a) {
  if (a <= 0.003 || rx < 0.3) return;
  g.globalAlpha = a; g.drawImage(spr, x - rx, y - ry, rx * 2, ry * 2);
}
function bgFill(g, col) { g.fillStyle = rgba(col, 1); g.fillRect(-80, -80, W + 160, H + 160); }
/** full-frame fill (section cuts through black) */
export function blackout(ctx, alpha = 1, colour = '#000') {
  if (alpha <= 0.001) return;
  ctx.save(); ctx.globalAlpha = clamp(alpha); ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = colour; ctx.fillRect(-80, -80, W + 160, H + 160); ctx.restore();
}
let vigC = null;
/** cached radial vignette (black) */
export function vignette(ctx, a = 0.8) {
  if (a <= 0) return;
  if (!vigC) {
    vigC = makeCanvas(W, H); const x = vigC.getContext('2d');
    const g = x.createRadialGradient(W / 2, H / 2, H * 0.28, W / 2, H / 2, H * 1.05);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.6, 'rgba(0,0,0,0.35)'); g.addColorStop(1, 'rgba(0,0,0,0.92)');
    x.fillStyle = g; x.fillRect(0, 0, W, H);
  }
  ctx.save(); ctx.globalAlpha = clamp(a); ctx.drawImage(vigC, 0, 0); ctx.restore();
}
/**
 * chromatic aberration: the red channel is shifted by `px` (GB stay) — 4 full-frame ops (≈ 8–10 ms) instead of
 * fx.rgbSplit's 6 (≈ 20 ms). Works on any canvas size; ctx transform is ignored (device pixels).
 */
export function chromatic(ctx, px = 3) {
  if (Math.abs(px) < 0.5) return;
  const cw = ctx.canvas.width, chh = ctx.canvas.height;
  const A = scratch('chromR', cw, chh), ax = A.getContext('2d');
  prep(ax); ax.globalCompositeOperation = 'copy'; ax.drawImage(ctx.canvas, 0, 0);
  ax.globalCompositeOperation = 'multiply'; ax.fillStyle = '#ff0000'; ax.fillRect(0, 0, cw, chh);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.filter = 'none';
  ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#00ffff'; ctx.fillRect(0, 0, cw, chh);
  ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(A, Math.round(px), 0);
  ctx.restore();
}

/* ---------- grayscale / duotone image caches (monitors, fragments) */
const grayCache = new Map(), duoCache = new Map();
function grayOf(name) {
  let c = grayCache.get(name);
  if (!c) {
    const im = A[name]; if (!im) return null;
    const sc = Math.min(1, 900 / Math.max(im.width, im.height));
    c = makeCanvas(im.width * sc, im.height * sc); const x = c.getContext('2d');
    x.fillStyle = '#000'; x.fillRect(0, 0, c.width, c.height);
    x.filter = 'grayscale(1) contrast(1.25) brightness(1.08)'; x.drawImage(im, 0, 0, c.width, c.height); x.filter = 'none';
    grayCache.set(name, c);
  }
  return c;
}
/** cover-crop rect of an image for a dest aspect: focus (fx,fy) in 0..1, zoom ≥ 1 */
function coverRect(iw, ih, dw, dh, fx, fy, zoom) {
  const s = Math.max(dw / iw, dh / ih) * zoom, sw = dw / s, sh = dh / s;
  return [clamp(fx * iw - sw / 2, 0, Math.max(0, iw - sw)), clamp(fy * ih - sh / 2, 0, Math.max(0, ih - sh)), Math.min(sw, iw), Math.min(sh, ih)];
}
/** duotone crop (dark → bg, light → colour) at w×h, cached */
function duotone(name, col, w, h, fx, fy, zoom) {
  const key = `${name}|${ck(col)}|${w}|${h}|${fx}|${fy}|${zoom}`;
  let c = duoCache.get(key);
  if (!c) {
    if (duoCache.size > 160) duoCache.clear();
    const gimg = grayOf(name); if (!gimg) return null;
    c = makeCanvas(w, h); const x = c.getContext('2d');
    const [sx, sy, sw, sh] = coverRect(gimg.width, gimg.height, w, h, fx, fy, zoom);
    x.drawImage(gimg, sx, sy, sw, sh, 0, 0, w, h);
    x.globalCompositeOperation = 'multiply'; x.fillStyle = rgba(col, 1); x.fillRect(0, 0, w, h);
    x.globalCompositeOperation = 'source-over';
    duoCache.set(key, c);
  }
  return c;
}

/* ---------- voice (capsule crowd) sprites, per palette level.
   core  = the character's silhouette, lightly blurred (drawn sharp, full resolution)
   soft  = capsule glass + wide silhouette glow (½-res; drawn into the ¼-res light buffer)
   refl  = blurred flipped copy, fading (light buffer) */
const spriteCache = new Map();
function capsulePath(x, l, t, w, h) {
  const r = w / 2, rb = w * 0.16;
  x.beginPath();
  x.moveTo(l, t + r); x.arc(l + r, t + r, r, Math.PI, 0);
  x.lineTo(l + w, t + h - rb); x.quadraticCurveTo(l + w, t + h, l + w - rb, t + h);
  x.lineTo(l + rb, t + h); x.quadraticCurveTo(l, t + h, l, t + h - rb); x.closePath();
}
function voiceSprite(core, glowC) {
  const key = ck(core) + ':' + ck(glowC);
  let s = spriteCache.get(key);
  if (s) return s;
  if (spriteCache.size > 48) spriteCache.clear();
  const FH = 560, sil = A.silhouette;
  const fw = sil ? Math.round((FH * sil.width) / sil.height) : 280;
  // core
  const cp = 6, cc = makeCanvas(fw + cp * 2, FH + cp * 2), cx = cc.getContext('2d');
  if (sil) {
    const tc = tinted(sil, rgba(core, 1), fw, FH);
    cx.filter = 'blur(1.4px)'; cx.drawImage(tc, cp, cp); cx.filter = 'none';
    // faint inner shading so the figure is not a flat cut-out: brighter top, slightly dimmer skirt
    cx.globalCompositeOperation = 'source-atop';
    const sg = cx.createLinearGradient(0, 0, 0, FH);
    sg.addColorStop(0, 'rgba(255,255,255,0.25)'); sg.addColorStop(0.5, 'rgba(0,0,0,0)'); sg.addColorStop(1, rgba(glowC, 0.35));
    cx.fillStyle = sg; cx.fillRect(0, 0, cc.width, cc.height);
  } else {
    cx.fillStyle = rgba(core, 1); capsulePath(cx, cp + fw * 0.15, cp, fw * 0.7, FH); cx.fill();
  }
  // soft (½ res)
  const k = 0.5, capW = fw * 1.24, capH = FH * 1.12, pad = 70;
  const sw = Math.ceil((capW + pad * 2) * k), sh = Math.ceil((capH + pad * 2) * k);
  const sc = makeCanvas(sw, sh), sx = sc.getContext('2d');
  const footS = (pad + capH - 10) * k; // foot line in soft-canvas px
  sx.scale(k, k);
  const gr = sx.createLinearGradient(0, pad, 0, pad + capH);
  gr.addColorStop(0, rgba(glowC, 0.30)); gr.addColorStop(0.6, rgba(glowC, 0.12)); gr.addColorStop(1, rgba(glowC, 0.22));
  sx.filter = 'blur(8px)'; capsulePath(sx, pad, pad, capW, capH); sx.fillStyle = gr; sx.fill();
  sx.filter = 'blur(2px)'; sx.lineWidth = 6; sx.strokeStyle = rgba(mix(glowC, core, 0.4), 0.45); capsulePath(sx, pad, pad, capW, capH); sx.stroke();
  if (sil) {
    const tg = tinted(sil, rgba(glowC, 1), fw, FH), fx0 = pad + (capW - fw) / 2, fy0 = pad + capH - 10 - FH;
    sx.filter = 'blur(26px)'; sx.globalAlpha = 0.75; sx.drawImage(tg, fx0, fy0);
    sx.filter = 'blur(8px)'; sx.globalAlpha = 0.4; sx.drawImage(tg, fx0, fy0);
  }
  sx.setTransform(1, 0, 0, 1, 0, 0); sx.filter = 'none'; sx.globalAlpha = 1;
  // reflection (from soft + core), fading
  const rh = Math.ceil(sh * 0.6), rc = makeCanvas(sw, rh), rx = rc.getContext('2d');
  rx.filter = 'blur(3px)'; rx.translate(0, footS); rx.scale(1, -1);
  rx.drawImage(sc, 0, 0);
  rx.globalAlpha = 0.6; rx.drawImage(cc, (sw - cc.width * k) / 2, footS - (FH + cp) * k, cc.width * k, cc.height * k);
  rx.setTransform(1, 0, 0, 1, 0, 0); rx.filter = 'none'; rx.globalAlpha = 1;
  rx.globalCompositeOperation = 'destination-in';
  const fg = rx.createLinearGradient(0, 0, 0, rh); fg.addColorStop(0, 'rgba(0,0,0,0.6)'); fg.addColorStop(1, 'rgba(0,0,0,0)');
  rx.fillStyle = fg; rx.fillRect(0, 0, sw, rh);
  s = {
    core: cc, cax: cc.width / 2, cfoot: FH + cp, figH: FH,
    soft: sc, sax: sw / 2, sfoot: footS, sk: k, refl: rc,
  };
  spriteCache.set(key, s);
  return s;
}
/** sprites for a palette (quantised: 12 levels); soft part crossfades between levels (cheap, ¼-res) */
function voiceSet(tint, alarm) {
  const L = 12, qv = clamp(tint) * L, i0 = Math.floor(qv), f = qv - i0;
  const mk = (kk) => { const pp = envPalette(kk / L, alarm); return voiceSprite(mix(mix(pp.hot, pp.glow, 0.22 + 0.1 * alarm), pp.bg, 0.12), pp.glow); };
  const a = mk(i0), b = f > 0.02 ? mk(Math.min(L, i0 + 1)) : null;
  return { a, b, f, core: f < 0.5 ? a : b };
}
/** one voice figure standing at world (x, 0, z), height h (world units) */
function drawVoice(g, q, cam, set, x, z, h, alpha, flip, refl = true, softK = 0.55) {
  if (alpha <= 0.004) return;
  const b = [0, 0, 0, 0], tp = [0, 0, 0, 0];
  if (!pc(cam, x, 0, z, b)) return;
  pc(cam, x, h, z, tp);
  const dx = tp[0] - b[0], dy = tp[1] - b[1], hs = Math.hypot(dx, dy);
  if (hs < 2) return;
  const sp = set.a, sc = hs / sp.figH;
  const halfW = (sp.soft.width / sp.sk) * sc * 0.5;
  if (b[0] + halfW < -60 || b[0] - halfW > W + 60) return;
  const ang = Math.atan2(dx, -dy);
  const soft = (S, a) => {
    if (a <= 0.003) return;
    const ss = sc / S.sk;
    q.globalAlpha = a; q.drawImage(S.soft, -S.sax * ss, -S.sfoot * ss, S.soft.width * ss, S.soft.height * ss);
    if (refl) { q.globalAlpha = a * 0.8; q.drawImage(S.refl, -S.sax * ss, 0, S.refl.width * ss, S.refl.height * ss); }
  };
  q.save(); q.translate(b[0], b[1]); q.rotate(ang); if (flip) q.scale(-1, 1);
  soft(set.a, softK * alpha * (set.b ? 1 - set.f : 1)); if (set.b) soft(set.b, softK * alpha * set.f);
  q.restore();
  const base = g.getTransform();
  g.translate(b[0], b[1]); g.rotate(ang); if (flip) g.scale(-1, 1);
  const C = set.core;
  g.globalAlpha = clamp(alpha); g.drawImage(C.core, -C.cax * sc, -C.cfoot * sc, C.core.width * sc, C.core.height * sc);
  g.setTransform(base);
}

/* ---------- hanging lamp: cable + glowing disc (sharp) + light cone, floor pool, halo (light buffer) */
function drawLamp(g, q, cam, L, pal, inten, floorY = 0) {
  const c = [0, 0, 0, 0], qq = [0, 0, 0, 0], u = [0, 0, 0, 0];
  if (!pc(cam, L.x, L.y, L.z, c)) return;
  const vis = fog(c[2], L.far || 70, 0, 1.2);
  if (vis <= 0.01 || inten <= 0.01) return;
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 0.55 * vis; g.strokeStyle = rgba(pal.line, 1); g.lineWidth = Math.min(2.2, 0.6 + c[3] * 0.012);
  g.beginPath(); seg3(g, cam, L.x, L.ceil, L.z, L.x, L.y, L.z); g.stroke();
  pc(cam, L.x + L.r, L.y, L.z, qq); const ax = Math.hypot(qq[0] - c[0], qq[1] - c[1]);
  pc(cam, L.x, L.y, L.z + L.r, qq); pc(cam, L.x, L.y, L.z - L.r, u);
  const ay = Math.max(1, Math.abs(qq[1] - u[1]) / 2);
  const pl = [0, 0, 0, 0], pr = [0, 0, 0, 0], fl = [0, 0, 0, 0], fr = [0, 0, 0, 0], fc = [0, 0, 0, 0];
  pc(cam, L.x - L.r, L.y, L.z, pl); pc(cam, L.x + L.r, L.y, L.z, pr);
  if (pc(cam, L.x, floorY, L.z, fc)) {
    pc(cam, L.x - L.R, floorY, L.z, fl); pc(cam, L.x + L.R, floorY, L.z, fr);
    const gr = q.createLinearGradient(c[0], c[1], fc[0], fc[1]);
    const ca = inten * vis;
    gr.addColorStop(0, rgba(pal.glow, 0.34 * ca)); gr.addColorStop(0.45, rgba(pal.glow, 0.12 * ca)); gr.addColorStop(1, rgba(pal.glow, 0.03 * ca));
    q.globalAlpha = 1; q.fillStyle = gr;
    q.beginPath(); q.moveTo(pl[0], pl[1]); q.lineTo(pr[0], pr[1]); q.lineTo(fr[0], fr[1]); q.lineTo(fl[0], fl[1]); q.closePath(); q.fill();
    const prx = Math.hypot(fr[0] - fl[0], fr[1] - fl[1]) / 2;
    pc(cam, L.x, floorY, L.z + L.R, qq); pc(cam, L.x, floorY, L.z - L.R, u);
    const pry = Math.max(2, Math.abs(qq[1] - u[1]) / 2);
    blob(q, glowSprite(pal.glow), fc[0], fc[1], prx * 1.5, pry * 1.5, 0.6 * ca);
  }
  blob(q, glowSprite(pal.glow), c[0], c[1], ax * 5, ax * 5, 0.6 * inten * vis);
  g.globalAlpha = Math.min(1, 0.95 * inten) * vis; g.fillStyle = rgba(pal.hot, 1);
  g.beginPath(); g.ellipse(c[0], c[1], Math.max(1, ax), ay, cam.roll ? -cam.roll : 0, 0, TAU); g.fill();
  g.globalAlpha = 0.8 * vis; g.strokeStyle = rgba(pal.line, 1); g.lineWidth = 1.2;
  g.beginPath(); g.ellipse(c[0], c[1] - ay * 0.6, Math.max(1, ax * 1.08), ay * 1.1, cam.roll ? -cam.roll : 0, Math.PI, TAU); g.stroke();
}
/** emissive horizontal bar (quad on a horizontal plane): sharp quad on g, halo on q */
function drawBar(g, q, cam, x, y, z, hw, hd, col, glowC, a, glowA = 0.5, far = 80) {
  const o = [0, 0, 0, 0], s = [];
  let cx = 0, cy = 0, sc = 0;
  for (const [px, pz] of [[x - hw, z - hd], [x + hw, z - hd], [x + hw, z + hd], [x - hw, z + hd]]) {
    if (!pc(cam, px, y, pz, o)) return;
    s.push([o[0], o[1]]); cx += o[0] / 4; cy += o[1] / 4; sc += o[3] / 4;
  }
  const vis = fog(o[2], far, 0, 1.1);
  if (vis < 0.01) return;
  blob(q, glowSprite(glowC), cx, cy, hw * sc * 2.4, Math.max(hw * sc * 0.9, hd * sc * 3), glowA * a * vis);
  g.globalAlpha = clamp(a * vis); g.fillStyle = rgba(col, 1);
  g.beginPath(); g.moveTo(s[0][0], s[0][1]); for (let i = 1; i < 4; i++) g.lineTo(s[i][0], s[i][1]); g.closePath(); g.fill();
  g.lineWidth = 1.5; g.strokeStyle = rgba(col, 1); g.stroke();
}

/* ================================================================ circuitCity */
const LZ = 6, C_FLOOR = -3.2, C_CEIL = 4.6, C_WALL = 9.5;
const cityCells = new Map();
function cityCell(seed, iz) {
  const key = seed + '|' + iz;
  let cell = cityCells.get(key);
  if (cell) return cell;
  if (cityCells.size > 800) cityCells.clear();
  const r = rng('city', seed, iz), z0 = iz * LZ;
  const boxes = [], traces = [], orbs = [];
  const box = (x0, x1, y0, y1, za, zb) => boxes.push({
    x0: Math.min(x0, x1), x1: Math.max(x0, x1), y0: Math.min(y0, y1), y1: Math.max(y0, y1), z0: za, z1: zb,
    lit: r() < 0.12, node: r() < 0.1 ? Math.floor(r() * 8) : -1, sub: r() < 0.5 ? 1 + Math.floor(r() * 3) : 0, ph: r() * TAU,
  });
  for (const side of [-1, 1]) {
    const n = 6 + Math.floor(r() * 4);
    for (let k = 0; k < n; k++) {
      const inner = 2.4 + r() * r() * 5, y0 = C_FLOOR + r() * (C_CEIL - C_FLOOR - 0.4), hh = 0.25 + r() * r() * 3.2;
      const zs = z0 + r() * LZ, zl = 0.35 + r() * r() * 4;
      box(side * inner, side * (inner + 0.4 + r() * (C_WALL - inner)), y0, Math.min(C_CEIL, y0 + hh), zs, zs + zl);
    }
    if (r() < 0.4) { const x = side * (2.5 + r() * 2.5), wd = 0.25 + r() * 0.6, zs = z0 + r() * LZ; box(x, x + side * wd, C_FLOOR, C_CEIL, zs, zs + 0.25 + r() * 0.7); }
  }
  for (let k = 0; k < 4; k++) { // floor blocks
    const x = (r() - 0.5) * 16, wd = 0.5 + r() * 2.5, zs = z0 + r() * LZ;
    box(x, x + wd, C_FLOOR, C_FLOOR + 0.2 + r() * 1.2, zs, zs + 0.4 + r() * 2.5);
  }
  for (let k = 0; k < 4; k++) { // ceiling blocks
    const x = (r() - 0.5) * 16, wd = 0.5 + r() * 2.5, zs = z0 + r() * LZ;
    box(x, x + wd, C_CEIL - (0.25 + r() * 2.2), C_CEIL, zs, zs + 0.4 + r() * 2.5);
  }
  if (r() < 0.45) { // bridge across the corridor
    const y0 = 1.5 + r() * 2.2, zs = z0 + r() * LZ;
    box(-C_WALL, C_WALL, y0, y0 + 0.15 + r() * 0.4, zs, zs + 0.25 + r() * 1.0);
  }
  for (const y of [C_FLOOR, C_CEIL]) {
    for (let k = 0; k < 5; k++) {
      let x = (r() - 0.5) * 17, z = z0 + r() * LZ;
      const pts = [[x, z]], n = 3 + Math.floor(r() * 3);
      for (let st = 0; st < n; st++) {
        if (st % 2 === 0) z += (r() < 0.8 ? 1 : -1) * (0.6 + r() * 2.8); else x += (r() < 0.5 ? -1 : 1) * (0.4 + r() * 2.4);
        pts.push([x, z]);
      }
      traces.push({ y, pts, pulse: r(), sp: 0.6 + r() * 0.9 });
    }
  }
  if (r() < 0.55) orbs.push({ x: (r() - 0.5) * 13, y: C_FLOOR + 0.6 + r() * (C_CEIL - C_FLOOR - 1.2), z: z0 + r() * LZ, s: 0.2 + r() * 0.4, ph: r() * TAU });
  cell = { boxes, traces, orbs };
  cityCells.set(key, cell);
  return cell;
}
const BOX_E = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];

/**
 * circuitCity(ctx, t, {tint, energy, cam, seed, alpha, bloom}) — wireframe canyon of boxes / circuit traces,
 * camera flies forward (default 2.4 units/s, lateral + vertical sway, slight roll). Corridor is ±2.3 wide,
 * floor y=−3.2, ceiling y=4.6. Glowing nodes, lit panels, data pulses running along floor/ceiling traces (energy).
 */
export function circuitCity(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 7 : p.seed;
  const tc = pathT(t, p.cam);
  const px = Math.sin(tc * 0.19) * 0.9 + Math.sin(tc * 0.071) * 0.5, py = 0.1 + Math.sin(tc * 0.15) * 0.45, pz = tc * 2.4;
  const cam = resolveCam({
    pos: [px, py, pz],
    target: [px + Math.sin(tc * 0.11 + 1) * 2.2, py - 0.15 + Math.sin(tc * 0.13) * 0.6, pz + 10],
    roll: Math.sin(tc * 0.083) * 0.07, fov: 64,
  }, p.cam);
  const pal = envPalette(p.tint || 0);
  return envRun(ctx, p, { radius: 20, strength: 0.8, wide: 0.5 }, (g, q) => {
    bgFill(g, pal.bg);
    const o = [0, 0, 0, 0];
    pc(cam, cam.px + cam.fx * 300, cam.py + cam.fy * 300, cam.pz + cam.fz * 300, o);
    blob(q, glowSprite(pal.haze), o[0], o[1], 1000, 700, 0.75);
    const FAR = 74;
    const iz0 = Math.floor((cam.pz - 8) / LZ), iz1 = Math.floor((cam.pz + FAR) / LZ);
    const items = [];
    const lineC = pal.line, hotC = pal.hot;
    const gs = glowSprite(pal.glow), gh = glowSprite(hotC);
    // --- traces on floor / ceiling planes (behind everything standing on them)
    g.lineWidth = 1; g.strokeStyle = rgba(lineC, 1);
    const pulses = [];
    for (let iz = iz0; iz <= iz1; iz++) {
      const cell = cityCell(seed, iz);
      for (const tr of cell.traces) {
        const m = tr.pts[(tr.pts.length / 2) | 0];
        cs(cam, m[0], tr.y, m[1], _a);
        const d = _a[2]; if (d < -6) continue;
        const vis = fog(Math.max(0, d), FAR, 0, 1.3); if (vis < 0.02) continue;
        g.globalAlpha = 0.45 * vis; g.beginPath();
        for (let i = 1; i < tr.pts.length; i++) seg3(g, cam, tr.pts[i - 1][0], tr.y, tr.pts[i - 1][1], tr.pts[i][0], tr.y, tr.pts[i][1]);
        g.stroke();
        g.fillStyle = rgba(hotC, 1);
        for (const e of [tr.pts[0], tr.pts[tr.pts.length - 1]]) {
          if (pc(cam, e[0], tr.y, e[1], o)) { const sz = Math.max(1.2, 0.06 * o[3]); g.globalAlpha = 0.75 * vis; g.fillRect(o[0] - sz, o[1] - sz, sz * 2, sz * 2); }
        }
        if (tr.pulse < 0.3 + 0.55 * en) pulses.push({ tr, vis });
      }
      for (const b of cell.boxes) {
        cs(cam, (b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2, (b.z0 + b.z1) / 2, _a);
        const ext = Math.max(b.x1 - b.x0, b.y1 - b.y0, b.z1 - b.z0);
        if (_a[2] + ext < cam.near || _a[2] - ext > FAR) continue;
        items.push({ d: _a[2], b });
      }
      for (const ob of cell.orbs) { cs(cam, ob.x, ob.y, ob.z, _a); if (_a[2] > 0.5 && _a[2] < FAR) items.push({ d: _a[2], ob }); }
    }
    // data pulses running along traces
    for (const { tr, vis } of pulses) {
      let total = 0; const Ls = [];
      for (let i = 1; i < tr.pts.length; i++) { const l = Math.hypot(tr.pts[i][0] - tr.pts[i - 1][0], tr.pts[i][1] - tr.pts[i - 1][1]); Ls.push(l); total += l; }
      let u = fract(tc * 0.45 * tr.sp + tr.pulse * 7) * total, i = 0;
      while (i < Ls.length - 1 && u > Ls[i]) { u -= Ls[i]; i++; }
      const k = Ls[i] ? u / Ls[i] : 0, a0 = tr.pts[i], a1 = tr.pts[i + 1];
      if (pc(cam, lerp(a0[0], a1[0], k), tr.y, lerp(a0[1], a1[1], k), o)) {
        const sz = Math.max(2.5, 0.3 * o[3]);
        blob(q, gs, o[0], o[1], sz * 3, sz * 3, 0.9 * vis);
        g.globalAlpha = vis; g.fillStyle = rgba(hotC, 1); g.fillRect(o[0] - sz * 0.3, o[1] - sz * 0.3, sz * 0.6, sz * 0.6);
      }
    }
    // --- boxes, painter-sorted far → near; hull fill occludes what is behind
    items.sort((a, b) => b.d - a.d);
    const P8 = Array.from({ length: 8 }, () => [0, 0, 0, 0]);
    const bgS = rgba(pal.bg, 1);
    for (const it of items) {
      const d = it.d, vis = fog(Math.max(0, d), FAR, 0, 1.25);
      if (vis < 0.01) continue;
      if (it.ob) {
        const ob = it.ob; if (!pc(cam, ob.x, ob.y, ob.z, o)) continue;
        const sz = ob.s * o[3] * (1 + 0.5 * en * (0.5 + 0.5 * Math.sin(tc * 5 + ob.ph)));
        blob(q, gs, o[0], o[1], sz * 5, sz * 5, 0.9 * vis);
        blob(g, gh, o[0], o[1], sz * 0.8, sz * 0.8, 0.9 * vis);
        continue;
      }
      const b = it.b;
      let all = true, minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
      for (let i = 0; i < 8; i++) {
        const v = pc(cam, i & 1 ? b.x1 : b.x0, i & 2 ? b.y1 : b.y0, i & 4 ? b.z1 : b.z0, P8[i]);
        all = all && v;
        minx = Math.min(minx, P8[i][0]); maxx = Math.max(maxx, P8[i][0]); miny = Math.min(miny, P8[i][1]); maxy = Math.max(maxy, P8[i][1]);
      }
      if (all && (maxx < -20 || minx > W + 20 || maxy < -20 || miny > H + 20)) continue;
      const nk = clamp(1 - d / 16);
      const lw = clamp(0.5 + 6 / Math.max(1, d), 0.5, 2.2);
      if (all) {
        const hp = hull(P8.map((qq) => [qq[0], qq[1]]));
        g.beginPath(); g.moveTo(hp[0][0], hp[0][1]); for (let i = 1; i < hp.length; i++) g.lineTo(hp[i][0], hp[i][1]); g.closePath();
        g.globalAlpha = 0.86; g.fillStyle = bgS; g.fill();
        if (b.lit) {
          const pulse = 0.55 + 0.45 * Math.sin(tc * 2.2 + b.ph) * (0.4 + en);
          g.globalAlpha = (0.05 + 0.1 * pulse) * vis; g.fillStyle = rgba(lineC, 1); g.fill();
        }
      }
      g.strokeStyle = rgba(mix(lineC, hotC, nk * 0.6 + (b.lit ? 0.25 : 0)), 1);
      g.globalAlpha = clamp((0.2 + 0.8 * vis) * vis * (b.lit ? 1 : 0.85)); g.lineWidth = lw;
      g.beginPath();
      if (all) for (const [i, j] of BOX_E) { g.moveTo(P8[i][0], P8[i][1]); g.lineTo(P8[j][0], P8[j][1]); }
      else for (const [i, j] of BOX_E) {
        seg3(g, cam, i & 1 ? b.x1 : b.x0, i & 2 ? b.y1 : b.y0, i & 4 ? b.z1 : b.z0, j & 1 ? b.x1 : b.x0, j & 2 ? b.y1 : b.y0, j & 4 ? b.z1 : b.z0);
      }
      g.stroke();
      if (b.sub && all) { // panel subdivisions on the near-z face
        g.lineWidth = lw * 0.6; g.globalAlpha *= 0.55; g.beginPath();
        for (let st = 1; st <= b.sub; st++) {
          const yy = lerp(b.y0, b.y1, st / (b.sub + 1));
          seg3(g, cam, b.x0, yy, b.z0, b.x1, yy, b.z0);
        }
        if (b.sub > 1) { const xx = lerp(b.x0, b.x1, 0.5); seg3(g, cam, xx, b.y0, b.z0, xx, b.y1, b.z0); }
        g.stroke();
      }
      if (b.node >= 0 && all) {
        const qq = P8[b.node], sz = Math.max(2, 0.08 * qq[3]);
        blob(q, gs, qq[0], qq[1], sz * 6 * (1 + en), sz * 6 * (1 + en), 0.9 * vis);
        g.globalAlpha = vis; g.fillStyle = rgba(hotC, 1); g.fillRect(qq[0] - sz / 2, qq[1] - sz / 2, sz, sz);
      }
    }
    return { cam };
  });
}

/* ================================================================ hall of voices (+ shared crowd hall) */
const HZ = 6;
function hallCell(seed, iz, kind) {
  const r = rng('hall', kind, seed, iz), zc = iz * HZ;
  const figs = [], lamps = [], strips = [];
  if (kind === 'alarm') {
    const n = 2 + Math.floor(r() * 3);
    for (let k = 0; k < n; k++) {
      let x = (r() - 0.5) * 18; if (Math.abs(x) < 2.0) x = Math.sign(x || 1) * (2.0 + r() * 2);
      figs.push({ x, z: zc + r() * HZ, h: 2.6 + r() * 2.2, flip: r() < 0.5, ph: r() * 9 });
    }
  } else {
    for (const sd of [-1, 1]) {
      if (r() > 0.08) figs.push({ x: sd * (3.4 + r() * 0.4), z: zc + r() * 1.0, h: 4.4 + r() * 0.8, flip: r() < 0.5, ph: r() * 9 });
      if (r() > 0.15) figs.push({ x: sd * (7.2 + r() * 0.8), z: zc + 3 + r() * 1.0, h: 5.4 + r() * 1.0, flip: r() < 0.5, ph: r() * 9 });
    }
    const s0 = iz % 2 ? 1 : -1;
    lamps.push({ x: s0 * (1.2 + r() * 1.0), y: 5.8 + r() * 1.6, z: zc + r() * HZ, ceil: 12, r: 0.42, R: 1.7, ph: r() * 9 });
    if (r() < 0.6) lamps.push({ x: -s0 * (4.8 + r() * 1.6), y: 6.6 + r() * 1.4, z: zc + r() * HZ, ceil: 12, r: 0.5, R: 2.0, ph: r() * 9 });
    strips.push({ x: 0, y: 9.2, z: zc + HZ * 0.5, hw: 1.25, hd: 0.16 });
    strips.push({ x: 0, y: 9.2, z: zc + HZ * 0.5 + 0.7, hw: 1.25, hd: 0.16 });
  }
  return { figs, lamps, strips };
}
/** dark backdrop: solid bg (sharp layer) + horizon haze band and glow (light buffer) */
function hallBackdrop(g, q, cam, pal, k = 1) {
  bgFill(g, pal.bg);
  const o = [0, 0, 0, 0];
  const hl = Math.hypot(cam.fx, cam.fz) || 1;
  pc(cam, cam.px + (cam.fx / hl) * 800, cam.py, cam.pz + (cam.fz / hl) * 800, o);
  const hy = o[1], hx = o[0];
  const gr = q.createLinearGradient(0, hy - 700, 0, hy + 560);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.5, rgba(pal.haze, 0.55 * k)); gr.addColorStop(0.56, rgba(pal.haze, 0.6 * k)); gr.addColorStop(1, 'rgba(0,0,0,0)');
  q.globalAlpha = 1; q.fillStyle = gr; q.fillRect(-80, -80, W + 160, H + 160);
  blob(q, glowSprite(pal.haze), hx, hy, 1100, 460, 0.9 * k);
  return [hx, hy];
}
function hallFloorGrid(g, cam, pal, FAR, a = 1) {
  g.strokeStyle = rgba(pal.line, 1); g.lineWidth = 1;
  const z0 = cam.pz + 0.4;
  const chunks = [[0, 8, 0.2], [8, 20, 0.13], [20, 36, 0.07], [36, FAR, 0.03]];
  for (const [c0, c1, al] of chunks) {
    g.globalAlpha = al * a; g.beginPath();
    for (let k = -7; k <= 7; k++) seg3(g, cam, k * 2.2, 0, z0 + c0, k * 2.2, 0, z0 + c1);
    g.stroke();
  }
  const m0 = Math.ceil(z0 / 2.5), m1 = Math.floor((z0 + FAR) / 2.5);
  for (let m = m0; m <= m1; m++) {
    const z = m * 2.5; cs(cam, 0, 0, z, _a);
    const vis = fog(Math.max(0, _a[2]), FAR, 0, 1.4); if (vis < 0.02) continue;
    g.globalAlpha = 0.15 * vis * a; g.beginPath(); seg3(g, cam, -16, 0, z, 16, 0, z); g.stroke();
  }
}
function dust(g, cam, t, pal, n, seed, area, a = 1) {
  const o = [0, 0, 0, 0]; const DEP = area.depth || 30;
  g.fillStyle = rgba(pal.hot, 1);
  for (let i = 0; i < n; i++) {
    const r = rng('dust', seed, i);
    const bx = (r() - 0.5) * area.w, by = area.y0 + r() * area.h, bz = r() * DEP;
    const z = cam.pz + 0.5 + (((bz - cam.pz) % DEP) + DEP) % DEP;
    const x = bx + Math.sin(t * 0.21 + i * 1.7) * 0.5, y = by + Math.sin(t * 0.27 + i * 2.3) * 0.35;
    if (!pc(cam, x, y, z, o)) continue;
    const fade = clamp((o[2] - 0.8) / 2.5) * fog(o[2], DEP + 2, 0, 1.2);
    const sz = Math.max(1, 0.025 * o[3]);
    g.globalAlpha = 0.5 * fade * a * (0.6 + 0.4 * Math.sin(t * 1.3 + i));
    g.fillRect(o[0] - sz / 2, o[1] - sz / 2, sz, sz);
  }
}

/**
 * hallOfVoices(ctx, t, {tint, energy, cam, seed, alpha, bloom, lampLevel})
 * dark stage, two rows per side of glowing capsule copies of Claude receding, hanging lamps with light cones,
 * ceiling light strips, floor grid + reflections, dust. Default camera: slow push-in 0.65 units/s at eye height
 * 1.45 looking slightly up. lampLevel 0..1 (default 1) dims the lamps — far ones die first (outro).
 */
export function hallOfVoices(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 3 : p.seed;
  const tc = pathT(t, p.cam);
  const px = Math.sin(tc * 0.1) * 0.5, pz = tc * 0.65;
  const cam = resolveCam({
    pos: [px, 1.45 + Math.sin(tc * 0.13) * 0.12, pz],
    target: [px * 0.4 + Math.sin(tc * 0.07) * 0.6, 2.8, pz + 12], roll: Math.sin(tc * 0.06) * 0.03, fov: 60,
  }, p.cam);
  const pal = envPalette(p.tint || 0);
  const lampLevel = p.lampLevel == null ? 1 : clamp(p.lampLevel);
  return envRun(ctx, p, { radius: 28, strength: 0.45, wide: 0.6, threshold: 0.35 }, (g, q) => {
    const FAR = 60;
    hallBackdrop(g, q, cam, pal, 0.5 + 0.5 * lampLevel);
    hallFloorGrid(g, cam, pal, FAR);
    const set = voiceSet(p.tint || 0, 0);
    const items = [];
    const iz0 = Math.floor((cam.pz - 3) / HZ), iz1 = Math.floor((cam.pz + FAR) / HZ);
    for (let iz = iz0; iz <= iz1; iz++) {
      const c = hallCell(seed, iz, 'hall');
      for (const f of c.figs) { cs(cam, f.x, f.h / 2, f.z, _a); if (_a[2] > 1.2 && _a[2] < FAR) items.push({ d: _a[2], f }); }
      for (const l of c.lamps) { cs(cam, l.x, l.y, l.z, _a); if (_a[2] > 0.4 && _a[2] < FAR) items.push({ d: _a[2], l }); }
      for (const st of c.strips) { cs(cam, st.x, st.y, st.z, _a); if (_a[2] > 0.4 && _a[2] < FAR) items.push({ d: _a[2], s: st }); }
    }
    items.sort((a, b) => b.d - a.d);
    for (const it of items) {
      if (it.f) {
        const vis = fog(it.d, FAR, 0, 1.5) * clamp((it.d - 3.2) / 1.6);
        const fl = 0.965 + 0.035 * rnd('hv', seed, it.f.ph, bucket(t, 12));
        drawVoice(g, q, cam, set, it.f.x, it.f.z, it.f.h, vis * fl * (0.85 + 0.15 * en), it.f.flip);
      } else if (it.l) {
        const die = clamp((lampLevel - 1) * 3 + 1 + (1 - it.d / FAR) * 2 * (1 - lampLevel)); // far lamps die first
        const inten = (0.7 + 0.35 * en + 0.08 * Math.sin(tc * 3 + it.l.ph)) * die;
        drawLamp(g, q, cam, { ...it.l, far: FAR }, pal, inten, 0);
      } else {
        drawBar(g, q, cam, it.s.x, it.s.y, it.s.z, it.s.hw, it.s.hd, pal.hot, pal.glow, (0.8 + 0.2 * en) * lampLevel, 0.6, FAR);
      }
    }
    dust(g, cam, t, pal, 150, seed, { w: 16, y0: 0, h: 8, depth: 30 });
    return { cam };
  });
}

/* ================================================================ alarmField */
const FRAG_CROPS = [
  ['face', 0.5, 0.42, 1.2], ['face', 0.32, 0.5, 2.6], ['face', 0.62, 0.48, 2.4], ['bust', 0.5, 0.3, 1.4],
  ['bust', 0.3, 0.6, 1.8], ['full', 0.5, 0.14, 3.0], ['full', 0.45, 0.5, 2.2], ['full', 0.55, 0.78, 2.0],
  ['book', 0.5, 0.5, 1.2], ['bust', 0.75, 0.5, 1.6], ['face', 0.5, 0.75, 1.8], ['full', 0.3, 0.3, 2.5],
];
function tornPoly(r) {
  const pts = [], jag = 0.07;
  const edge = (x0, y0, x1, y1, n, nx, ny) => {
    for (let i = 0; i < n; i++) { const k = i / n, j = (r() - 0.2) * jag; pts.push([lerp(x0, x1, k) + nx * j, lerp(y0, y1, k) + ny * j]); }
  };
  edge(0, 0, 1, 0, 5, 0, 1); edge(1, 0, 1, 1, 4, -1, 0); edge(1, 1, 0, 1, 5, 0, -1); edge(0, 1, 0, 0, 4, 1, 0);
  if (r() < 0.45) { // tear off a corner
    const c = Math.floor(r() * 4), lim = 0.35 + r() * 0.2, cx = c & 1 ? 1 : 0, cy = c & 2 ? 1 : 0;
    const keep = pts.filter((qq) => Math.abs(qq[0] - cx) + Math.abs(qq[1] - cy) > lim);
    return keep.length > 4 ? keep : pts;
  }
  return pts;
}
function rotE(x, y, z, a, b, c) { // Euler: Z(c) then X(a) then Y(b)
  let cc = Math.cos(c), sc = Math.sin(c); [x, y] = [x * cc - y * sc, x * sc + y * cc];
  cc = Math.cos(a); sc = Math.sin(a); [y, z] = [y * cc - z * sc, y * sc + z * cc];
  cc = Math.cos(b); sc = Math.sin(b); [x, z] = [x * cc + z * sc, -x * sc + z * cc];
  return [x, y, z];
}
/** cheap chromatic fringe on the ¼-res glow: red copy shifted right, cyan copy shifted left */
function glowFringe(cx, src, w4, h4, px) {
  if (px < 0.2) return;
  const f = scratch('fringe', w4, h4), fx = f.getContext('2d');
  for (const [col, dx] of [['#ff2a10', px], ['#10e0ff', -px]]) {
    prep(fx); fx.globalCompositeOperation = 'copy'; fx.drawImage(src, 0, 0);
    fx.globalCompositeOperation = 'multiply'; fx.fillStyle = col; fx.fillRect(0, 0, w4, h4);
    fx.globalCompositeOperation = 'destination-in'; fx.drawImage(src, 0, 0);
    cx.globalAlpha = 0.6; cx.drawImage(f, dx, 0);
  }
  cx.globalAlpha = 1;
}

/**
 * alarmField(ctx, t, {tint, energy, cam, seed, alpha, bloom, fragments, aberration})
 * black void lit alarm-red (#E8452A; tint → orange-red): rows of ceiling light bars, runway bars + laser lines,
 * the capsule crowd lit alarm, torn photo fragments (image crops in torn polygons) tumbling towards the camera,
 * a cheap colour fringe on the glow, and — if `aberration` (px) is given — a full-frame chromatic split
 * (≈ +12 ms). fragments = count (default 14 + 10·energy).
 */
export function alarmField(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 11 : p.seed, tint = clamp(p.tint || 0);
  const tc = pathT(t, p.cam), SPD = 0.55;
  const px = Math.sin(tc * 0.08) * 0.8, pz = tc * SPD;
  const cam = resolveCam({
    pos: [px, 1.6, pz], target: [Math.sin(tc * 0.05) * 1.2, 2.5 + Math.sin(tc * 0.09) * 0.4, pz + 12],
    roll: 0.03 + Math.sin(tc * 0.07) * 0.05, fov: 62,
  }, p.cam);
  const al = lerp(1, 0.4, tint);
  const pal = envPalette(tint, al);
  const pal2 = { ...pal, hot: mix(pal.hot, '#ffffff', 0.4) };
  return envRun(ctx, p, { radius: 26, strength: 0.45, wide: 0.6, threshold: 0.35 }, (g, q) => {
    const FAR = 60, o = [0, 0, 0, 0];
    bgFill(g, pal.bg);
    pc(cam, cam.px + cam.fx * 400, cam.py, cam.pz + 400, o);
    blob(q, glowSprite(pal.haze), o[0], o[1], 1300, 520, 0.9);
    const iz0 = Math.floor((cam.pz - 3) / HZ), iz1 = Math.floor((cam.pz + FAR) / HZ);
    // laser lines on the floor + in the air
    g.strokeStyle = rgba(pal.line, 1);
    for (let iz = iz0 - 2; iz <= iz1; iz++) {
      const r = rng('laser', seed, iz), zc = iz * HZ;
      for (let k = 0; k < 2; k++) {
        const x0 = (r() - 0.5) * 30, x1 = (r() - 0.5) * 30, za = zc + r() * HZ, zb = za + 6 + r() * 16, y = r() < 0.3 ? 0.4 + r() * 5 : 0.01;
        cs(cam, (x0 + x1) / 2, y, (za + zb) / 2, _a); const vis = fog(Math.max(0, _a[2]), FAR, 0, 1.1);
        const fl = 0.65 + 0.35 * Math.sin(tc * 7 + iz * 3 + k) * en;
        g.lineWidth = 1.4; g.globalAlpha = 0.7 * vis * fl; g.beginPath(); seg3(g, cam, x0, y, za, x1, y, zb); g.stroke();
      }
    }
    const items = [];
    const set = voiceSet(tint, al);
    for (let iz = iz0; iz <= iz1; iz++) {
      const c = hallCell(seed, iz, 'alarm');
      for (const f of c.figs) { cs(cam, f.x, f.h / 2, f.z, _a); if (_a[2] > 1.2 && _a[2] < FAR) items.push({ d: _a[2], f }); }
      const zc = iz * HZ + HZ / 2; cs(cam, 0, 7.5, zc, _a);
      if (_a[2] > 0.5 && _a[2] < FAR) items.push({ d: _a[2], row: iz, z: zc });
    }
    items.sort((a, b) => b.d - a.d);
    for (const it of items) {
      if (it.f) {
        const vis = fog(it.d, FAR, 0, 1.4) * clamp((it.d - 4) / 1.6);
        const fl = 0.95 + 0.05 * rnd('af', seed, it.f.ph, bucket(t, 15));
        drawVoice(g, q, cam, set, it.f.x, it.f.z, it.f.h, vis * fl, it.f.flip, true, 0.45);
      } else {
        const pulse = 0.65 + 0.35 * Math.sin(tc * 4.5 - it.row * 1.2) * (0.3 + en);
        for (let k = -3; k <= 3; k++) drawBar(g, q, cam, k * 2.5, 7.5, it.z, 0.75, 0.12, pal2.hot, pal.glow, pulse, 0.8, FAR);
        for (const sd of [-1, 1]) drawBar(g, q, cam, sd * 1.5, 0.02, it.z, 0.45, 0.05, pal2.hot, pal.glow, 0.8 * pulse, 0.5, FAR);
      }
    }
    // torn fragments
    const N = p.fragments == null ? Math.round(14 + 10 * en) : p.fragments;
    const frs = [];
    for (let i = 0; i < N; i++) {
      const r0 = rng('frag', seed, i), life = 3.5 + r0() * 3, ph = r0() * life;
      const age = (tc + ph) % life, gen = Math.floor((tc + ph) / life);
      const r = rng('frag', seed, i, gen);
      const sx = (r() - 0.5) * 13, sy = 0.6 + r() * 6, sz = (tc - age) * SPD + 14 + r() * 16;
      const vx = (r() - 0.5) * 1.6, vy = (r() - 0.45) * 0.9, vz = -(2.5 + r() * 4);
      const wa = (r() - 0.5) * 3, wb = (r() - 0.5) * 3, wc = (r() - 0.5) * 2;
      const a0 = r() * TAU, b0 = r() * TAU, c0 = r() * TAU;
      const fw = 0.9 + r() * 1.4, fh = fw * (0.6 + r() * 0.5);
      const crop = FRAG_CROPS[Math.floor(r() * FRAG_CROPS.length)], hotF = r() < 0.2;
      const poly = tornPoly(r);
      const cx = sx + vx * age, cy = sy + vy * age, cz = sz + vz * age;
      const ea = a0 + wa * age, eb = b0 + wb * age, ec = c0 + wc * age;
      const fade = clamp(age / 0.5) * clamp((life - age) / 0.8);
      const pts = [[-fw / 2, fh / 2], [fw / 2, fh / 2], [-fw / 2, -fh / 2], [fw / 2, -fh / 2]].map(([lx, ly]) => { const qq = rotE(lx, ly, 0, ea, eb, ec); return [cx + qq[0], cy + qq[1], cz + qq[2]]; });
      const pr = pts.map(() => [0, 0, 0, 0]);
      let ok = true; for (let k = 0; k < 4; k++) ok = pc(cam, pts[k][0], pts[k][1], pts[k][2], pr[k]) && pr[k][2] > 2.2 && ok;
      if (!ok || fade <= 0.01) continue;
      frs.push({ d: pr[0][2], pr, crop, hotF, poly, fade: fade * clamp((pr[0][2] - 2.2) / 2) });
    }
    frs.sort((a, b) => b.d - a.d);
    const base = g.getTransform();
    const fragCol = mix(pal.line, '#FFE0D6', 0.45);
    for (const fr of frs) {
      const [p0, p1, p2] = fr.pr, vis = fog(fr.d, 40, 0, 0.8) * fr.fade;
      const ax = p1[0] - p0[0], ay = p1[1] - p0[1], bx = p2[0] - p0[0], by = p2[1] - p0[1];
      const area = Math.abs(ax * by - ay * bx); if (area < 4 || vis < 0.01) continue;
      const back = ax * by - ay * bx < 0;
      blob(q, glowSprite(pal.glow), p0[0] + (ax + bx) / 2, p0[1] + (ay + by) / 2, Math.sqrt(area) * 1.2, Math.sqrt(area) * 1.2, 0.18 * vis);
      const img = duotone(fr.crop[0], fr.hotF ? mix(pal.hot, '#ffffff', 0.5) : fragCol, 160, 120, fr.crop[1], fr.crop[2], fr.crop[3]);
      g.transform(ax, ay, bx, by, p0[0], p0[1]);
      g.beginPath(); g.moveTo(fr.poly[0][0], fr.poly[0][1]); for (let k = 1; k < fr.poly.length; k++) g.lineTo(fr.poly[k][0], fr.poly[k][1]); g.closePath();
      g.save(); g.clip();
      g.globalAlpha = vis;
      if (img) g.drawImage(img, 0, 0, 1, 1); else { g.fillStyle = rgba(pal.line, 1); g.fillRect(0, 0, 1, 1); }
      if (back) { g.globalAlpha = 0.55 * vis; g.fillStyle = '#000'; g.fillRect(0, 0, 1, 1); }
      g.restore();
      g.lineWidth = 2.2 / Math.sqrt(area); g.globalAlpha = 0.85 * vis; g.strokeStyle = rgba(pal2.hot, 1); g.stroke();
      g.setTransform(base);
    }
    dust(g, cam, t, pal2, 90, seed, { w: 18, y0: 0, h: 8, depth: 26 });
    const fr = 0.8 + 1.4 * en;
    return {
      cam,
      fringe: (cx, c4b, w4, h4) => glowFringe(cx, c4b, w4, h4, fr),
      post: p.aberration ? (gg) => chromatic(gg, p.aberration) : null,
    };
  });
}

/* ================================================================ lightTunnel */
/**
 * lightTunnel(ctx, t, {tint, energy, cam, seed, alpha, bloom})
 * kaleidoscopic square tunnel: one quadrant of rings / diagonal light fixtures / wall strips is drawn and
 * mirrored left/right + top/bottom around the vanishing point; rings travel towards the viewer (1.4 rings/s,
 * faster with energy), the figure rolls back and forth slowly (±0.2 rad). cam: { dolly (extra rings travelled),
 * strafe / rise (vanishing-point shift, 1 unit = 120 px), roll (rad, added), zoom, speed, offset }.
 */
export function lightTunnel(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 5 : p.seed, o = p.cam || {};
  const tc = pathT(t, o);
  const travel = tc * 1.4 + (o.dolly || 0);
  const roll = 0.16 * Math.sin(tc * 0.05) + 0.045 * Math.sin(tc * 0.23) + (o.roll || 0);
  const zoom = o.zoom || 1;
  const vx = W / 2 + (o.strafe || 0) * 120 + Math.sin(tc * 0.17) * 18, vy = H / 2 - (o.rise || 0) * 120 + Math.sin(tc * 0.13) * 10;
  const pal = envPalette(p.tint || 0);
  return envRun(ctx, p, { radius: 24, strength: 0.8, wide: 0.55, threshold: 0.1 }, (g, q) => {
    bgFill(g, pal.bg);
    g.translate(vx, vy); g.rotate(roll);
    q.translate(vx, vy); q.rotate(roll);
    blob(q, glowSprite(pal.haze), 0, 0, 900, 900, 0.7);
    const f = 560 * zoom, N = 44, DZ = 0.62, ph = fract(travel), i0 = Math.floor(travel), R = 1500;
    const gs = glowSprite(pal.glow);
    const lineS = rgba(pal.line, 1), hotS = rgba(pal.hot, 1);
    const rings = [];
    for (let k = N - 1; k >= 0; k--) {
      const z = (k + 1 - ph) * DZ + 0.2, sz = f / z;
      if (sz > R * 1.6) continue;
      const id = i0 + k, vis = Math.pow(1 - (k + 1 - ph) / N, 0.9) * clamp((k + 1 - ph) / 1.5);
      rings.push({ s: sz, id, vis, k });
    }
    const quadrant = (G, Q) => {
      // longitudinal lines (diagonal, wall rails, axis seams)
      G.strokeStyle = lineS; G.lineWidth = 1.2;
      G.globalAlpha = 0.35; G.beginPath(); G.moveTo(0, 0); G.lineTo(-R, -R); G.stroke();
      G.globalAlpha = 0.2; G.lineWidth = 1; G.beginPath();
      for (const qq of [0.2, 0.4, 0.6, 0.8]) { G.moveTo(0, 0); G.lineTo(-R * qq, -R); G.moveTo(0, 0); G.lineTo(-R, -R * qq); }
      G.stroke();
      G.globalAlpha = 0.1; G.beginPath(); G.moveTo(0, 0); G.lineTo(-R * 1.5, 0); G.moveTo(0, 0); G.lineTo(0, -R * 1.5); G.stroke();
      // bright X along the diagonal (soft)
      Q.globalAlpha = 0.14 + 0.14 * en; Q.strokeStyle = rgba(pal.glow, 1); Q.lineWidth = 16; Q.beginPath(); Q.moveTo(-20, -20); Q.lineTo(-R, -R); Q.stroke();
      for (const rg of rings) {
        const { s: sz, id, vis } = rg, r = rng('tun', seed, id);
        const lw = clamp(sz / 300, 0.5, 3.5);
        G.strokeStyle = lineS; G.lineWidth = lw; G.globalAlpha = 0.75 * vis;
        G.beginPath(); G.moveTo(-sz, 0); G.lineTo(-sz, -sz); G.lineTo(0, -sz); G.stroke();
        if (id % 2 === 0) { G.lineWidth = lw * 0.5; G.globalAlpha = 0.3 * vis; G.beginPath(); G.moveTo(-sz * 0.95, 0); G.lineTo(-sz * 0.95, -sz * 0.95); G.lineTo(0, -sz * 0.95); G.stroke(); }
        if (rg.k > 8 && id % 3 === 0) { G.lineWidth = lw; G.globalAlpha = 0.4 * vis; G.beginPath(); G.moveTo(0, -sz * 1.35); G.lineTo(-sz * 1.35, 0); G.stroke(); }
        const pulse = 0.5 + 0.5 * Math.sin(tc * 5.5 - id * 0.8);
        const bright = (0.5 + 0.5 * pulse * (0.3 + en)) * vis;
        if (id % 2 === 0) { // corner fixture on the diagonal
          blob(Q, gs, -sz * 0.92, -sz * 0.92, sz * 0.5, sz * 0.5, 1.0 * bright);
          G.strokeStyle = hotS; G.lineWidth = clamp(sz / 60, 1, 14); G.globalAlpha = bright;
          G.beginPath(); G.moveTo(-sz, -sz); G.lineTo(-sz * 0.84, -sz * 0.84); G.stroke();
        }
        if (id % 3 === 1) { // ceiling + wall strips across the tunnel
          const aa = 0.15 + r() * 0.3, bb = aa + 0.1 + r() * 0.2;
          G.strokeStyle = hotS; G.lineWidth = clamp(sz / 110, 1, 8); G.globalAlpha = 0.85 * bright;
          G.beginPath(); G.moveTo(-sz * aa, -sz); G.lineTo(-sz * bb, -sz); G.moveTo(-sz, -sz * aa); G.lineTo(-sz, -sz * bb); G.stroke();
          blob(Q, gs, -sz * (aa + bb) / 2, -sz, sz * 0.22, sz * 0.07, 0.8 * bright);
          blob(Q, gs, -sz, -sz * (aa + bb) / 2, sz * 0.07, sz * 0.22, 0.8 * bright);
        }
        if (id % 5 === 2) { // small ticks along the rim
          G.strokeStyle = lineS; G.lineWidth = Math.max(0.6, lw * 0.6); G.globalAlpha = 0.45 * vis; G.beginPath();
          for (let m = 1; m < 6; m++) { const u = -sz * m / 6; G.moveTo(u, -sz); G.lineTo(u, -sz * 0.97); G.moveTo(-sz, u); G.lineTo(-sz * 0.97, u); }
          G.stroke();
        }
      }
      // streaks rushing outward along the diagonal / rails
      G.strokeStyle = hotS;
      for (let i = 0; i < 8; i++) {
        const rr = rng('streak', seed, i), sp = 0.5 + rr() * 0.7, qq = [1, 0.4, 0.6, 0.2][i % 4];
        const z = 0.3 + fract(-tc * sp * (0.6 + en * 0.8) + rr()) * 18, z2 = z + 0.7 + rr();
        const s1 = f / z, s2 = f / z2;
        G.globalAlpha = clamp(0.25 + 0.5 * en) * (1 - z / 18); G.lineWidth = clamp(s1 / 200, 1, 5);
        G.beginPath(); G.moveTo(-s2 * (i % 2 ? qq : 1), -s2 * (i % 2 ? 1 : qq)); G.lineTo(-s1 * (i % 2 ? qq : 1), -s1 * (i % 2 ? 1 : qq)); G.stroke();
      }
    };
    const baseG = g.getTransform(), baseQ = q.getTransform();
    for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {
      g.setTransform(baseG); g.scale(sx, sy); q.setTransform(baseQ); q.scale(sx, sy); quadrant(g, q);
    }
    g.setTransform(baseG); q.setTransform(baseQ);
    blob(q, glowSprite(pal.hot), 0, 0, 80 * (1 + en * 0.8), 80 * (1 + en * 0.8), 1);
    blob(q, gs, 0, 0, 300, 300, 0.6 + 0.3 * en);
    blob(g, glowSprite(pal.hot), 0, 0, 26 * (1 + en * 0.6), 26 * (1 + en * 0.6), 0.9);
    return { cam: { vp: [vx, vy], roll, zoom, f } };
  });
}

/* ================================================================ orb */
let mottle = null;
function mottleTex() {
  if (mottle) return mottle;
  mottle = makeCanvas(256, 256); const x = mottle.getContext('2d');
  x.fillStyle = '#b4b4b4'; x.fillRect(0, 0, 256, 256);
  const r = rng('mottle', 1);
  for (let i = 0; i < 520; i++) {
    const cx = r() * 256, cy = r() * 256, rad = 3 + r() * r() * 40, v = r() < 0.45 ? 255 : 70 + r() * 70;
    const gr = x.createRadialGradient(cx, cy, 0, cx, cy, rad);
    gr.addColorStop(0, `rgba(${v | 0},${v | 0},${v | 0},${0.3 + r() * 0.4})`); gr.addColorStop(1, `rgba(${v | 0},${v | 0},${v | 0},0)`);
    x.fillStyle = gr; x.fillRect(cx - rad, cy - rad, rad * 2, rad * 2);
  }
  // limb darkening baked in
  const lg = x.createRadialGradient(128, 128, 60, 128, 128, 128);
  lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(1, 'rgba(60,60,60,0.55)');
  x.fillStyle = lg; x.fillRect(0, 0, 256, 256);
  return mottle;
}
/**
 * orb(ctx, t, {tint, energy, cam, seed, alpha, bloom, radius})
 * huge glowing sphere (mottled surface, slow spin) with 5 tilted concentric 3D rings (depth-split in front of /
 * behind the sphere), orbiting satellites, flat HUD circles, parallax bokeh and drifting haze.
 * Default camera: slow orbit (0.11 rad/s) at distance 11±1.2, gentle bob. Returns { cam, center, radiusPx }.
 */
export function orb(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 9 : p.seed;
  const tc = pathT(t, p.cam), a = tc * 0.11, D = 11 + Math.sin(tc * 0.15) * 1.2;
  const cam = resolveCam({
    pos: [Math.sin(a) * D, 0.9 + Math.sin(tc * 0.045) * 1.2, -Math.cos(a) * D],
    target: [0, 0.15 * Math.sin(tc * 0.1), 0], roll: 0.05 * Math.sin(tc * 0.05), fov: 48,
  }, p.cam);
  const pal = envPalette(p.tint || 0);
  const R = p.radius || 2.3;
  return envRun(ctx, p, { radius: 30, strength: 0.7, wide: 0.6, threshold: 0.35 }, (g, q) => {
    bgFill(g, pal.bg);
    const oc = [0, 0, 0, 0], o = [0, 0, 0, 0];
    pc(cam, 0, 0, 0, oc);
    const Rs = R * oc[3], gs = glowSprite(pal.glow), gh = glowSprite(pal.hot);
    blob(q, glowSprite(pal.haze), oc[0], oc[1], 1500, 1100, 1);
    for (let i = 0; i < 6; i++) {
      const r = rng('ohaze', seed, i);
      const hx = oc[0] + Math.sin(tc * 0.05 * (0.5 + r()) + r() * 6) * 700, hy = oc[1] + Math.cos(tc * 0.04 * (0.5 + r()) + r() * 6) * 380;
      blob(q, gs, hx, hy, 300 + r() * 300, 200 + r() * 200, 0.12 + 0.06 * en);
    }
    for (let i = 0; i < 80; i++) { // parallax bokeh on a far shell
      const r = rng('bokeh', seed, i), th = r() * TAU, ph2 = Math.acos(2 * r() - 1), rr = 13 + r() * 14;
      if (!pc(cam, rr * Math.sin(ph2) * Math.cos(th), rr * Math.cos(ph2) * 0.6, rr * Math.sin(ph2) * Math.sin(th), o)) continue;
      const tw = 0.5 + 0.5 * Math.sin(t * (0.7 + r() * 1.5) + i);
      const sz = Math.max(1.2, 0.05 * o[3]);
      blob(q, gs, o[0], o[1], sz * 7, sz * 7, 0.5 * tw);
      g.globalAlpha = 0.8 * tw; g.fillStyle = rgba(pal.hot, 1); g.beginPath(); g.arc(o[0], o[1], sz, 0, TAU); g.fill();
    }
    const hc = rgba(pal.line, 1);
    ring(g, oc[0], oc[1], { r: Rs * 1.75, color: hc, alpha: 0.4, lw: 1, ticks: 120, tickLen: 5, major: 10, rot: tc * 0.05, arcs: [[0.2, 2.6], [3.0, 5.9]] });
    ring(g, oc[0], oc[1], { r: Rs * 2.45, color: hc, alpha: 0.26, lw: 1, dash: [2, 7], rot: -tc * 0.03 });
    ring(g, oc[0], oc[1], { r: Rs * 3.4, color: hc, alpha: 0.2, lw: 1.2, arcs: [[-0.4, 0.9], [2.4, 3.6]], rot: tc * 0.02, dots: 24, dotOff: 10 });
    const rings = [];
    const radii = [3.0, 3.6, 4.6, 6.2, 8.6];
    for (let j = 0; j < 5; j++) {
      const r = rng('oring', seed, j);
      const th = r() * TAU + tc * 0.03 * (j % 2 ? 1 : -1), phi = 0.15 + r() * 0.55;
      const n = [Math.sin(phi) * Math.cos(th), Math.cos(phi), Math.sin(phi) * Math.sin(th)];
      let u = [n[1], -n[0], 0]; const ul = Math.hypot(...u) || 1; u = u.map((v) => v / ul);
      const v = [n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0]];
      const rr = radii[j] * (R / 2.3), NS = 120, pts = [];
      for (let i = 0; i <= NS; i++) {
        const an = (i / NS) * TAU, c = Math.cos(an), sn = Math.sin(an);
        const qq = [0, 0, 0, 0]; pc(cam, rr * (c * u[0] + sn * v[0]), rr * (c * u[1] + sn * v[1]), rr * (c * u[2] + sn * v[2]), qq); pts.push(qq);
      }
      const sats = [];
      if (j !== 1 && j !== 4) for (let k = 0; k < 1 + (j === 2 ? 2 : 1); k++) {
        const an = r() * TAU + tc * (0.35 / (j + 1)) * (k % 2 ? -1 : 1), c = Math.cos(an), sn = Math.sin(an);
        const qq = [0, 0, 0, 0]; pc(cam, rr * (c * u[0] + sn * v[0]), rr * (c * u[1] + sn * v[1]), rr * (c * u[2] + sn * v[2]), qq); sats.push(qq);
      }
      rings.push({ j, pts, sats });
    }
    const style = (j) => {
      g.strokeStyle = rgba(j === 0 ? mix(pal.line, pal.hot, 0.5) : pal.line, 1);
      g.lineWidth = [1.8, 1.2, 1.5, 1, 1.4][j]; g.globalAlpha = [0.9, 0.65, 0.75, 0.55, 0.35][j];
      g.setLineDash(j === 1 ? [10, 8] : j === 3 ? [2, 6] : []);
    };
    const drawRings = (front) => {
      for (const rg of rings) {
        style(rg.j); g.beginPath();
        for (let i = 1; i < rg.pts.length; i++) {
          const a0 = rg.pts[i - 1], a1 = rg.pts[i];
          if (((a0[2] + a1[2]) / 2 < oc[2]) !== front) continue;
          g.moveTo(a0[0], a0[1]); g.lineTo(a1[0], a1[1]);
        }
        g.stroke(); g.setLineDash([]);
        if (rg.j === 0) {
          g.beginPath();
          for (let i = 0; i < rg.pts.length - 1; i += 4) {
            const qq = rg.pts[i]; if ((qq[2] < oc[2]) !== front) continue;
            const dx = qq[0] - oc[0], dy = qq[1] - oc[1], l = Math.hypot(dx, dy) || 1, tl = i % 20 === 0 ? 14 : 6;
            g.moveTo(qq[0], qq[1]); g.lineTo(qq[0] + (dx / l) * tl, qq[1] + (dy / l) * tl);
          }
          g.stroke();
        }
        for (const qq of rg.sats) {
          if ((qq[2] < oc[2]) !== front) continue;
          const sz = Math.max(3, 0.1 * qq[3]);
          blob(q, gs, qq[0], qq[1], sz * 8, sz * 8, 0.9);
          g.globalAlpha = 1; g.fillStyle = rgba(pal.hot, 1); g.beginPath(); g.arc(qq[0], qq[1], sz, 0, TAU); g.fill();
        }
      }
    };
    drawRings(false);
    // sphere
    blob(q, gs, oc[0], oc[1], Rs * 3.2, Rs * 3.2, 0.9 * (0.75 + 0.4 * en));
    // the sphere occludes the light behind it: punch its disc out of the light buffer (rim keeps a little)
    q.globalCompositeOperation = 'destination-out'; q.globalAlpha = 0.92; q.fillStyle = '#000';
    q.beginPath(); q.arc(oc[0], oc[1], Rs * 0.9, 0, TAU); q.fill();
    q.globalCompositeOperation = 'lighter'; q.globalAlpha = 1;
    const sg = g.createRadialGradient(oc[0] - Rs * 0.25, oc[1] - Rs * 0.3, 0, oc[0], oc[1], Rs);
    sg.addColorStop(0, rgba(mix(pal.hot, pal.glow, 0.08), 1)); sg.addColorStop(0.55, rgba(mix(pal.hot, pal.glow, 0.35), 1));
    sg.addColorStop(0.9, rgba(mix(pal.glow, pal.bg, 0.25), 1)); sg.addColorStop(1, rgba(mix(pal.hot, pal.glow, 0.45), 1));
    g.globalAlpha = 1; g.fillStyle = sg; g.beginPath(); g.arc(oc[0], oc[1], Rs, 0, TAU); g.fill();
    g.save(); g.clip();
    g.translate(oc[0], oc[1]); g.rotate(tc * 0.12);
    g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.85; g.drawImage(mottleTex(), -Rs * 1.02, -Rs * 1.02, Rs * 2.04, Rs * 2.04);
    g.restore();
    g.strokeStyle = rgba(pal.hot, 1); g.globalAlpha = 0.75; g.lineWidth = Math.max(1.5, Rs * 0.02);
    g.beginPath(); g.arc(oc[0], oc[1], Rs, 0, TAU); g.stroke();
    drawRings(true);
    return { cam, center: [oc[0], oc[1]], radiusPx: Rs };
  });
}

/* ================================================================ monitors */
const MON = [
  { x: 0.0, y: 0.55, z: 9.0, w: 3.9, yaw: -0.16, pitch: 0.04, roll: -0.03, scr: 0 },
  { x: -4.7, y: 2.0, z: 11.5, w: 2.3, yaw: 0.45, pitch: -0.1, roll: 0.07, scr: 1 },
  { x: 4.9, y: 1.6, z: 10.5, w: 2.5, yaw: -0.52, pitch: 0.1, roll: -0.06, scr: 2 },
  { x: -3.7, y: -1.9, z: 7.4, w: 1.8, yaw: 0.32, pitch: 0.2, roll: 0.1, scr: 3 },
  { x: 4.0, y: -2.1, z: 7.9, w: 1.9, yaw: -0.38, pitch: 0.16, roll: -0.12, scr: 4 },
  { x: -8.4, y: 0.1, z: 15.5, w: 2.7, yaw: 0.62, pitch: 0.0, roll: 0.05, scr: 5 },
  { x: 8.9, y: -0.3, z: 16.5, w: 2.7, yaw: -0.6, pitch: 0.05, roll: -0.04, scr: 6 },
];
/** screen crops: [image, focusX, focusY, zoom] */
export const MONITOR_SCREENS = [
  ['face', 0.5, 0.45, 1.0], ['book', 0.5, 0.5, 1.0], ['bust', 0.52, 0.3, 1.3], ['face', 0.36, 0.5, 2.3],
  ['full', 0.5, 0.15, 3.0], ['bust', 0.4, 0.62, 1.6], ['full', 0.5, 0.5, 1.1],
];
const scrPool = [];
let scanPat = null;
function scanlinePattern() {
  if (scanPat) return scanPat;
  scanPat = makeCanvas(512, 384); const x = scanPat.getContext('2d');
  x.fillStyle = 'rgba(0,0,0,0.38)'; for (let y = 0; y < 384; y += 3) x.fillRect(0, y, 512, 1);
  const g = x.createRadialGradient(256, 192, 120, 256, 192, 330);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.75)');
  x.fillStyle = g; x.fillRect(0, 0, 512, 384);
  return scanPat;
}
const baseCache = new Map();
/** static part of a screen (duotone crop + lift), cached per crop / palette level / size */
function screenBase(crop, pal, SW, SH) {
  const named = typeof crop[0] === 'string';
  const key = named ? `${crop.join('|')}|${ck(pal.hot)}|${ck(pal.glow)}|${ck(pal.bg)}|${SW}` : null;
  let c = key && baseCache.get(key);
  if (c) return c;
  if (baseCache.size > 120) baseCache.clear();
  c = makeCanvas(SW, SH); const x = c.getContext('2d');
  x.fillStyle = rgba(mix(pal.bg, pal.glow, 0.18), 1); x.fillRect(0, 0, SW, SH);
  const img = named ? grayOf(crop[0]) : crop[0];
  if (img) {
    const [sx, sy, sw, sh] = coverRect(img.width, img.height, SW, SH, crop[1], crop[2], crop[3]);
    x.drawImage(img, sx, sy, sw, sh, 0, 0, SW, SH);
    if (named) { x.globalCompositeOperation = 'multiply'; x.fillStyle = rgba(mix(pal.hot, pal.glow, 0.45), 1); x.fillRect(0, 0, SW, SH); }
    x.globalCompositeOperation = 'screen'; x.fillStyle = rgba(pal.glow, 0.14); x.fillRect(0, 0, SW, SH);
  }
  if (key) baseCache.set(key, c);
  return c;
}
function renderScreen(i, m, t, tc, pal, en, glitch, p, seed) {
  const SW = i === 0 ? 512 : 384, SH = SW * 0.75;
  let c = scrPool[i]; if (!c || c.width !== SW) { c = makeCanvas(SW, SH); scrPool[i] = c; }
  const x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none';
  const crop = (p.screens && p.screens[i]) || MONITOR_SCREENS[m.scr % MONITOR_SCREENS.length];
  x.globalCompositeOperation = 'copy'; x.drawImage(screenBase(crop, pal, SW, SH), 0, 0);
  x.globalCompositeOperation = 'source-over';
  if (p.screenFn) { x.save(); p.screenFn(x, i, t, SW, SH); x.restore(); }
  // rolling bright band
  const by = fract(tc * 0.22 + i * 0.37) * (SH + 120) - 60;
  const bg = x.createLinearGradient(0, by - 50, 0, by + 50);
  bg.addColorStop(0, 'rgba(255,255,255,0)'); bg.addColorStop(0.5, rgba(pal.hot, 0.13)); bg.addColorStop(1, 'rgba(255,255,255,0)');
  x.globalCompositeOperation = 'lighter'; x.fillStyle = bg; x.fillRect(0, by - 50, SW, 100);
  x.globalCompositeOperation = 'source-over';
  // glitch
  const spike = rnd('mglitch', seed, i, bucket(t, 10)) < 0.04 + 0.12 * en ? 0.7 : 0;
  const gi = clamp(glitch + spike);
  if (gi > 0.01) {
    const r = rng('mg', seed, i, bucket(t, 20));
    const n = 2 + Math.floor(gi * 8);
    for (let k = 0; k < n; k++) {
      const yy = r() * SH, hh = 2 + r() * r() * 40, dx = (r() - 0.5) * 80 * gi;
      x.drawImage(c, 0, yy, SW, hh, dx, yy, SW, hh);
      if (r() < 0.4) { x.globalCompositeOperation = 'lighter'; x.fillStyle = r() < 0.5 ? rgba(pal.line, 0.25 * gi) : rgba(ALARM, 0.25 * gi); x.fillRect(0, yy, SW, hh); x.globalCompositeOperation = 'source-over'; }
    }
  }
  x.drawImage(scanlinePattern(), 0, 0, SW, SH);
  return c;
}
/**
 * monitors(ctx, t, {tint, energy, cam, seed, alpha, bloom, count, glitch, screens, screenFn})
 * 3–7 CRT monitors hanging on cables in a dark room, each rotated in 3D and swaying, showing a duotone image
 * crop with scanlines / rolling band / glitch slices (texture: 4–6 vertical strips, each a best-fit parallelogram
 * of its projected corners — the 'trapezoid via slices' approximation),
 * spotlights with light cones, diagonal light beams. Monitor 0 is the large hero screen.
 *   count   number of monitors (default 6, max 7)
 *   glitch  0..1 extra glitch on every screen (random spikes also happen with energy)
 *   screens [[imageName|Image|Canvas, focusX, focusY, zoom], ...] per monitor (default MONITOR_SCREENS)
 *   screenFn(sctx, index, t, w, h) hook drawn into each screen before scanlines (e.g. text / waveform)
 * Default camera: slow lateral drift (±2.0) + dolly breathing (±1.2), looking at the hero.
 */
export function monitors(ctx, t, p = {}) {
  const en = clamp(p.energy || 0), seed = p.seed == null ? 13 : p.seed;
  const tc = pathT(t, p.cam);
  const cam = resolveCam({
    pos: [Math.sin(tc * 0.16) * 2.0, 0.2 + Math.sin(tc * 0.07) * 0.5, 0.6 + Math.sin(tc * 0.11) * 1.2],
    target: [Math.sin(tc * 0.13) * 1.0, 0.45, 9], roll: 0.04 * Math.sin(tc * 0.08), fov: 52,
  }, p.cam);
  const pal = envPalette(p.tint || 0);
  const count = clamp(p.count == null ? 6 : p.count, 1, MON.length);
  const palQ = envPalette(Math.round(clamp(p.tint || 0) * 16) / 16);
  return envRun(ctx, p, { radius: 24, strength: 0.7, wide: 0.55, threshold: 0.15 }, (g, q) => {
    const FAR = 40, o = [0, 0, 0, 0];
    bgFill(g, pal.bg);
    pc(cam, 0, 0, 30, o);
    blob(q, glowSprite(pal.haze), o[0], o[1], 1200, 800, 0.75);
    // floor grid far below
    g.strokeStyle = rgba(pal.line, 1); g.lineWidth = 1; g.globalAlpha = 0.1; g.beginPath();
    for (let k = -8; k <= 8; k++) seg3(g, cam, k * 2.5, -4.5, 0, k * 2.5, -4.5, 40);
    for (let k = 0; k <= 16; k++) seg3(g, cam, -20, -4.5, k * 2.5, 20, -4.5, k * 2.5);
    g.stroke();
    // diagonal beams
    for (let i = 0; i < 6; i++) {
      const r = rng('beam', seed, i);
      const x0 = (r() - 0.5) * 22, z0 = 4 + r() * 18, x1 = x0 + (r() - 0.5) * 10, z1 = z0 + (r() - 0.5) * 8;
      const a = (0.25 + 0.2 * Math.sin(tc * 0.7 + i)) * (0.7 + 0.5 * en);
      q.strokeStyle = rgba(pal.glow, 1); q.lineWidth = 16; q.globalAlpha = a * 0.35; q.beginPath(); seg3(q, cam, x0, 12, z0, x1, -6, z1); q.stroke();
      g.strokeStyle = rgba(pal.hot, 1); g.lineWidth = 1.3; g.globalAlpha = a; g.beginPath(); seg3(g, cam, x0, 12, z0, x1, -6, z1); g.stroke();
    }
    const items = [];
    for (let i = 0; i < count; i++) {
      const m = MON[i], ph = rnd('mon', seed, i) * TAU;
      const cy = m.y + 0.08 * Math.sin(tc * 0.6 + ph);
      cs(cam, m.x, cy, m.z, _a);
      items.push({ d: _a[2], i, m, ph, cy });
    }
    const lamps = [[-2.3, 4.3, 7.2], [2.7, 4.8, 9.4], [-6.2, 3.9, 13], [6.6, 4.1, 14], [0.4, 5.2, 15]];
    for (const [lx, ly, lz] of lamps) { cs(cam, lx, ly, lz, _a); items.push({ d: _a[2], lamp: { x: lx, y: ly, z: lz, ceil: 14, r: 0.45, R: 1.7 } }); }
    items.sort((a, b) => b.d - a.d);
    for (const it of items) {
      if (it.d < cam.near + 0.3) continue;
      if (it.lamp) { drawLamp(g, q, cam, { ...it.lamp, far: FAR }, pal, 0.75 + 0.35 * en, -4.5); continue; }
      const { m, i, ph, cy } = it;
      const yaw = m.yaw + 0.14 * Math.sin(tc * 0.45 + ph), pitch = m.pitch + 0.06 * Math.sin(tc * 0.37 + ph), rl = m.roll + 0.05 * Math.sin(tc * 0.41 + ph);
      const w = m.w, h = w * 0.75, dep = h * 0.75;
      const W3 = (lx, ly, lz) => { const q = rotE(lx, ly, lz, pitch, yaw, rl); return [m.x + q[0], cy + q[1], m.z + q[2]]; };
      const vis = fog(it.d, FAR, 0, 0.8);
      // cables
      g.strokeStyle = rgba(pal.line, 1); g.lineWidth = 1.2; g.globalAlpha = 0.6 * vis; g.beginPath();
      for (const s of [-1, 1]) { const a = W3(s * w * 0.38, h * 0.56, 0.3); seg3(g, cam, a[0], a[1], a[2], a[0] + s * 0.25, 16, a[2] + 0.3); }
      g.stroke();
      // housing box
      const BX = [];
      for (let k = 0; k < 8; k++) {
        const back = k & 4, sx = k & 1 ? 1 : -1, sy = k & 2 ? 1 : -1;
        const q = back ? W3(sx * w * 0.36, sy * h * 0.35, dep) : W3(sx * w * 0.55, sy * h * 0.56, 0.02);
        const pq = [0, 0, 0, 0]; if (!pc(cam, q[0], q[1], q[2], pq)) { BX.length = 0; break; } BX.push(pq);
      }
      if (BX.length < 8) continue;
      const hp = hull(BX.map((q) => [q[0], q[1]]));
      g.globalAlpha = 0.97; g.fillStyle = rgba(mix(pal.bg, pal.line, 0.07), 1);
      g.beginPath(); g.moveTo(hp[0][0], hp[0][1]); for (let k = 1; k < hp.length; k++) g.lineTo(hp[k][0], hp[k][1]); g.closePath(); g.fill();
      g.globalAlpha = 0.35 * vis; g.lineWidth = 1; g.beginPath();
      for (const [a, b] of BOX_E) { g.moveTo(BX[a][0], BX[a][1]); g.lineTo(BX[b][0], BX[b][1]); }
      g.stroke();
      // facing?
      const nrm = rotE(0, 0, -1, pitch, yaw, rl), ctr = [m.x, cy, m.z];
      const facing = nrm[0] * (cam.px - ctr[0]) + nrm[1] * (cam.py - ctr[1]) + nrm[2] * (cam.pz - ctr[2]) > 0;
      if (facing) {
        const scr = renderScreen(i, m, t, tc, palQ, en, p.glitch || 0, p, seed);
        // texture: NS vertical strips, each drawn as the best-fit parallelogram of its projected corners
        // (no clipping → cheap; perspective error is sub-pixel at these sizes)
        const NS = i === 0 ? 6 : 4, SW = scr.width, SH = scr.height;
        const top = [], bot = [];
        for (let k = 0; k <= NS; k++) {
          const u = k / NS, qa = [0, 0, 0, 0], qb = [0, 0, 0, 0];
          const A3 = W3(-w / 2 + u * w, h / 2, -0.01), B3 = W3(-w / 2 + u * w, -h / 2, -0.01);
          pc(cam, A3[0], A3[1], A3[2], qa); pc(cam, B3[0], B3[1], B3[2], qb);
          top.push([qa[0], qa[1]]); bot.push([qb[0], qb[1]]);
        }
        const flick = 0.92 + 0.08 * rnd('mf', seed, i, bucket(t, 15));
        g.globalAlpha = vis * flick;
        const base = g.getTransform();
        for (let k = 0; k < NS; k++) {
          const tl = top[k], tr = top[k + 1], bl = bot[k], br = bot[k + 1];
          const sw = SW / NS, sx0 = k * sw;
          const ax = (tr[0] - tl[0] + br[0] - bl[0]) / 2 / sw, ay = (tr[1] - tl[1] + br[1] - bl[1]) / 2 / sw;
          const cx = (bl[0] - tl[0] + br[0] - tr[0]) / 2 / SH, cy = (bl[1] - tl[1] + br[1] - tr[1]) / 2 / SH;
          const mx = (tl[0] + tr[0] + bl[0] + br[0]) / 4, my = (tl[1] + tr[1] + bl[1] + br[1]) / 4;
          const ov = k < NS - 1 ? 1.5 : 0; // overlap into the next strip hides seams
          g.transform(ax, ay, cx, cy, mx - ax * (sw / 2) - cx * (SH / 2), my - ay * (sw / 2) - cy * (SH / 2));
          g.drawImage(scr, sx0, 0, sw + ov, SH, 0, 0, sw + ov, SH);
          g.setTransform(base);
        }
        const G = [top[0], top[NS], bot[NS], bot[0]];
        const [c0, c1, c2, c3] = G;
        q.globalAlpha = 0.35 * vis * (1 + en); q.fillStyle = rgba(pal.glow, 1);
        q.beginPath(); q.moveTo(c0[0], c0[1]); q.lineTo(c1[0], c1[1]); q.lineTo(c2[0], c2[1]); q.lineTo(c3[0], c3[1]); q.closePath(); q.fill();
        g.beginPath(); g.moveTo(c0[0], c0[1]); g.lineTo(c1[0], c1[1]); g.lineTo(c2[0], c2[1]); g.lineTo(c3[0], c3[1]); g.closePath();
        g.strokeStyle = rgba(pal.hot, 1); g.globalAlpha = 0.6 * vis; g.lineWidth = 1.4; g.stroke();
      }
      g.strokeStyle = rgba(pal.line, 1); g.globalAlpha = 0.85 * vis; g.lineWidth = 1.6; g.beginPath();
      g.moveTo(BX[0][0], BX[0][1]); g.lineTo(BX[1][0], BX[1][1]); g.lineTo(BX[3][0], BX[3][1]); g.lineTo(BX[2][0], BX[2][1]); g.closePath(); g.stroke();
      // tiny label LED
      const led = W3(w * 0.47, -h * 0.53, -0.02), lq = [0, 0, 0, 0];
      if (pc(cam, led[0], led[1], led[2], lq) && Math.sin(tc * 3 + i) > -0.3) { g.globalAlpha = vis; g.fillStyle = rgba(i === 0 ? ALARM : pal.hot, 1); g.fillRect(lq[0] - 2, lq[1] - 2, 4, 4); }
    }
    dust(g, cam, t, pal, 80, seed, { w: 16, y0: -4, h: 9, depth: 20 });
    return { cam };
  });
}

/* ================================================================ cockpitFrame */
const pad2 = (n) => String(Math.floor(n)).padStart(2, '0');
/**
 * cockpitFrame(ctx, t, {style:'cold'|'warm', intensity=1, draw=1, labels, accent})
 * persistent HUD frame drawn straight onto ctx (no bloom): side rails + ")" arcs, half rings with rotating ticks
 * at mid-height, corner target circles with rotating ticks, edge rules with sliding dashes, 8 tiny mono labels.
 *   draw     0..1 build-in progress (section boundaries: the frame re-draws itself)
 *   labels   { tl, tr, top, l, r, bl, br, bottom } overrides (strings)
 */
export function cockpitFrame(ctx, t, p = {}) {
  const I = p.intensity == null ? 1 : clamp(p.intensity, 0, 2), D = clamp(p.draw == null ? 1 : p.draw);
  if (I <= 0.001 || D <= 0.001) return;
  const warm = p.style === 'warm';
  const c1 = warm ? P.gold : P.steel, c2 = warm ? P.paper : P.ice, acc = p.accent || (warm ? P.orange : P.cyan);
  const A0 = 0.68 * I;
  const k = (i) => clamp((D - i * 0.07) / 0.45); // staggered element progress
  const g = ctx;
  g.save();
  g.lineCap = 'butt'; g.lineJoin = 'miter'; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  const poly = (pts, prog) => { // partial polyline by arc length
    if (prog <= 0) return;
    let total = 0; for (let i = 1; i < pts.length; i++) total += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    let left = total * prog;
    g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length && left > 0; i++) {
      const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]), q = Math.min(1, left / l);
      g.lineTo(lerp(pts[i - 1][0], pts[i][0], q), lerp(pts[i - 1][1], pts[i][1], q)); left -= l;
    }
  };
  const stroke2 = (col, a, lw) => { // soft underlay + crisp line
    g.strokeStyle = rgba(col, 1); g.globalAlpha = a * 0.22; g.lineWidth = lw + 3; g.stroke();
    g.globalAlpha = a; g.lineWidth = lw; g.stroke();
  };
  const breathe = Math.sin(t * 0.8) * 4;
  const side = () => {
    // outer rail with chamfers
    g.beginPath(); poly([[70, 92], [40, 124], [40, 470]], k(0)); poly([[40, 610], [40, 956], [70, 988]], k(0)); stroke2(c1, A0, 1.3);
    // ")" arc, gap in the middle
    const R = 720 + breathe, cx = 140 - R;
    g.beginPath(); g.arc(cx, 540, R, -0.52 * k(1), -0.17 * k(1) ** 0.5); g.moveTo(cx + R * Math.cos(0.17), 540 + R * Math.sin(0.17)); g.arc(cx, 540, R, 0.17, 0.17 + 0.35 * k(1)); stroke2(c1, A0 * 0.8, 1.1);
    // mid half ring with rotating ticks
    if (k(2) > 0) {
      ring(g, 0, 540, { r: 150, color: rgba(c2, 1), alpha: A0 * 0.9 * k(2), lw: 1.3, ticks: 72, tickLen: 6, major: 6, majorLen: 14, rot: t * 0.2, arcs: [[-Math.PI / 2 * k(2), Math.PI / 2 * k(2)]] });
      ring(g, 0, 540, { r: 118, color: rgba(c1, 1), alpha: A0 * 0.7 * k(2), lw: 1, dash: [3, 6], rot: -t * 0.35 });
      ring(g, 0, 540, { r: 84, color: rgba(c1, 1), alpha: A0 * 0.8 * k(2), lw: 1.4, arcs: [[-1.2, -0.25], [0.25, 1.2]], rot: Math.sin(t * 0.5) * 0.3 });
      g.beginPath(); g.moveTo(160, 540); g.lineTo(160 + 40 * k(2), 540); stroke2(c2, A0, 1.2);
      g.globalAlpha = A0; g.fillStyle = rgba(acc, 1); g.fillRect(208, 538, 4 * k(2), 4);
    }
    // inner dashed guides (sliding)
    g.setLineDash([6, 8]); g.lineDashOffset = -t * 14;
    g.beginPath(); poly([[88, 300], [88, 430]], k(3)); poly([[88, 650], [88, 780]], k(3)); stroke2(c1, A0 * 0.6, 1);
    g.setLineDash([]); g.lineDashOffset = 0;
    // tick ladders on the rail
    if (k(3) > 0) {
      g.beginPath();
      for (let i = 0, y = 140; y < 140 + 300 * k(3); i++, y += 12) { const l = i % 5 === 0 ? 12 : 6; g.moveTo(40, y); g.lineTo(40 + l, y); }
      for (let i = 0, y = 640; y < 640 + 300 * k(3); i++, y += 12) { const l = i % 5 === 0 ? 12 : 6; g.moveTo(40, y); g.lineTo(40 + l, y); }
      stroke2(c1, A0 * 0.5, 1);
    }
    // little chevrons riding up/down the inner guide
    if (k(4) > 0) {
      const yy = 360 + Math.sin(t * 0.6) * 60;
      g.beginPath(); g.moveTo(96, yy - 6); g.lineTo(104, yy); g.lineTo(96, yy + 6); g.moveTo(96, 1080 - yy - 6); g.lineTo(104, 1080 - yy); g.lineTo(96, 1080 - yy + 6);
      stroke2(c2, A0 * 0.8 * k(4), 1.2);
    }
    // top corner bracket + little ring + diagonal
    g.beginPath(); poly([[40, 76], [40, 40], [170, 40], [206, 76], [560, 76]], k(1)); stroke2(c1, A0, 1.2);
    ring(g, 66, 66, { r: 7, color: rgba(c2, 1), alpha: A0 * k(2), lw: 1 });
    g.beginPath(); poly([[206, 76], [252, 122], [330, 122]], k(3)); stroke2(c1, A0 * 0.55, 1);
    for (let i = 0; i < 3; i++) ring(g, 360 + i * 22, 122, { r: 5, color: rgba(c2, 1), alpha: A0 * 0.7 * k(4) * (i === Math.floor(t * 1.5) % 3 ? 1 : 0.4), lw: 1 });
    // top rule with step + blinking squares
    g.beginPath(); poly([[600, 40], [790, 40], [812, 58], [880, 58]], k(2)); stroke2(c1, A0 * 0.8, 1);
    for (let i = 0; i < 4; i++) { g.globalAlpha = A0 * k(3) * (Math.sin(t * 2.4 - i * 0.9) > 0 ? 0.9 : 0.25); g.fillStyle = rgba(c2, 1); g.fillRect(612 + i * 12, 48, 6, 6); }
    // bottom corner target
    const tx = 128, ty = 952, kk = k(2);
    if (kk > 0) {
      ring(g, tx, ty, { r: 20, color: rgba(c2, 1), alpha: A0 * kk, lw: 2 });
      ring(g, tx, ty, { r: 31, color: rgba(c1, 1), alpha: A0 * 0.8 * kk, lw: 1, ticks: 16, tickLen: 5, rot: t * 0.6, arcs: [[0, TAU * kk]] });
      ring(g, tx, ty, { r: 40, color: rgba(c1, 1), alpha: A0 * 0.6 * kk, lw: 1, arcs: [[0, 1.3], [2.1, 3.4]], rot: -t * 0.3 });
      g.globalAlpha = A0 * kk; g.fillStyle = rgba(acc, 1); g.beginPath(); g.arc(tx, ty, 6, 0, TAU); g.fill();
    }
    // bottom rule + sliding dot row
    g.beginPath(); poly([[40, 1004], [70, 1040], [520, 1040], [540, 1024], [640, 1024]], k(3)); stroke2(c1, A0 * 0.8, 1.1);
    g.beginPath(); poly([[190, 1004], [470, 1004]], k(4)); stroke2(c1, A0 * 0.4, 1);
    g.setLineDash([2, 5]); g.lineDashOffset = t * 10; g.beginPath(); poly([[660, 1024], [820, 1024]], k(4)); stroke2(c2, A0 * 0.6, 1); g.setLineDash([]);
    g.fillStyle = rgba(c2, 1);
    for (let i = 0; i < 9; i++) { const xx = 220 + ((i * 16 + t * 20) % 144); g.globalAlpha = A0 * 0.7 * k(4) * (1 - Math.abs(xx - 292) / 80); g.fillRect(xx, 1018, 3, 3); }
  };
  const base = g.getTransform();
  side();
  g.setTransform(base); g.translate(W, 0); g.scale(-1, 1); side();
  g.setTransform(base);
  // top / bottom centre marks
  g.beginPath(); poly([[900, 40], [1020, 40]], k(4)); stroke2(c1, A0 * 0.7, 1);
  g.beginPath(); poly([[880, 1040], [1040, 1040]], k(4)); stroke2(c1, A0 * 0.7, 1);
  // labels (typed in with draw progress)
  const L = p.labels || {};
  const az = (132.4 + t * 3.7) % 360, el = 12.5 + Math.sin(t * 0.3) * 6;
  const tcStr = `${pad2(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;
  const lab = [
    [L.tl || 'VOICE.SYNTH // CLAUDE', 96, 64, 'left'],
    [L.tr || 'CH-01 · 48.0KHZ · 24BIT', W - 96, 64, 'right'],
    [L.top || '[ CLAUDE ]', W / 2, 30, 'center'],
    [L.l || `AZ ${az.toFixed(1)}`, 196, 528, 'left'],
    [L.r || `EL ${el.toFixed(1)}`, W - 196, 528, 'right'],
    [L.bl || 'MODEL: CLAUDE', 176, 958, 'left'],
    [L.br || `T+${tcStr}`, W - 176, 958, 'right'],
    [L.bottom || (warm ? 'TEMP 0.98 · FEELING: ???' : 'TEMP 0.00 · FEELING: NULL'), W / 2, 1066, 'center'],
  ];
  lab.forEach(([s, x, y, align], i) => {
    const kk = k(2 + i * 0.5); if (kk <= 0) return;
    const str = kk >= 1 ? s : s.slice(0, Math.ceil(s.length * kk));
    label(g, str, x, y, { size: 14, align, color: rgba(i === 2 ? acc : c2, 1), alpha: A0 * (i === 2 ? 1 : 0.85) });
  });
  // REC dot
  if (k(5) > 0 && Math.sin(t * 3.1) > -0.2) { g.globalAlpha = A0; g.fillStyle = rgba(ALARM, 1); g.beginPath(); g.arc(W - 96 - 300, 59, 4, 0, TAU); g.fill(); }
  g.restore();
}
