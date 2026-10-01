// charfx.js — character animation layer for the 機械の声 × Claude MV (STORYBOARD_V2 §2.2).
//
// Everything is a pure function of t (+ opts): randomness only via fx.js's seeded mulberry32 (rng/rnd/noise1),
// no Math.random, no frame-to-frame state. Expensive intermediates (scaled source, blurred silhouettes, bloom
// bright-pass, scanline masks) are cached per (image, quantised height) in offscreen canvases; per-frame work is
// drawImage / fillRect only (no per-pixel JS loops after the one-off cache build).
//
// Exports
//   drawCharacter(ctx, t, opts)                 -> {x0,y0,x1,y1, scale}   (bbox in the ctx's current user space)
//   drawVoiceCrowd(ctx, t, {silhouette, positions:[{x,y,h,depth,alpha?}], color, blur, alpha, glow, seed})
//   drawMonitorFace(ctx, quad:[p0,p1,p2,p3], image, srcRect, {scanlines, glitch, t, seed, tint, alpha, bg, glow})
//   cameraShot(t, {from, to, t0, t1, ease, drift, seed}) | cameraShot(k, from, to, ease)  -> {scale,x,y,rotate,cx,cy}
//   applyCamera(ctx, cam)
//   prepareCharacter(opts)  (cache warm-up), rimColour(tint), CHAR (layout constants), clearCharCache()
import * as fx from './fx.js';

const { W, H, P, clamp, lerp, smooth, TAU, ease, rng, rnd, noise1, bucket, ramp, rgba, makeCanvas } = fx;

/* ------------------------------------------------------------------ constants */
// Fractions of the full-body image height (char_full*.png, char_mono.png share one layout).
export const CHAR = {
  shoulder: 0.22,   // everything above this line (head, face, top of hair) is drawn rigidly: the face never wobbles
  faceY: 0.10,      // face centre
  hairTips: 0.58,   // lowest hair strands
  hem: 0.90,        // skirt hem
};
// Hair/skirt sway envelope: [fraction of height, amplitude px @ h=1000]. Grows from 0 at the shoulder to 6 px where
// the hair tips and the skirt flare are, then tapers so the shoes stay planted on the anchor.
const SWAY_KNOTS = [
  [CHAR.shoulder, 0], [0.34, 2.0], [0.47, 4.6], [0.60, 6.0],
  [0.73, 5.0], [0.86, 3.0], [1.0, 0.5],
];
const COL_W = 24;             // strip width in px @ h=1000
const MARGIN = 28;            // transparent margin around the cached source (px @ h=1000) so sway/split never clip
const MAX_ENTRIES = 6;          // each entry holds ~10–25 MB of work canvases at h≈1000

/* ------------------------------------------------------------------ small helpers */
function wctx(c) {
  const x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0);
  x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none';
  x.imageSmoothingEnabled = true;
  return x;
}
function colStr(c, a = 1) { return typeof c === 'string' && c[0] !== '#' ? c : rgba(c, a); }
const toRGB = (c) => (Array.isArray(c) ? c : fx.hex2rgb(c));
/** default rim colour for tint 0 (cold) → 1 (warm) */
export function rimColour(tint) {
  return ramp([[0, P.cyan], [0.45, P.ice], [0.7, P.orangeL], [1, P.orange]], clamp(tint));
}
function sized(c, w, h) {
  if (!c) return makeCanvas(w, h);
  if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  return c;
}

/* ------------------------------------------------------------------ cache */
// image -> Map(hc -> entry). Height is quantised to 1/12 octave so an animated h (dolly) re-uses entries.
const CACHE = new Map();
let LRU = [];
export function clearCharCache() { CACHE.clear(); LRU = []; CROWD.clear(); }

function quantH(h, ih) {
  const q = Math.pow(2, Math.ceil(Math.log2(Math.max(16, h)) * 12 - 1e-9) / 12);
  return Math.max(16, Math.min(Math.round(q), ih));
}
function imgH(img) { return img.naturalHeight || img.height; }
function imgW(img) { return img.naturalWidth || img.width; }

function getEntry(img, h) {
  const ih = imgH(img), iw = imgW(img);
  const hc = quantH(h, ih);
  let m = CACHE.get(img);
  if (!m) { m = new Map(); CACHE.set(img, m); }
  let e = m.get(hc);
  if (!e) {
    const k = hc / 1000;
    const wc = Math.round(iw * hc / ih);
    const M = Math.ceil(MARGIN * Math.max(k, 0.5));
    const cw = wc + 2 * M, ch = hc + 2 * M;
    const src = makeCanvas(cw, ch), x = wctx(src);
    x.imageSmoothingQuality = 'high';
    // two-step downscale for large ratios keeps hair lines crisp but not aliased
    if (ih / hc > 2.2) {
      const mid = makeCanvas(Math.round(iw * 2 * hc / ih), hc * 2), mx = wctx(mid);
      mx.imageSmoothingQuality = 'high'; mx.drawImage(img, 0, 0, mid.width, mid.height);
      x.drawImage(mid, M, M, wc, hc);
    } else x.drawImage(img, M, M, wc, hc);
    e = { img, hc, wc, M, cw, ch, k, src, work: {}, lay: {} };
    m.set(hc, e);
    LRU.push(e);
    if (LRU.length > MAX_ENTRIES) {
      const old = LRU.shift();
      const mm = CACHE.get(old.img); if (mm) { mm.delete(old.hc); if (!mm.size) CACHE.delete(old.img); }
    }
  } else { LRU.splice(LRU.indexOf(e), 1); LRU.push(e); }
  return e;
}
function work(e, name, ds = 1) {
  const w = Math.ceil(e.cw / ds), h = Math.ceil(e.ch / ds);
  return (e.work[name] = sized(e.work[name], w, h));
}

/** rim halo: white silhouette blurred at two radii (tight 7 px + wide 30 px @ h=1000), summed, stored at 1/3 res.
 *  Coloured copies are cached per quantised colour, so a static or slowly ramping rim colour costs one drawImage. */
function haloLayer(e) {
  let L = e.lay.halo;
  if (!L) {
    const ds = 3, rT = 7 * e.k / ds, rW = 26 * e.k / ds;
    const pad = Math.ceil(rW * 2.0) + 2;
    const w = Math.ceil(e.cw / ds), h = Math.ceil(e.ch / ds);
    const sil = makeCanvas(w, h), sx = wctx(sil);
    sx.drawImage(e.src, 0, 0, w, h);
    sx.globalCompositeOperation = 'source-in'; sx.fillStyle = '#fff'; sx.fillRect(0, 0, w, h);
    const c = makeCanvas(w + 2 * pad, h + 2 * pad), x = wctx(c);
    x.globalCompositeOperation = 'lighter';
    x.filter = `blur(${rW.toFixed(2)}px)`; x.globalAlpha = 0.62; x.drawImage(sil, pad, pad);
    x.filter = `blur(${rT.toFixed(2)}px)`; x.globalAlpha = 0.48; x.drawImage(sil, pad, pad);
    x.filter = 'none';
    L = e.lay.halo = { c, ds, ox: -pad * ds, oy: -pad * ds, col: new Map() };
  }
  return L;
}
function haloColoured(L, rgb) {
  const key = rgb.map((v) => Math.round(v / 6)).join(',');
  let c = L.col.get(key);
  if (!c) {
    c = colourInto(makeCanvas(L.c.width, L.c.height), L.c, rgb, 'in');
    if (L.col.size >= 6) L.col.delete(L.col.keys().next().value);
    L.col.set(key, c);
  }
  return c;
}

/** bloom: bright-pass (one-off pixel loop at 1/4 res) + two blur radii, additive-ready */
function bloomLayer(e) {
  if (e.lay.bloom) return e.lay.bloom;
  const ds = 4, w = Math.ceil(e.cw / ds), h = Math.ceil(e.ch / ds);
  const bp = document.createElement('canvas'); bp.width = w; bp.height = h;
  const bx = bp.getContext('2d', { willReadFrequently: true });
  bx.imageSmoothingQuality = 'high';
  bx.drawImage(e.src, 0, 0, w, h);
  const id = bx.getImageData(0, 0, w, h), d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    const a = d[i + 3] / 255;
    if (a <= 0) continue;
    const r = d[i], g = d[i + 1], b = d[i + 2];
    const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    // warm highlights (gold trim, lit hair) count a bit more than neutral cream so the dress does not dominate
    const warm = clamp((r - b) / 120) * 0.08;
    let k = (lum + warm - 0.86) / 0.16; k = clamp(k); k = k * k * (3 - 2 * k);
    d[i + 3] = Math.round(255 * k * a);
  }
  bx.putImageData(id, 0, 0);
  const r1 = 6 * e.k / ds, r2 = 22 * e.k / ds;
  const pad = Math.ceil(r2 * 2.4) + 2;
  const c = makeCanvas(w + 2 * pad, h + 2 * pad), x = wctx(c);
  x.filter = `blur(${r1.toFixed(2)}px)`; x.drawImage(bp, pad, pad);
  x.globalCompositeOperation = 'lighter';
  x.filter = `blur(${r2.toFixed(2)}px)`; x.globalAlpha = 0.85; x.drawImage(bp, pad, pad);
  x.filter = 'none';
  return (e.lay.bloom = { c, ds, ox: -pad * ds, oy: -pad * ds });
}

/** cached horizontal scanline mask (opaque rows every `period` px) */
const SCAN = new Map();
function scanMask(w, h, period, thick) {
  const key = `${w}x${h}/${period}/${thick}`;
  let c = SCAN.get(key);
  if (!c) {
    c = makeCanvas(w, h + period); const x = wctx(c);
    x.fillStyle = '#000';
    for (let y = 0; y < h + period; y += period) x.fillRect(0, y, w, thick);
    if (SCAN.size > 16) SCAN.clear();
    SCAN.set(key, c);
  }
  return c;
}

/* ------------------------------------------------------------------ per-frame passes (all in cache space) */
/** hair/skirt sway: 24 px column strips below the shoulder line, each split at the knot rows into sheared
 *  segments so the displacement is continuous down a column (no horizontal seams); each column is clipped to its
 *  own integer-aligned destination band so neighbours never overlap or leave gaps (no vertical seams). */
function swayPass(e, src, dst, t, amp, seed) {
  const x = wctx(dst);
  x.clearRect(0, 0, e.cw, e.ch);
  const ys = e.M + Math.round(CHAR.shoulder * e.hc);
  x.drawImage(src, 0, 0, e.cw, ys, 0, 0, e.cw, ys);           // rigid head/face/shoulders
  const colW = Math.max(6, Math.round(COL_W * e.k));
  const nCol = Math.ceil(e.cw / colW);
  const knotsY = SWAY_KNOTS.map(([f]) => e.M + Math.round(f * e.hc));
  knotsY[knotsY.length - 1] = e.ch;                            // last segment runs through the bottom margin
  const nK = knotsY.length;
  const w1 = TAU / 3.6, w2 = TAU / 2.3;
  const sp = rnd(seed, 'sway-phase') * TAU;
  const D = new Float32Array(nK);
  const occ = occupancy(e, colW, knotsY, ys, nCol);
  for (let c = 0; c < nCol; c++) {
    if (!occ[c * nK + nK - 1]) continue;                        // column empty below the shoulder (+ pad)
    const X0 = c * colW, X1 = Math.min(e.cw, X0 + colW);
    const xf = ((X0 + X1) / 2 - e.M) / e.wc;                    // 0..1 across the figure
    const side = smooth(0.08, 0.30, Math.abs(xf - 0.5));        // torso/book move less than the outer hair
    const wgt = 0.28 + 0.72 * side;
    // per-column phase: smooth seeded noise of the column's x-fraction (so it is independent of the cache grid;
    // neighbours stay within ~0.3 rad -> < 2 px kinks at strip boundaries)
    const ph = xf * 3.6 + 1.4 * noise1(seed + ':swc', xf * 5) + sp;
    let maxd = 0;
    for (let j = 0; j < nK; j++) {
      const a = SWAY_KNOTS[j][1] * e.k * amp * wgt;
      const psi = -j * 0.5;                                     // lower knots lag: the wave travels downwards
      const v = 0.72 * Math.sin(w1 * t + ph + psi) + 0.28 * Math.sin(w2 * t + 1.7 * ph + 1.3 * psi + 2.1);
      D[j] = a * v; maxd = Math.max(maxd, Math.abs(D[j]));
    }
    const pad = Math.ceil(maxd) + 2;
    x.save();
    x.beginPath(); x.rect(X0, ys, X1 - X0, e.ch - ys); x.clip();
    for (let j = 0; j < nK - 1; j++) {
      const y0 = j === 0 ? ys : knotsY[j], y1 = knotsY[j + 1];
      if (y1 <= y0 || !occ[c * nK + j]) continue;
      const d0 = j === 0 ? 0 : D[j], d1 = D[j + 1];
      const sh = (d1 - d0) / (y1 - y0);
      x.setTransform(1, 0, sh, 1, d0 - sh * y0, 0);
      const sx = Math.max(0, X0 - pad), sw = Math.min(e.cw, X1 + pad) - sx;
      x.drawImage(src, sx, y0, sw, y1 - y0, sx, y0, sw, y1 - y0);
    }
    x.restore();
  }
}

/** one-off (per cache entry) alpha occupancy of each strip segment, widened by 10 px so content that sways into a
 *  strip from its neighbour is never skipped. occ[c*nK + j] = segment j of column c has content; [c*nK + nK-1] = any. */
function occupancy(e, colW, knotsY, ys, nCol) {
  if (e.occ && e.occ.colW === colW) return e.occ.a;
  const nK = knotsY.length, a = new Uint8Array(nCol * nK);
  const cv = document.createElement('canvas'); cv.width = e.cw; cv.height = e.ch;
  const x = cv.getContext('2d', { willReadFrequently: true });
  x.drawImage(e.src, 0, 0);
  const d = x.getImageData(0, 0, e.cw, e.ch).data, padX = Math.ceil(10 * e.k);
  for (let c = 0; c < nCol; c++) {
    const X0 = Math.max(0, c * colW - padX), X1 = Math.min(e.cw, (c + 1) * colW + padX);
    for (let j = 0; j < nK - 1; j++) {
      const y0 = j === 0 ? ys : knotsY[j], y1 = knotsY[j + 1];
      let hit = 0;
      for (let y = y0; y < y1 && !hit; y++) for (let xx = X0; xx < X1; xx++) if (d[(y * e.cw + xx) * 4 + 3] > 3) { hit = 1; break; }
      a[c * nK + j] = hit; if (hit) a[c * nK + nK - 1] = 1;
    }
  }
  e.occ = { colW, a };
  return a;
}

/** per-row horizontal alpha extent of the cached source (one-off), used to band additive layers */
function rowExtents(e) {
  if (e.rows) return e.rows;
  const cv = document.createElement('canvas'); cv.width = e.cw; cv.height = e.ch;
  const x = cv.getContext('2d', { willReadFrequently: true });
  x.drawImage(e.src, 0, 0);
  const d = x.getImageData(0, 0, e.cw, e.ch).data;
  const lo = new Int32Array(e.ch).fill(-1), hi = new Int32Array(e.ch).fill(-1);
  for (let y = 0; y < e.ch; y++) {
    const o = y * e.cw * 4;
    let a = -1, b = -1;
    for (let xx = 0; xx < e.cw; xx++) if (d[o + xx * 4 + 3] > 3) { if (a < 0) a = xx; b = xx; }
    lo[y] = a; hi[y] = b;
  }
  return (e.rows = { lo, hi, bands: new Map() });
}
/** horizontal bands [y0,y1,x0,x1] (cache px) covering the figure grown by `reachX` sideways / `reachY` vertically */
function bandsFor(e, reachX, reachY) {
  const R = rowExtents(e), key = `${Math.round(reachX)}/${Math.round(reachY)}`;
  let B = R.bands.get(key);
  if (B) return B;
  const NB = 10, y0 = -Math.ceil(reachY), y1 = e.ch + Math.ceil(reachY), bh = Math.ceil((y1 - y0) / NB);
  B = [];
  for (let b = 0; b < NB; b++) {
    const a0 = y0 + b * bh, a1 = Math.min(y1, a0 + bh);
    let x0 = 1e9, x1 = -1e9;
    for (let y = Math.max(0, Math.floor(a0 - reachY)); y < Math.min(e.ch, Math.ceil(a1 + reachY)); y++) {
      if (R.lo[y] >= 0) { x0 = Math.min(x0, R.lo[y]); x1 = Math.max(x1, R.hi[y] + 1); }
    }
    if (x1 > x0) B.push([a0, a1, Math.floor(x0 - reachX), Math.ceil(x1 + reachX)]);
  }
  R.bands.set(key, B);
  return B;
}
/** additive draw of a layer canvas placed at cache-space (ox,oy) with scale sc, restricted to the bands */
function drawBanded(ctx, c, ox, oy, sc, bands) {
  const W2 = c.width * sc, H2 = c.height * sc;
  for (const [a0, a1, b0, b1] of bands) {
    const y0 = Math.max(a0, oy), y1 = Math.min(a1, oy + H2), x0 = Math.max(b0, ox), x1 = Math.min(b1, ox + W2);
    if (y1 <= y0 || x1 <= x0) continue;
    ctx.drawImage(c, (x0 - ox) / sc, (y0 - oy) / sc, (x1 - x0) / sc, (y1 - y0) / sc, x0, y0, x1 - x0, y1 - y0);
  }
}

/** cold grade: lerp toward deep steel inside the figure (tint 0 → ~17 %) */
function gradePass(dst, cw, ch, tint) {
  const a = 0.17 * (1 - clamp(tint));
  if (a < 0.004) return;
  const x = wctx(dst);
  x.globalCompositeOperation = 'source-atop';
  x.fillStyle = rgba('#40596A', a); x.fillRect(0, 0, cw, ch);
}

/** hologram: built on an OPAQUE BLACK canvas so channel isolation needs only cheap bounded ops
 *  (fill black → 'lighter' frame → 'multiply' channel colour), integer-pixel offsets (no resampling), and the result
 *  is drawn additively ('lighter') — a projected, light-emitting figure. RGB split 2 screen px, tint wash,
 *  rolling scanlines, a sweep bar. Returns the opaque canvas. */
function holoPass(e, frame, t, amt, s, col, seed) {
  const R = work(e, 'hR'), O = work(e, 'hO'), FB = work(e, 'hFB');
  const cw = e.cw, ch = e.ch;
  const fb = wctx(FB);                                          // frame composited over opaque black, shared
  fb.globalCompositeOperation = 'copy'; fb.fillStyle = '#000'; fb.fillRect(0, 0, cw, ch);
  fb.globalCompositeOperation = 'lighter'; fb.drawImage(frame, 0, 0);
  const split = Math.max(1, Math.round((2 / s) * amt));
  const jit = rnd(seed, 'hsplit', bucket(t, 12)) < 0.25 ? Math.round(split * 0.8) : 0;
  const chan = (c, dx, fill) => {
    const x = wctx(c);
    x.globalCompositeOperation = 'copy'; x.drawImage(FB, dx, 0);   // the uncovered strip is transparent = black for 'lighter'
    x.globalCompositeOperation = 'multiply'; x.fillStyle = fill; x.fillRect(0, 0, cw, ch);
    // multiply paints the fill colour into the transparent strip the offset uncovered: clear it again
    x.globalCompositeOperation = 'source-over';
    if (dx > 0) x.clearRect(0, 0, Math.ceil(dx), ch); else if (dx < 0) x.clearRect(cw + Math.floor(dx), 0, -Math.floor(dx), ch);
    return x;
  };
  // the tint wash is folded into the channel masks: R ← (w_r,0,0), GB ← (0,w_g,w_b)
  const wash = mix3([255, 255, 255], col, 0.45 * amt);
  chan(R, -split - jit, rgba([wash[0], 0, 0]));
  const x = chan(O, split + jit, rgba([0, wash[1], wash[2]]));
  x.globalCompositeOperation = 'lighter'; x.drawImage(R, 0, 0);
  // sweep bar: re-add the figure itself inside a band travelling down every 2.6 s
  const ph = ((t / 2.6) % 1 + 1) % 1, bh = Math.round(60 * e.k);
  const by = Math.round(e.M + ph * (e.hc + 2 * bh) - bh);
  const y0 = Math.max(0, by), y1 = Math.min(ch, by + bh);
  if (y1 > y0) {
    x.globalCompositeOperation = 'lighter'; x.globalAlpha = 0.28 * amt;
    x.drawImage(frame, 0, y0, cw, y1 - y0, 0, y0, cw, y1 - y0);
    x.globalAlpha = 1;
  }
  // scanlines (3 screen px period, 1 px dark), slowly rolling
  const period = Math.max(2, Math.round(3 / s)), thick = Math.max(1, Math.round(1 / s));
  const sm = scanMask(cw, ch, period, thick);
  x.globalCompositeOperation = 'source-over'; x.globalAlpha = 0.55 * amt;
  x.drawImage(sm, 0, -(Math.floor(t * 18) % period));
  return O;
}

/** slice glitch: seeded horizontal bands displaced; event probability rises with amount */
function glitchPass(e, frame, t, amt, s, seed, name = 'gl') {
  const b = bucket(t, 15);
  const r = rng(seed, 'cglitch', b);
  // events come in short bursts: the burst gate changes every 1/5 s, bands re-roll every 1/15 s
  const gate = rnd(seed, 'cgate', bucket(t, 5));
  if (gate > 0.15 + 0.75 * amt) return frame;
  const O = work(e, name), x = wctx(O);
  x.globalCompositeOperation = 'copy'; x.drawImage(frame, 0, 0); x.globalCompositeOperation = 'source-over';
  const n = 1 + Math.floor(r() * (2 + 5 * amt));
  const opaque = name === 'glH';
  for (let i = 0; i < n; i++) {
    const hb = Math.max(2, Math.round((3 + r() * r() * 70) * e.k));
    const y = Math.round(e.M + r() * (e.hc - hb));
    const dx = Math.round((r() < 0.5 ? -1 : 1) * (6 + r() * 46 * amt) * e.k / Math.max(0.5, s));
    x.clearRect(0, y, e.cw, hb);
    if (opaque) { x.fillStyle = '#000'; x.fillRect(0, y, e.cw, hb); }
    x.drawImage(frame, 0, y, e.cw, hb, dx, y, e.cw, hb);
    if (r() < 0.45) {
      // colour flash on the band; on the opaque hologram canvas use multiply so the black surround stays black
      const c2 = r() < 0.5 ? P.cyan : P.orangeL;
      x.globalCompositeOperation = opaque ? 'multiply' : 'source-atop';
      x.fillStyle = opaque ? rgba(mix3([255, 255, 255], fx.hex2rgb(c2), 0.6), 1) : rgba(c2, 0.28);
      x.fillRect(0, y, e.cw, hb);
      x.globalCompositeOperation = 'source-over';
    }
  }
  return O;
}

/** colour a low-res copy of `src` (white-alpha or frame) into `dst`, mode 'in' = flat colour, 'atop' = keep detail */
function colourInto(dst, src, col, mode = 'in', k = 1) {
  const x = wctx(dst);
  x.globalCompositeOperation = 'copy';
  x.drawImage(src, 0, 0, dst.width, dst.height);
  // 'source-atop' with an opaque fill == 'source-in' recolour, but bounded (≈4× faster on the CPU raster)
  x.globalCompositeOperation = 'source-atop';
  x.fillStyle = colStr(col, mode === 'in' ? 1 : k); x.fillRect(0, 0, dst.width, dst.height);
  return dst;
}

/* ------------------------------------------------------------------ drawCharacter */
/**
 * drawCharacter(ctx, t, opts)
 *  opts.image      full-body RGBA image/canvas (char_full*.png layout)            [required]
 *  opts.imageMono  same-layout mono image for `mono` crossfade (char_mono.png)
 *  opts.x, opts.y  feet anchor (bottom-centre of the image) in ctx user space      [960, 1040]
 *  opts.h          target height in px                                            [1000]
 *  opts.energy     0..1 (lyric-onset drive: rim pulse + bloom brightness only)        [0.5]
 *  opts.tint       0 cold → 1 warm (cold grade + rim colour)                       [1]
 *  opts.breathing  bool | scale amount (1 = 1.000↔1.008, 3.5 s)                    [true]
 *  opts.sway       bool | amplitude multiplier (1 = 2–6 px @ h=1000)               [true]
 *  opts.float      bool | multiplier (1 = ±6 px @ h=1000, 5 s)                     [true]
 *  opts.rim        bool | {color, strength, inner}                                 [true]
 *  opts.bloom      0..1                                                           [0.35]
 *  opts.hologram   0..1                                                           [0]
 *  opts.ghosts     0..1, with opts.cutAge = seconds since the last hard cut (omit → steady echoes) [0]
 *  opts.glitch     0..1 slice-glitch bursts                                       [0]
 *  opts.mono       0..1 crossfade to opts.imageMono                                [0]
 *  opts.alpha      0..1 overall                                                   [1]
 *  opts.flip       mirror horizontally                                            [false]
 *  opts.seed       PRNG key (string|number)                                       ['claude']
 *  opts.cacheH     pin the cache level (e.g. the largest h of a dolly) so an animated h never rebuilds caches
 *                  mid-shot; drawing is then scaled by h/cacheH                    [h]
 *  opts.glowFilter 'bilinear' | 'nearest' — upscale filter for the half-res glow layers. 'nearest' saves ~4–6 ms
 *                  but pixelates echoes / rim edges at 1:1; use it for previews only.    ['bilinear']
 * Geometry (sway/breath/float) never depends on energy, so energy may jump on onsets without popping the figure.
 * Returns the drawn bbox {x0,y0,x1,y1,scale} in ctx user space (without fx overhang).
 */
export function drawCharacter(ctx, t, opts = {}) {
  const img = opts.image;
  if (!img) return null;
  const alpha = clamp(opts.alpha == null ? 1 : opts.alpha);
  const h = opts.h || 1000, ax = opts.x == null ? W / 2 : opts.x, ay = opts.y == null ? H - 40 : opts.y;
  const energy = clamp(opts.energy == null ? 0.5 : opts.energy);
  const tint = clamp(opts.tint == null ? 1 : opts.tint);
  const seed = opts.seed == null ? 'claude' : opts.seed;
  const num = (v, d) => (v === false ? 0 : v === true || v == null ? d : +v);
  const breathe = num(opts.breathing, 1), swayAmt = num(opts.sway, 1), floatAmt = num(opts.float, 1);
  const bloomAmt = clamp(opts.bloom == null ? 0.35 : +opts.bloom);
  const holo = clamp(+opts.hologram || 0), ghosts = clamp(+opts.ghosts || 0), glitch = clamp(+opts.glitch || 0);
  const mono = opts.imageMono ? clamp(+opts.mono || 0) : 0;
  const nearest = opts.glowFilter === 'nearest';
  const rimO = opts.rim === false ? null : (typeof opts.rim === 'object' ? opts.rim : {});
  const rimCol = rimO && rimO.color ? toRGB(rimO.color) : rimColour(tint);
  const rimStr = rimO ? (rimO.strength == null ? 1 : rimO.strength) : 0;
  const bounds = { x0: ax - h * 0.28, y0: ay - h, x1: ax + h * 0.28, y1: ay, scale: 1 };
  if (alpha <= 0.002) return bounds;

  const e = getEntry(img, opts.cacheH || h);
  const s = h / e.hc;                                       // cache px → user px
  bounds.x0 = ax - e.wc * s / 2; bounds.x1 = ax + e.wc * s / 2; bounds.scale = s;

  // --- source (with mono crossfade) -----------------------------------------------------------------
  let src = e.src;
  if (mono > 0.002) {
    const em = getEntry(opts.imageMono, opts.cacheH || h);
    if (mono > 0.998 && em.cw === e.cw && em.ch === e.ch) src = em.src;
    else {
      const mc = work(e, 'mix'), x = wctx(mc);
      x.clearRect(0, 0, e.cw, e.ch); x.drawImage(e.src, 0, 0);
      x.globalAlpha = mono; x.drawImage(em.src, 0, 0, e.cw, e.ch);
      src = mc;
    }
  }
  // --- sway + grade -> frame ------------------------------------------------------------------------
  let frame = src;
  // geometry never depends on `energy` (it can jump on lyric onsets; a pure function has no history to smooth it)
  const swayK = swayAmt;
  if (swayK > 0.01 || tint < 0.995) {
    const F = work(e, 'frame');
    if (swayK > 0.01) swayPass(e, src, F, t, swayK, seed);
    else { const x = wctx(F); x.clearRect(0, 0, e.cw, e.ch); x.drawImage(src, 0, 0); }
    gradePass(F, e.cw, e.ch, tint);
    frame = F;
  }
  const base = frame;                                         // alpha-correct frame (rim / ghosts derive from it)
  let holoFrame = null;
  if (holo > 0.002) holoFrame = holoPass(e, frame, t, holo, s, mix3(rimCol, [255, 255, 255], 0.25), seed);
  const gAmt = Math.max(glitch, holo * 0.3);
  if (gAmt > 0.002) {
    if (holo < 0.998) frame = glitchPass(e, frame, t, gAmt, s, seed, 'gl');
    if (holoFrame) holoFrame = glitchPass(e, holoFrame, t, gAmt, s, seed, 'glH');
  }

  // --- placement --------------------------------------------------------------------------------------
  const bph = (Math.sin(TAU * t / 3.5 + rnd(seed, 'breath') * TAU) + 1) / 2;   // 0..1
  const sy = s * (1 + 0.008 * breathe * bph), sx = s * (1 + 0.004 * breathe * bph) * (opts.flip ? -1 : 1);
  const fy = -6 * (h / 1000) * floatAmt * Math.sin(TAU * t / 5 + rnd(seed, 'float') * TAU);
  bounds.y0 = ay + fy - e.hc * sy - 0; bounds.y1 = ay + fy;

  ctx.save();
  ctx.translate(ax, ay + fy);
  ctx.scale(sx, sy);
  ctx.translate(-e.cw / 2, -(e.M + e.hc));
  const ga = ctx.globalAlpha * alpha;
  const pulse = 0.55 + 0.45 * energy + 0.1 * Math.sin(TAU * t / 1.75) * (0.4 + energy);

  // Additive layers are pre-composited at 1/2 res into an UNDER layer (rim halo + ghost echoes, behind the body)
  // and an OVER layer (inner rim + bloom, on top), so each costs one upscaled drawImage on the main canvas.
  const flick = holo > 0 ? 1 - holo * (0.22 + 0.18 * noise1(seed + ':fl', t * 9) + (rnd(seed, 'fl', bucket(t, 24)) < 0.06 ? 0.25 : 0)) : 1;
  const doRim = rimStr > 0.002;
  let hb = null;
  const halfBase = () => {                                       // one bilinear 1/2-res copy of the frame, shared
    if (hb) return hb;
    hb = work(e, 'half', 2); const x = wctx(hb);
    x.globalCompositeOperation = 'copy'; x.drawImage(base, 0, 0, hb.width, hb.height);
    return hb;
  };
  const age = opts.cutAge, gk = ghosts > 0.002 ? (age == null ? 1 : Math.exp(-Math.max(0, age) / 0.55)) : 0;
  const haloA = clamp(rimStr * pulse * (1 - 0.4 * holo));
  if (doRim && gk <= 0.01) {
    // halo only: draw the cached coloured 1/3-res layer directly (one upscaled draw)
    const L = haloLayer(e);
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga * haloA;
    ctx.imageSmoothingEnabled = !nearest;
    const reach = -L.ox;
    drawBanded(ctx, haloColoured(L, rimCol), L.ox, L.oy - 6 * e.k, L.ds, bandsFor(e, reach, reach + 6 * e.k));
    ctx.imageSmoothingEnabled = true;
  } else if (gk > 0.01) {
    const L = haloLayer(e);
    // padding: the halo needs it all round, the echoes mostly sideways (their vertical drift is ≤ 0.2 × spread)
    const ph = doRim ? -L.ox / 2 + 4 * e.k : 0;
    const pu = Math.ceil(Math.max(ph, gk > 0.01 ? 72 * e.k : 0)), pw = Math.ceil(Math.max(ph, gk > 0.01 ? 16 * e.k : 0));
    const U = (e.work.under = sized(e.work.under, Math.ceil(e.cw / 2) + 2 * pu, Math.ceil(e.ch / 2) + 2 * pw)), ux = wctx(U);
    ux.clearRect(0, 0, U.width, U.height);
    ux.globalCompositeOperation = 'lighter';
    if (doRim) {
      // rim halo (offset 6 px up: the light sits behind and above her)
      ux.globalAlpha = haloA;
      ux.drawImage(haloColoured(L, rimCol), pu + L.ox / 2, pw + (L.oy - 6 * e.k) / 2, L.c.width * L.ds / 2, L.c.height * L.ds / 2);
    }
    if (gk > 0.01) {
      // ghost echoes: 3 tinted copies that spread out and fade after a cut (steady drift if cutAge is omitted)
      const E = colourInto(work(e, 'ghost', 2), halfBase(), mix3(rimCol, [255, 255, 255], 0.3), 'atop', 0.7);
      const gdir = rnd(seed, 'gdir', age == null ? 0 : Math.floor((t - age) * 1000)) < 0.5 ? -1 : 1;
      for (let i = 1; i <= 3; i++) {
        // after a cut the echoes start wide (≈45 px × i) and converge into her as they fade
        const spread = age == null ? 12 + 4 * Math.sin(TAU * t / 4.2 + i * 1.9) : 8 + 38 * gk;
        const dx = gdir * (i % 2 ? 1 : -0.7) * spread * i * e.k / 2;   // screen px @ h=1000 → half-res cache px
        const dy = -spread * 0.2 * i * e.k / 2;
        ux.globalAlpha = clamp(ghosts * gk * [0, 0.5, 0.32, 0.18][i]);
        ux.drawImage(E, Math.round(pu + dx), Math.round(pw + dy));
      }
    }
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga;
    ctx.imageSmoothingEnabled = !nearest;
    drawBanded(ctx, U, -2 * pu, -2 * pw, 2, bandsFor(e, 2 * pu, 2 * pw));
    ctx.imageSmoothingEnabled = true;
  }
  // --- body -------------------------------------------------------------------------------------------
  if (holo < 0.998) {
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = ga * (1 - holo);
    ctx.drawImage(frame, 0, 0);
  }
  if (holoFrame) {
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga * flick * holo;
    drawBanded(ctx, holoFrame, 0, 0, 1, bandsFor(e, Math.ceil(70 * e.k), 0));   // 70 px: room for glitch-band offsets
  }
  // --- over layer: inner rim + bloom ------------------------------------------------------------------
  const doInner = doRim && rimO.inner !== false;
  if (doInner || bloomAmt > 0.002) {
    const bl = bloomAmt > 0.002 ? bloomLayer(e) : null;
    const pv = bl ? Math.ceil(-bl.ox / 2) : 0;
    const V = (e.work.over = sized(e.work.over, Math.ceil(e.cw / 2) + 2 * pv, Math.ceil(e.ch / 2) + 2 * pv)), vx = wctx(V);
    vx.clearRect(0, 0, V.width, V.height);
    vx.globalCompositeOperation = 'lighter';
    if (doInner) {
      // edge bands = (frame − frame shifted right/down) ∪ (frame − frame shifted left/down), integer half-res
      // offsets only (no resampling): thin edge light on both flanks + the top, like a light behind her
      const B2 = halfBase(), RA = work(e, 'rimA', 2), RB = work(e, 'rimB', 2);
      const o = Math.max(1, Math.round(4.5 * e.k / 2)), oy = Math.max(1, Math.round(o * 0.7));
      for (const [c, dx] of [[RA, o], [RB, -o]]) {
        const x = wctx(c);
        x.globalCompositeOperation = 'copy'; x.drawImage(B2, 0, 0);
        x.globalCompositeOperation = 'destination-out'; x.drawImage(B2, dx, oy);
        x.globalCompositeOperation = 'source-atop'; x.fillStyle = rgba(rimCol, 1); x.fillRect(0, 0, c.width, c.height);
      }
      vx.globalAlpha = clamp(0.4 * rimStr * pulse);
      vx.drawImage(RA, pv, pv); vx.drawImage(RB, pv, pv);
    }
    if (bl) {
      const ba = bloomAmt * (0.5 + 0.5 * energy) * (1 - 0.5 * holo);
      const put = (L, a) => { vx.globalAlpha = clamp(a); vx.drawImage(L.c, pv + L.ox / 2, pv + L.oy / 2, L.c.width * L.ds / 2, L.c.height * L.ds / 2); };
      if (mono > 0.002) put(bloomLayer(getEntry(opts.imageMono, opts.cacheH || h)), ba * mono);
      if (mono < 0.998) put(bl, ba * (1 - mono));
    }
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga * flick;
    ctx.imageSmoothingEnabled = !nearest;
    drawBanded(ctx, V, -2 * pv, -2 * pv, 2, bandsFor(e, 2 * pv + 4, 2 * pv + 4));
    ctx.imageSmoothingEnabled = true;
  }
  ctx.restore();
  return bounds;
}
/** build every cache layer for (image[, imageMono], h) up front — call while awaiting MV.ready so the first frame
 *  of a shot doesn't pay the one-off 100–170 ms build. Accepts the same opts as drawCharacter. */
export function prepareCharacter(opts) {
  const c = makeCanvas(8, 8);
  drawCharacter(c.getContext('2d'), 0, Object.assign({}, opts, { rim: true, bloom: 0.5, ghosts: 0.5, cutAge: 0, hologram: 0.5,
    mono: opts.imageMono ? 0.5 : 0, tint: 0.5, alpha: 1 }));
}
function mix3(a, b, k) { return [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)]; }

/* ------------------------------------------------------------------ drawVoiceCrowd */
// silhouette -> Map(colour -> {body, soft, halo}) at a fixed cache height
const CROWD = new Map();
const CROWD_H = 520;
function crowdEntry(sil, col) {
  let m = CROWD.get(sil);
  if (!m) { m = new Map(); CROWD.set(sil, m); }
  const key = String(col);
  let e = m.get(key);
  if (e) return e;
  const hc = Math.min(CROWD_H, imgH(sil)), wc = Math.round(imgW(sil) * hc / imgH(sil));
  const pad = 48, cw = wc + 2 * pad, ch = hc + 2 * pad;
  const rgb = toRGB(col);
  const base = makeCanvas(cw, ch), bx = wctx(base);
  bx.imageSmoothingQuality = 'high';
  bx.drawImage(sil, pad, pad, wc, hc);
  bx.globalCompositeOperation = 'source-in'; bx.fillStyle = '#fff'; bx.fillRect(0, 0, cw, ch);
  // body: tinted, brighter towards the head, fading at the feet; core glow in thick regions
  const body = makeCanvas(cw, ch), x = wctx(body);
  x.filter = 'blur(1.6px)'; x.drawImage(base, 0, 0); x.filter = 'none';
  x.globalCompositeOperation = 'source-in';
  const g = x.createLinearGradient(0, pad, 0, pad + hc);
  g.addColorStop(0, rgba(mix3(rgb, [255, 255, 255], 0.3), 0.78));
  g.addColorStop(0.45, rgba(rgb, 0.62));
  g.addColorStop(0.86, rgba(mix3(rgb, [0, 0, 0], 0.25), 0.42));
  g.addColorStop(1, rgba(mix3(rgb, [0, 0, 0], 0.4), 0.06));
  x.fillStyle = g; x.fillRect(0, 0, cw, ch);
  const core = makeCanvas(cw, ch), cx = wctx(core);
  cx.filter = 'blur(14px)'; cx.drawImage(base, 0, 0); cx.filter = 'none';
  cx.globalCompositeOperation = 'destination-in'; cx.drawImage(base, 0, 0);
  cx.globalCompositeOperation = 'source-in'; cx.fillStyle = rgba(mix3(rgb, [255, 255, 255], 0.55), 0.45); cx.fillRect(0, 0, cw, ch);
  x.globalCompositeOperation = 'lighter'; x.drawImage(core, 0, 0);
  const soft = makeCanvas(cw, ch), sx = wctx(soft);
  sx.filter = 'blur(7px)'; sx.drawImage(body, 0, 0); sx.filter = 'none';
  const halo = makeCanvas(cw, ch), hx = wctx(halo);
  hx.filter = 'blur(22px)'; hx.drawImage(base, 0, 0); hx.filter = 'none';
  hx.globalCompositeOperation = 'source-in'; hx.fillStyle = rgba(rgb, 1); hx.fillRect(0, 0, cw, ch);
  e = { body, soft, halo, hc, wc, pad, cw, ch };
  if (m.size > 10) m.delete(m.keys().next().value);
  m.set(key, e);
  return e;
}
/**
 * drawVoiceCrowd(ctx, t, opts) — glowing faceless copies of Claude ("the voices").
 *  opts.silhouette  white RGBA silhouette (char_silhouette.png)           [required]
 *  opts.positions   [{x, y (feet), h, depth 0 near..1 far, alpha?, flip?}]
 *  opts.color       glow colour (hex or [r,g,b])                         [P.ice]
 *  opts.blur        0..1 extra softness (far figures get more)            [0.4]
 *  opts.alpha       overall alpha                                         [1]
 *  opts.glow        halo strength multiplier                              [1]
 *  opts.seed        PRNG key for the per-figure idle motion               ['crowd']
 * Figures are drawn far → near; each breathes and sways on its own seeded phase.
 */
export function drawVoiceCrowd(ctx, t, o = {}) {
  const sil = o.silhouette;
  if (!sil || !o.positions || !o.positions.length) return;
  const e = crowdEntry(sil, o.color || P.ice);
  const blur = o.blur == null ? 0.4 : o.blur, alpha = o.alpha == null ? 1 : o.alpha, glow = o.glow == null ? 1 : o.glow;
  const seed = o.seed == null ? 'crowd' : o.seed;
  const order = o.positions.map((p, i) => [p, i]).sort((a, b) => (b[0].depth || 0) - (a[0].depth || 0));
  ctx.save();
  const ga = ctx.globalAlpha;
  for (const [p, i] of order) {
    const d = clamp(p.depth || 0);
    const a = alpha * (p.alpha == null ? 1 : p.alpha) * lerp(1, 0.25, d);
    if (a <= 0.003) continue;
    const ph = rnd(seed, 'ph', i) * TAU;
    const br = 1 + 0.007 * Math.sin(TAU * t / (3.2 + rnd(seed, 'bp', i)) + ph);
    const sway = 3 * Math.sin(TAU * t / (5.5 + 2 * rnd(seed, 'sp', i)) + ph) * p.h / 1000;
    const s = p.h / e.hc;
    const flip = p.flip == null ? rnd(seed, 'flip', i) < 0.35 : p.flip;
    ctx.save();
    ctx.translate(p.x + sway, p.y);
    ctx.scale(s * (flip ? -1 : 1) * (1 + (br - 1) * 0.5), s * br);
    ctx.translate(-e.cw / 2, -(e.pad + e.hc));
    const k = clamp(blur * (0.35 + d));
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga * clamp(a * 0.42 * glow);
    ctx.drawImage(e.halo, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    if (k < 0.99) { ctx.globalAlpha = ga * clamp(a * (1 - k)); ctx.drawImage(e.body, 0, 0); }
    if (k > 0.01) { ctx.globalAlpha = ga * clamp(a * k); ctx.drawImage(e.soft, 0, 0); }
    // a touch of additive light so the figures read as emitters, not cut-outs
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = ga * clamp(a * 0.12 * glow);
    ctx.drawImage(e.soft, 0, 0);
    ctx.restore();
  }
  ctx.restore();
}

/* ------------------------------------------------------------------ drawMonitorFace */
function homography(q) {
  // unit square (u,v) -> quad [p0 (0,0), p1 (1,0), p2 (1,1), p3 (0,1)]
  const [x0, y0] = q[0], [x1, y1] = q[1], [x2, y2] = q[2], [x3, y3] = q[3];
  const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2;
  const sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
  let g = 0, h = 0;
  if (Math.abs(sx) > 1e-9 || Math.abs(sy) > 1e-9) {
    const den = dx1 * dy2 - dx2 * dy1;
    g = (sx * dy2 - dx2 * sy) / den; h = (dx1 * sy - sx * dy1) / den;
  }
  const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, c = x0;
  const d = y1 - y0 + g * y1, e = y3 - y0 + h * y3, f = y0;
  return (u, v) => { const w = g * u + h * v + 1; return [(a * u + b * v + c) / w, (d * u + e * v + f) / w]; };
}
function normQuad(q) { return q.map((p) => (Array.isArray(p) ? p : [p.x, p.y])); }
function normRect(img, r) {
  if (!r) return [0, 0, imgW(img), imgH(img)];
  if (Array.isArray(r)) return r;
  return [r.x || 0, r.y || 0, r.w || r.width, r.h || r.height];
}
/** affine that maps source triangle (s0,s1,s2) onto destination triangle (d0,d1,d2) */
function triAffine(s0, s1, s2, d0, d1, d2) {
  const ux = s1[0] - s0[0], uy = s1[1] - s0[1], vx = s2[0] - s0[0], vy = s2[1] - s0[1];
  const det = ux * vy - vx * uy;
  if (Math.abs(det) < 1e-9) return null;
  const pX = d1[0] - d0[0], pY = d1[1] - d0[1], qX = d2[0] - d0[0], qY = d2[1] - d0[1];
  const a = (pX * vy - qX * uy) / det, c = (qX * ux - pX * vx) / det;
  const b = (pY * vy - qY * uy) / det, d = (qY * ux - pY * vx) / det;
  return [a, b, c, d, d0[0] - a * s0[0] - c * s0[1], d0[1] - b * s0[0] - d * s0[1]];
}
function inflate(tri, px) {
  const cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3, cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3;
  return tri.map(([x, y]) => { const dx = x - cx, dy = y - cy, l = Math.hypot(dx, dy) || 1; return [x + dx / l * px, y + dy / l * px]; });
}
/**
 * drawMonitorFace(ctx, quad, image, srcRect, opts) — image crop mapped into a perspective quad.
 *  quad     [p0 top-left, p1 top-right, p2 bottom-right, p3 bottom-left] as [x,y] or {x,y}
 *  srcRect  [sx,sy,sw,sh] | {x,y,w,h} | null (whole image)
 *  opts     {t, seed, scanlines 0..1 [0.5], glitch 0..1 [0], tint colour|null, alpha [1], bg ['#07090B'],
 *            glow 0..1 [0.5] (CRT bloom / roll bar), grid (subdivisions, auto)}
 * Projectively-correct: a homography is subdivided into a grid of affine triangles, each clipped to its slightly
 * inflated destination triangle (inflation hides AA seams; a dark backing makes overlaps harmless).
 */
export function drawMonitorFace(ctx, quad, image, srcRect, o = {}) {
  if (!image || !quad) return;
  const q = normQuad(quad), [rx, ry, rw, rh] = normRect(image, srcRect);
  const t = o.t || 0, seed = o.seed == null ? 'mon' : o.seed;
  const scan = o.scanlines == null ? 0.5 : o.scanlines, glitch = o.glitch || 0, glowA = o.glow == null ? 0.5 : o.glow;
  const Hm = homography(q);
  const span = Math.max(Math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]), Math.hypot(q[3][0] - q[0][0], q[3][1] - q[0][1]),
    Math.hypot(q[2][0] - q[3][0], q[2][1] - q[3][1]), Math.hypot(q[2][0] - q[1][0], q[2][1] - q[1][1]));
  const n = o.grid || clamp(Math.ceil(span / 110), 2, 10);
  const quadPath = () => { ctx.beginPath(); ctx.moveTo(q[0][0], q[0][1]); for (let i = 1; i < 4; i++) ctx.lineTo(q[i][0], q[i][1]); ctx.closePath(); };
  ctx.save();
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  const ga = ctx.globalAlpha;
  const base = ctx.getTransform();
  // backing
  quadPath(); ctx.fillStyle = o.bg || '#07090B'; ctx.fill();
  // glitch bands (in v) re-roll at 12 Hz, gated in bursts
  const bands = [];
  if (glitch > 0.002 && rnd(seed, 'mg', bucket(t, 6)) < 0.2 + 0.7 * glitch) {
    const r = rng(seed, 'mgb', bucket(t, 12));
    const nb = 1 + Math.floor(r() * 4 * glitch + r());
    for (let i = 0; i < nb; i++) {
      const v0 = r(), hv = 0.01 + r() * r() * 0.12;
      bands.push([v0, Math.min(1, v0 + hv), (r() - 0.5) * 0.18 * glitch]);
    }
  }
  const P0 = [];
  for (let j = 0; j <= n; j++) for (let i = 0; i <= n; i++) P0.push(Hm(i / n, j / n));
  const pt = (i, j) => P0[j * (n + 1) + i];
  const sp = (i, j, du = 0) => [rx + (i / n + du) * rw, ry + (j / n) * rh];
  const drawTri = (s, d, du) => {
    const m = triAffine(s[0], s[1], s[2], d[0], d[1], d[2]);
    if (!m) return;
    const di = inflate(d, 0.6);
    ctx.save();
    ctx.beginPath(); ctx.moveTo(di[0][0], di[0][1]); ctx.lineTo(di[1][0], di[1][1]); ctx.lineTo(di[2][0], di[2][1]); ctx.closePath();
    ctx.clip();
    ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
    // only sample a margin around the triangle's source bbox
    const xs = [s[0][0], s[1][0], s[2][0]], ys = [s[0][1], s[1][1], s[2][1]];
    const mx = rw / n * 0.25 + 2, my = rh / n * 0.25 + 2;
    let sx0 = Math.max(0, Math.min(...xs) - mx), sy0 = Math.max(0, Math.min(...ys) - my);
    let sx1 = Math.min(imgW(image), Math.max(...xs) + mx), sy1 = Math.min(imgH(image), Math.max(...ys) + my);
    if (sx1 > sx0 && sy1 > sy0) ctx.drawImage(image, sx0, sy0, sx1 - sx0, sy1 - sy0, sx0, sy0, sx1 - sx0, sy1 - sy0);
    ctx.restore();
  };
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const vmid = (j + 0.5) / n;
    let du = 0;
    for (const [a, b, d] of bands) if (vmid >= a && vmid < b) du = d;
    if (du) continue; // drawn by band pass
    drawTri([sp(i, j), sp(i + 1, j), sp(i, j + 1)], [pt(i, j), pt(i + 1, j), pt(i, j + 1)]);
    drawTri([sp(i + 1, j), sp(i + 1, j + 1), sp(i, j + 1)], [pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)]);
  }
  // glitch bands: draw a v-slab with its own u offset (+ a colour flash)
  for (const [v0, v1, du] of bands) {
    const a0 = Hm(0, v0), b0 = Hm(1, v0), b1 = Hm(1, v1), a1 = Hm(0, v1);
    ctx.save();
    ctx.beginPath(); ctx.moveTo(a0[0], a0[1]); ctx.lineTo(b0[0], b0[1]); ctx.lineTo(b1[0], b1[1]); ctx.lineTo(a1[0], a1[1]); ctx.closePath(); ctx.clip();
    const m = triAffine([rx + du * rw, ry + v0 * rh], [rx + (1 + du) * rw, ry + v0 * rh], [rx + du * rw, ry + v1 * rh], a0, b0, a1);
    if (m) {
      ctx.save(); ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
      ctx.drawImage(image, 0, 0); ctx.restore();
    }
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = ga * 0.12 * glitch;
    ctx.fillStyle = rnd(seed, 'bc', v0) < 0.5 ? P.cyan : P.orangeL; ctx.fillRect(-1e4, -1e4, 2e4, 2e4);
    ctx.restore();
  }
  ctx.setTransform(base);
  ctx.save();
  quadPath(); ctx.clip();
  if (o.tint) { ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = ga * 0.22; ctx.fillStyle = colStr(o.tint); quadPath(); ctx.fill(); }
  // scanlines along the screen's own v axis (perspective-correct)
  if (scan > 0.002) {
    const nl = Math.max(20, Math.round(span / 3.2));
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = ga * 0.42 * scan;
    ctx.strokeStyle = '#000'; ctx.lineWidth = Math.max(0.8, span / nl * 0.42);
    ctx.beginPath();
    for (let k = 0; k < nl; k++) { const v = (k + 0.5) / nl, a = Hm(0, v), b = Hm(1, v); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); }
    ctx.stroke();
  }
  if (glowA > 0.002) {
    // rolling bright bar + inner edge darkening (CRT)
    const ph = ((t * 0.35 + rnd(seed, 'roll')) % 1);
    const v0 = ph * 1.3 - 0.15, v1 = v0 + 0.12;
    const a0 = Hm(0, clamp(v0)), b0 = Hm(1, clamp(v0)), b1 = Hm(1, clamp(v1)), a1 = Hm(0, clamp(v1));
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = ga * 0.10 * glowA;
    ctx.fillStyle = o.tint ? colStr(o.tint) : P.ice;
    ctx.beginPath(); ctx.moveTo(a0[0], a0[1]); ctx.lineTo(b0[0], b0[1]); ctx.lineTo(b1[0], b1[1]); ctx.lineTo(a1[0], a1[1]); ctx.closePath(); ctx.fill();
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = ga * 0.55 * glowA;
    ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = span * 0.06; ctx.lineJoin = 'round';
    quadPath(); ctx.stroke();
  }
  ctx.restore();
  ctx.restore();
}

/* ------------------------------------------------------------------ camera */
const CAM0 = { scale: 1, x: 0, y: 0, rotate: 0 };
/**
 * cameraShot(t, {from, to, t0, t1, ease, drift, seed, cx, cy})
 *   from/to {scale, x, y, rotate (radians)}; missing keys default to identity. ease = fx.ease name or fn
 *   ['inOutSine']. drift = px of slow seeded hand-held wander (rotation follows at drift*0.0004 rad).
 * cameraShot(k, from, to, ease)  — positional form; k is already the 0..1 progress.
 * Returns {scale, x, y, rotate, cx, cy}; pass to applyCamera.
 */
export function cameraShot(t, a, b, c) {
  let from, to, k, fn, o;
  if (a && (a.from || a.to)) {
    o = a; from = a.from || CAM0; to = a.to || from;
    const t0 = a.t0 == null ? 0 : a.t0, t1 = a.t1 == null ? t0 + 1 : a.t1;
    k = t1 > t0 ? clamp((t - t0) / (t1 - t0)) : 1; fn = a.ease;
  } else { o = {}; from = a || CAM0; to = b || from; k = clamp(t); fn = c; }
  const ef = typeof fn === 'function' ? fn : ease[fn || 'inOutSine'] || ease.inOutSine;
  const e = ef(k);
  const g = (key, d) => lerp(from[key] == null ? d : from[key], to[key] == null ? (from[key] == null ? d : from[key]) : to[key], e);
  const cam = { scale: g('scale', 1), x: g('x', 0), y: g('y', 0), rotate: g('rotate', 0), cx: o.cx == null ? W / 2 : o.cx, cy: o.cy == null ? H / 2 : o.cy };
  if (o.drift) {
    const s = o.seed == null ? 'cam' : o.seed, tt = (o.t != null ? o.t : t) * 0.35;
    cam.x += (noise1(s + ':x', tt) - 0.5) * 2 * o.drift;
    cam.y += (noise1(s + ':y', tt + 7.3) - 0.5) * 2 * o.drift * 0.6;
    cam.rotate += (noise1(s + ':r', tt * 0.8 + 3.1) - 0.5) * 2 * o.drift * 0.0004;
  }
  return cam;
}
/** applies cam about its centre (default canvas centre): x/y pan in screen px, scale >1 zooms in */
export function applyCamera(ctx, cam) {
  if (!cam) return;
  const cx = cam.cx == null ? W / 2 : cam.cx, cy = cam.cy == null ? H / 2 : cam.cy;
  ctx.translate(cx + (cam.x || 0), cy + (cam.y || 0));
  if (cam.rotate) ctx.rotate(cam.rotate);
  const s = cam.scale == null ? 1 : cam.scale;
  ctx.scale(s, s);
  ctx.translate(-cx, -cy);
}
