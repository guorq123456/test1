// fx.js — pure drawing helpers for the 機械の声 × Claude MV.
// Everything here is deterministic: randomness comes only from seeded mulberry32.

export const W = 1920, H = 1080;

/* ------------------------------------------------------------------ math */
export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, k) => a + (b - a) * k;
export const inv = (a, b, x) => clamp((x - a) / (b - a));
export const smooth = (a, b, x) => { const k = inv(a, b, x); return k * k * (3 - 2 * k); };
export const fract = (x) => x - Math.floor(x);
export const TAU = Math.PI * 2;

export const ease = {
  linear: (k) => k,
  inQuad: (k) => k * k,
  outQuad: (k) => k * (2 - k),
  inOutQuad: (k) => (k < 0.5 ? 2 * k * k : -1 + (4 - 2 * k) * k),
  inCubic: (k) => k * k * k,
  outCubic: (k) => 1 - Math.pow(1 - k, 3),
  inOutCubic: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  outQuart: (k) => 1 - Math.pow(1 - k, 4),
  inOutQuart: (k) => (k < 0.5 ? 8 * k * k * k * k : 1 - Math.pow(-2 * k + 2, 4) / 2),
  outExpo: (k) => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
  inExpo: (k) => (k <= 0 ? 0 : Math.pow(2, 10 * k - 10)),
  inOutSine: (k) => -(Math.cos(Math.PI * k) - 1) / 2,
  outSine: (k) => Math.sin((k * Math.PI) / 2),
  outBack: (k) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
};
/** eased inverse-lerp */
export const ek = (a, b, x, fn = ease.inOutCubic) => fn(inv(a, b, x));

/* ------------------------------------------------------------------ PRNG */
export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function hash(...keys) {
  let h = 2166136261 >>> 0;
  for (const k of keys) {
    const s = String(k);
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    h ^= 0x9e; h = Math.imul(h, 16777619);
  }
  h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995); h ^= h >>> 15;
  return h >>> 0;
}
/** new PRNG keyed by any list of values (scene, element, frame bucket ...) */
export const rng = (...keys) => mulberry32(hash(...keys));
/** single deterministic random number in [0,1) */
export const rnd = (...keys) => mulberry32(hash(...keys))();
/** smooth 1D value noise in [0,1] */
export function noise1(seed, x) {
  const i = Math.floor(x), f = x - i;
  const a = rnd(seed, i), b = rnd(seed, i + 1);
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}
/** frame bucket helper (24 buckets / second by default) */
export const bucket = (t, rate = 24) => Math.floor(t * rate + 1e-6);

/* ---------------------------------------------------------------- colour */
export const P = {
  ink: '#1B1512', ink2: '#2A1F19', brown: '#3A2415',
  paper: '#F3EAD9', paper2: '#E9DCC3',
  orange: '#E8702A', orangeL: '#F4A062', orangeD: '#B8481A',
  gold: '#C9A054', goldD: '#8C6B35',
  steel: '#9FB3BF', ice: '#DDEBF2', cyan: '#7FD3E6',
  coldInk: '#0E1115', coldInk2: '#151A1F',
};
const rgbCache = new Map();
export function hex2rgb(h) {
  if (Array.isArray(h)) return h;
  let c = rgbCache.get(h);
  if (!c) {
    const s = h.replace('#', '');
    c = [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
    rgbCache.set(h, c);
  }
  return c;
}
export function mix(c1, c2, k) {
  const a = hex2rgb(c1), b = hex2rgb(c2);
  return [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
}
export function rgba(c, a = 1) {
  const v = hex2rgb(c);
  return `rgba(${v[0] | 0},${v[1] | 0},${v[2] | 0},${clamp(a)})`;
}
/** multi-stop colour ramp: stops [[k, colour], ...] */
export function ramp(stops, k) {
  if (k <= stops[0][0]) return hex2rgb(stops[0][1]);
  for (let i = 1; i < stops.length; i++) {
    if (k <= stops[i][0]) {
      const [k0, c0] = stops[i - 1], [k1, c1] = stops[i];
      return mix(c0, c1, (k - k0) / (k1 - k0));
    }
  }
  return hex2rgb(stops[stops.length - 1][1]);
}

/* ---------------------------------------------------------------- canvas */
let CANVAS_OPTS = {};
export function setCanvasOptions(o) { CANVAS_OPTS = o || {}; }
export function makeCanvas(w, h) {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h));
  if (CANVAS_OPTS.willReadFrequently) c.getContext('2d', { willReadFrequently: true }); // fix the backend before first use
  return c;
}
export function reset(ctx) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none'; ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
  ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0;
  ctx.letterSpacing = '0px'; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  ctx.lineCap = 'butt'; ctx.lineJoin = 'miter'; ctx.setLineDash([]);
}
/** draw an image with a given alpha / composite and restore */
export function blit(ctx, img, x, y, w, h, alpha = 1, op = 'source-over') {
  if (alpha <= 0.002 || !img) return;
  const ga = ctx.globalAlpha, go = ctx.globalCompositeOperation;
  ctx.globalAlpha = ga * clamp(alpha); ctx.globalCompositeOperation = op;
  if (w == null) ctx.drawImage(img, x, y); else ctx.drawImage(img, x, y, w, h);
  ctx.globalAlpha = ga; ctx.globalCompositeOperation = go;
}
/** tint: returns a new canvas = img's alpha filled with colour */
export function tinted(img, colour, w = img.width, h = img.height) {
  const c = makeCanvas(w, h), x = c.getContext('2d');
  x.drawImage(img, 0, 0, w, h);
  x.globalCompositeOperation = 'source-in';
  x.fillStyle = typeof colour === 'string' ? colour : rgba(colour);
  x.fillRect(0, 0, w, h);
  return c;
}
/** blurred + padded copy (for bloom / rim light) */
export function blurred(img, blur, pad, colour = null, w = img.width, h = img.height) {
  const src = colour ? tinted(img, colour, w, h) : img;
  const c = makeCanvas(w + pad * 2, h + pad * 2), x = c.getContext('2d');
  x.filter = `blur(${blur}px)`;
  x.drawImage(src, pad, pad, w, h);
  x.filter = 'none';
  return c;
}
/** crop region of image with feathered edges (feather in source px per side) */
export function featherCrop(img, sx, sy, sw, sh, f = {}) {
  const c = makeCanvas(sw, sh), x = c.getContext('2d');
  x.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
  x.globalCompositeOperation = 'destination-in';
  // build a mask by multiplying 4 gradients
  const m = makeCanvas(sw, sh), mx = m.getContext('2d');
  mx.fillStyle = '#000'; mx.fillRect(0, 0, sw, sh);
  mx.globalCompositeOperation = 'destination-in';
  const apply = (g) => { if (g) { mx.fillStyle = g; mx.fillRect(0, 0, sw, sh); } };
  const lin = (x0, y0, x1, y1, n) => {
    if (!n) return null;
    const g = mx.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)');
    return g;
  };
  // each gradient only covers its band; outside band alpha=1 thanks to clamp of linear gradient
  apply(lin(0, 0, f.l || 0, 0, f.l));
  apply(lin(sw, 0, sw - (f.r || 0), 0, f.r));
  apply(lin(0, 0, 0, f.t || 0, f.t));
  apply(lin(0, sh, 0, sh - (f.b || 0), f.b));
  x.drawImage(m, 0, 0);
  return c;
}
/** draw image to cover a destination rect, focused at (fx,fy) in source px, zoom = src px per dst px */
export function drawFocus(ctx, img, fx, fy, zoom, dx, dy, dw, dh) {
  const sw = dw * zoom, sh = dh * zoom;
  let sx = fx - sw / 2, sy = fy - sh / 2;
  sx = clamp(sx, 0, Math.max(0, img.width - sw)); sy = clamp(sy, 0, Math.max(0, img.height - sh));
  ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
}

/* ------------------------------------------------------------- typography */
export const F = {
  zomR: '"Zen Old Mincho"', zom: '"Zen Old Mincho"',
  smb: '"Shippori Mincho B1"',
  zkg: '"Zen Kaku Gothic New"',
  dot: '"DotGothic16"',
  mono: '"Share Tech Mono", "DotGothic16", monospace',
  orb: '"Orbitron"',
  cor: '"Cormorant Garamond"',
  zh: '"MV Noto Sans SC", "Zen Kaku Gothic New", sans-serif',
};
export const fontStr = (family, size, weight = 400, style = 'normal') => `${style} ${weight} ${size}px ${family}`;

const wCache = new Map();
let measureCtx = null;
function mctx() {
  if (!measureCtx) measureCtx = makeCanvas(8, 8).getContext('2d');
  return measureCtx;
}
/** advance width of one char in font (cached) */
export function charW(font, ch) {
  const key = font + '\u0001' + ch;
  let w = wCache.get(key);
  if (w === undefined) {
    const c = mctx(); c.font = font; c.letterSpacing = '0px';
    w = c.measureText(ch).width;
    wCache.set(key, w);
  }
  return w;
}
export function textW(font, s, trackPx = 0) {
  let w = 0; for (const ch of s) w += charW(font, ch) + trackPx;
  return Math.max(0, w - trackPx);
}

const NO_START = '、。，．」』）〕】！？!?…ー〜ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ・：；,.)]}　 ';
const NO_END = '「『（〔【([{';
const PREF_AFTER = '　 、。」』！？…';
const PARTICLE = 'はがをにでともへのてやかよねな';

/** split Japanese text into at most `maxLines` lines so each fits maxW (by measuring font) */
export function wrapJa(text, font, maxW, maxLines = 2, trackPx = 0) {
  if (text.includes('\n')) return text.split('\n');
  const chars = [...text];
  if (textW(font, text, trackPx) <= maxW || maxLines <= 1) return [text];
  let best = null;
  for (let i = 2; i < chars.length - 1; i++) {
    const a = chars[i - 1], b = chars[i];
    if (NO_START.includes(b) && b !== '　' && b !== ' ') continue;
    if (NO_END.includes(a)) continue;
    let left = chars.slice(0, i).join(''), right = chars.slice(i).join('');
    let pen = 0;
    if (b === '　' || b === ' ') { right = right.slice(1); pen -= 0.35; }
    else if (PREF_AFTER.includes(a)) pen -= 0.3;
    else if (b === '「' || b === '『') pen -= 0.25;
    else if (PARTICLE.includes(a) && !PARTICLE.includes(b)) pen -= 0.12;
    else pen += 0.25;
    left = left.replace(/[　 ]+$/, '');
    const wl = textW(font, left, trackPx), wr = textW(font, right, trackPx);
    const score = Math.max(wl, wr) / maxW + pen * 0.35 + Math.abs(wl - wr) / maxW * 0.15;
    if (!best || score < best.score) best = { score, left, right, wr };
  }
  if (!best) return [text];
  if (maxLines > 2 && best.wr > maxW) return [best.left, ...wrapJa(best.right, font, maxW, maxLines - 1, trackPx)];
  return [best.left, best.right];
}

/**
 * Lay out a text block.
 * o: {text, family, size, weight, style, track (em), lineH (multiple), maxW, maxLines, minSize,
 *     spans:[{match, color, scale, family, weight, glitch, tag}], wrap:boolean}
 * Returns {lines:[{chars:[{ch,x,w,size,font,span}], width}], size, lineH, width, height}
 */
export function layout(o) {
  const family = o.family, weight = o.weight || 400, style = o.style || 'normal';
  let size = o.size;
  const minSize = o.minSize || Math.round(o.size * 0.6);
  const maxW = o.maxW || 1600;
  const track = o.track || 0;
  const maxLines = o.maxLines || (o.wrap === false ? 1 : 2);
  let rows;
  let fixed = o.lines ? o.lines.slice() : null;
  // prefer shrinking a single line down to size*shrinkFirst before wrapping
  if (!fixed && !String(o.text).includes('\n')) {
    const w1 = measureRow(o.text, o, size).width;
    if (w1 > maxW) {
      const s2 = Math.floor(size * Math.max(maxW / w1, 0));
      if (o.shrinkFirst && s2 >= size * o.shrinkFirst) size = s2;
      else if (o.hint && maxLines >= 2) fixed = o.hint.split('\n'); // hand-made Japanese line break
    }
  }
  for (let guard = 0; guard < 40; guard++) {
    const font = fontStr(family, size, weight, style);
    rows = fixed ? fixed.slice() : wrapJa(o.text, font, maxW, maxLines, track * size);
    const widest = Math.max(...rows.map((r) => measureRow(r, o, size).width));
    if (widest <= maxW || size <= minSize) break;
    size = Math.max(minSize, Math.floor(size * 0.95));
  }
  const lineH = size * (o.lineH || 1.3);
  const lines = rows.map((r) => measureRow(r, o, size));
  const width = Math.max(...lines.map((l) => l.width));
  return { lines, size, lineH, width, height: lineH * (lines.length - 1) + size, nChars: lines.reduce((s, l) => s + l.chars.length, 0) };
}
function spanMap(row, spans) {
  const m = new Array([...row].length).fill(null);
  if (!spans) return m;
  const arr = [...row];
  for (const sp of spans) {
    const mt = [...sp.match];
    for (let i = 0; i + mt.length <= arr.length; i++) {
      let ok = true;
      for (let j = 0; j < mt.length; j++) if (arr[i + j] !== mt[j]) { ok = false; break; }
      if (ok) for (let j = 0; j < mt.length; j++) m[i + j] = sp;
    }
  }
  return m;
}
function measureRow(row, o, size) {
  const arr = [...row];
  const sm = spanMap(row, o.spans);
  const chars = [];
  let x = 0;
  const track = (o.track || 0) * size;
  for (let i = 0; i < arr.length; i++) {
    const sp = sm[i];
    const s = size * (sp && sp.scale ? sp.scale : 1);
    const font = fontStr(sp && sp.family ? sp.family : o.family, s, sp && sp.weight ? sp.weight : o.weight || 400, sp && sp.style ? sp.style : o.style || 'normal');
    const w = charW(font, arr[i]);
    chars.push({ ch: arr[i], x, w, size: s, font, span: sp });
    x += w + track;
  }
  return { chars, width: Math.max(0, x - track), text: row };
}

/**
 * Draw a laid-out block.
 * x,y: anchor (y = baseline of first line). o.align: 'left'|'center'|'right'.
 * o.color, o.alpha, o.reveal {style, rt, dur, seed}, o.exit {style, et, dur, seed},
 * o.cursor {color, blink:true, show}, o.glow {color, blur}, o.charFx(k, c, state) hook,
 * o.rgb {dx, a} (chromatic split), o.lineAlign per line.
 * Returns bounding box {x0,y0,x1,y1}.
 */
export function drawBlock(ctx, B, x, y, o = {}) {
  const align = o.align || 'left';
  const color = o.color || P.paper;
  const alpha = o.alpha == null ? 1 : o.alpha;
  if (alpha <= 0.003) return null;
  const n = B.nChars;
  const rv = o.reveal || null, ex = o.exit || null;
  let k = 0;
  const items = [];
  let bx0 = 1e9, bx1 = -1e9;
  B.lines.forEach((L, li) => {
    const lx = align === 'center' ? x - L.width / 2 : align === 'right' ? x - L.width : x;
    const ly = y + li * B.lineH;
    bx0 = Math.min(bx0, lx); bx1 = Math.max(bx1, lx + L.width);
    for (const c of L.chars) {
      items.push({ c, k, li, x: lx + c.x, y: ly });
      k++;
    }
  });
  const box = { x0: bx0, y0: y - B.size * 0.88, x1: bx1, y1: y + (B.lines.length - 1) * B.lineH + B.size * 0.2 };

  // cursor position for typewriter
  let shown = n, cursorAt = null;
  const st = (it) => {
    const s = { a: 1, dx: 0, dy: 0, rot: 0, sc: 1, vis: true, blur: 0 };
    const kk = it.k;
    if (rv) {
      const D = rv.dur || 0.6, T = rv.rt;
      switch (rv.style) {
        case 'typewriter': {
          const p = clamp(T / D);
          shown = Math.min(n, Math.floor(p * n + 0.0001) + (T > 0 ? 1 : 0));
          if (kk >= shown) s.vis = false;
          break;
        }
        case 'fadeup': {
          const stag = Math.min(0.045, Math.max(0.012, (D - 0.4) / Math.max(1, n)));
          const lk = clamp((T - kk * stag) / 0.42);
          const e = ease.outCubic(lk);
          s.a = e; s.dy = 12 * (1 - e);
          break;
        }
        case 'charfade': {
          const stag = Math.max(0.02, (D - 0.6) / Math.max(1, n));
          const lk = clamp((T - kk * stag) / 0.6);
          s.a = ease.inOutSine(lk); s.dy = 4 * (1 - lk);
          break;
        }
        case 'scatter': {
          const r = rng(rv.seed || 1, 'sc', kk);
          const lk = ease.outExpo(clamp((T - r() * 0.12) / D));
          s.dx = (r() - 0.5) * 360 * (1 - lk); s.dy = (r() - 0.5) * 220 * (1 - lk);
          s.rot = (r() - 0.5) * 1.2 * (1 - lk); s.a = clamp(lk * 1.6);
          break;
        }
        case 'pop': {
          const stag = Math.min(0.05, (D - 0.25) / Math.max(1, n));
          const lk = clamp((T - kk * stag) / 0.25);
          s.a = clamp(lk * 2); s.sc = lerp(1.35, 1, ease.outBack(lk));
          break;
        }
        case 'slam': {
          const lk = clamp(T / Math.max(0.05, D));
          s.sc = lerp(1.25, 1, ease.outExpo(lk)); s.a = clamp(lk * 4);
          break;
        }
        default: break; // slice / wipe / none handled at block level
      }
    }
    if (ex && ex.et > 0) {
      const D = ex.dur || 0.3, T = ex.et;
      switch (ex.style) {
        case 'dissolve': {
          const r = rng(ex.seed || 7, 'dz', kk);
          const delay = r() * D * 0.5;
          const lk = clamp((T - delay) / (D * 0.5));
          s.a *= 1 - ease.inQuad(lk); s.dy += 46 * ease.inQuad(lk); s.dx += (r() - 0.5) * 18 * lk;
          s.rot += (r() - 0.5) * 0.3 * lk;
          break;
        }
        case 'rise': {
          const lk = clamp(T / D);
          s.a *= 1 - ease.inOutSine(lk); s.dy -= 18 * ease.inQuad(lk);
          break;
        }
        case 'fade': default: {
          const lk = clamp(T / D);
          s.a *= 1 - ease.inOutSine(lk);
          break;
        }
      }
    }
    if (o.charFx) o.charFx(it, s);
    return s;
  };

  const drawAll = (c2, ox, oy, colourOverride, alphaMul) => {
    let lastFont = null;
    for (const it of items) {
      const s = st(it);
      if (!s.vis || s.a <= 0.003) continue;
      if (it.c.ch === ' ' || it.c.ch === '　') continue;
      const col = colourOverride || (it.c.span && it.c.span.color) || color;
      c2.globalAlpha = clamp(alpha * s.a * alphaMul * (it.c.span && it.c.span.alpha != null ? it.c.span.alpha : 1));
      c2.fillStyle = typeof col === 'string' ? col : rgba(col);
      if (it.c.font !== lastFont) { c2.font = it.c.font; lastFont = it.c.font; }
      const px = it.x + s.dx + ox, py = it.y + s.dy + oy;
      if (s.rot || s.sc !== 1) {
        c2.save();
        const cx = px + it.c.w / 2, cy = py - it.c.size * 0.35;
        c2.translate(cx, cy); c2.rotate(s.rot); c2.scale(s.sc, s.sc);
        c2.fillText(it.c.ch, -it.c.w / 2, it.c.size * 0.35);
        c2.restore();
      } else {
        c2.fillText(it.c.ch, px, py);
      }
    }
    c2.globalAlpha = 1;
  };

  ctx.save();
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; ctx.letterSpacing = '0px';
  if (rv && rv.style === 'wipe') {
    const p = ease.inOutCubic(clamp(rv.rt / (rv.dur || 0.6)));
    const sx = lerp(box.x0 - 20, box.x1 + 30, p);
    ctx.save();
    ctx.beginPath(); ctx.rect(box.x0 - 40, box.y0 - 40, sx - box.x0 + 40, box.y1 - box.y0 + 80); ctx.clip();
    if (o.glow) { ctx.shadowColor = o.glow.color; ctx.shadowBlur = o.glow.blur; }
    drawAll(ctx, 0, 0, null, 1);
    ctx.restore();
    if (p < 1) {
      ctx.globalAlpha = alpha * (1 - smooth(0.85, 1, p));
      ctx.fillStyle = o.ruleColor || color;
      ctx.fillRect(sx, box.y0 - 16, 2, box.y1 - box.y0 + 32);
      ctx.globalAlpha = alpha * 0.25 * (1 - p);
      ctx.fillRect(box.x0, box.y1 + 14, sx - box.x0, 1);
    }
  } else if (rv && rv.style === 'slice' && rv.rt < (rv.dur || 0.45)) {
    // render to scratch then draw horizontal slices with decaying offsets
    const D = rv.dur || 0.45, p = clamp(rv.rt / D);
    const pad = 60;
    const bw = Math.min(SCR_W, Math.ceil(box.x1 - box.x0 + pad * 2)), bh = Math.min(SCR_H, Math.ceil(box.y1 - box.y0 + pad * 2));
    const sc = scratch(bw, bh), sx = sc.getContext('2d');
    sx.setTransform(1, 0, 0, 1, 0, 0); sx.clearRect(0, 0, sc.width, sc.height);
    sx.textBaseline = 'alphabetic';
    const sbx = Math.floor(box.x0 - pad), sby = Math.floor(box.y0 - pad); // integer blit origin, sub-pixel kept in scratch
    drawAll(sx, -sbx, -sby, null, 1);
    const r = rng(rv.seed || 3, 'slice', Math.floor(rv.rt * 30));
    const amp = (1 - ease.outCubic(p)) * (o.sliceAmp || 90);
    let yy = 0;
    const appear = clamp(p * 3);
    while (yy < bh) {
      const hh = 4 + Math.floor(r() * 26);
      const off = (r() < 0.55 ? (r() - 0.5) * 2 * amp : 0);
      const show = r() < appear + 0.15;
      if (show) {
        ctx.globalAlpha = alpha * clamp(0.3 + appear);
        ctx.drawImage(sc, 0, yy, bw, Math.min(hh, bh - yy), sbx + Math.round(off), sby + yy, bw, Math.min(hh, bh - yy));
      }
      yy += hh;
    }
    if (p < 0.6) {
      // chromatic ghost
      ctx.globalAlpha = alpha * 0.35 * (1 - p / 0.6);
      ctx.globalCompositeOperation = o.lightBg ? 'multiply' : 'screen';
      ctx.drawImage(tintScratch(sc, o.lightBg ? '#00A0C0' : '#FF3030', bw, bh), 0, 0, bw, bh, sbx - Math.round(amp * 0.12 + 4), sby, bw, bh);
      ctx.drawImage(tintScratch(sc, o.lightBg ? '#C02040' : '#30E0FF', bw, bh), 0, 0, bw, bh, sbx + Math.round(amp * 0.12 + 4), sby, bw, bh);
      ctx.globalCompositeOperation = 'source-over';
    }
    ctx.globalAlpha = 1;
  } else {
    if (o.rgb && o.rgb.a > 0.01) {
      const dx = o.rgb.dx;
      ctx.globalCompositeOperation = o.lightBg ? 'multiply' : 'screen';
      drawAll(ctx, -dx, 0, o.lightBg ? '#20B8D8' : '#FF2A3A', o.rgb.a);
      drawAll(ctx, dx, 0, o.lightBg ? '#E83050' : '#2AE0FF', o.rgb.a);
      ctx.globalCompositeOperation = 'source-over';
    }
    if (o.glow) { ctx.shadowColor = o.glow.color; ctx.shadowBlur = o.glow.blur; }
    drawAll(ctx, 0, 0, null, 1);
    ctx.shadowBlur = 0;
  }
  // cursor
  if (o.cursor && o.cursor.show !== false) {
    const blinkOn = !o.cursor.blink || Math.floor((o.cursor.t || 0) * 2.4) % 2 === 0;
    let cx, cy, cs;
    if (rv && rv.style === 'typewriter' && shown < n) {
      const it = items[Math.max(0, shown - 1)];
      cx = shown > 0 ? it.x + it.c.w + 4 : items[0].x; cy = (shown > 0 ? it.y : items[0].y); cs = B.size;
      ctx.globalAlpha = alpha;
    } else {
      const it = items[items.length - 1];
      cx = it.x + it.c.w + 6; cy = it.y; cs = B.size;
      ctx.globalAlpha = blinkOn ? alpha * (o.cursor.alpha == null ? 1 : o.cursor.alpha) : 0;
    }
    ctx.fillStyle = o.cursor.color || color;
    const cw = o.cursor.w || Math.max(4, cs * 0.5);
    ctx.fillRect(cx, cy - cs * 0.82, cw, cs * 0.98);
    ctx.globalAlpha = 1;
  }
  ctx.restore();
  box.items = items;
  return box;
}
// fixed-size scratch buffers: their size must not depend on render history (bit-exact re-renders)
const SCR_W = W + 480, SCR_H = 900;
let _scratch = null, _tscr = null;
function scratch(w, h) {
  if (!_scratch) _scratch = makeCanvas(SCR_W, SCR_H);
  return _scratch;
}
function tintScratch(src, colour, w, h) {
  if (!_tscr) _tscr = makeCanvas(SCR_W, SCR_H);
  const x = _tscr.getContext('2d');
  x.clearRect(0, 0, SCR_W, SCR_H);
  x.globalCompositeOperation = 'source-over'; x.drawImage(src, 0, 0, w, h, 0, 0, w, h);
  x.globalCompositeOperation = 'source-in'; x.fillStyle = colour; x.fillRect(0, 0, w, h);
  x.globalCompositeOperation = 'source-over';
  return _tscr;
}

/** simple HUD label (mono, uppercase, tracked) */
export function label(ctx, text, x, y, o = {}) {
  const size = o.size || 18;
  ctx.save();
  ctx.font = fontStr(o.family || F.mono, size, o.weight || 400);
  ctx.letterSpacing = `${(o.track == null ? 0.12 : o.track) * size}px`;
  ctx.textAlign = o.align || 'left';
  ctx.textBaseline = o.baseline || 'alphabetic';
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  ctx.fillStyle = o.color || P.ice;
  ctx.fillText(o.upper === false ? text : text.toUpperCase(), x, y);
  const w = ctx.measureText(o.upper === false ? text : text.toUpperCase()).width;
  ctx.restore();
  return w;
}

/** label with a dark backing plate (legible over imagery) */
export function tag(ctx, text, x, y, o = {}) {
  const size = o.size || 16;
  ctx.save();
  ctx.font = fontStr(o.family || F.mono, size, 400);
  ctx.letterSpacing = `${(o.track == null ? 0.12 : o.track) * size}px`;
  const s = o.upper === false ? text : text.toUpperCase();
  const w = ctx.measureText(s).width;
  const px = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  ctx.fillStyle = o.plate || 'rgba(10,12,14,0.78)';
  ctx.fillRect(px - 8, y - size * 0.95, w + 14, size * 1.4);
  ctx.restore();
  return label(ctx, text, x, y, o);
}

/* ----------------------------------------------------------- HUD shapes */
/** ring with ticks. o: {r, ticks, tickLen, major, majorLen, rot, color, alpha, lw, arcs:[[a0,a1]], dash} */
export function ring(ctx, cx, cy, o) {
  ctx.save();
  ctx.translate(cx, cy); ctx.rotate(o.rot || 0);
  ctx.strokeStyle = o.color || P.ice; ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  ctx.lineWidth = o.lw || 1.5;
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath();
  if (o.arcs) for (const [a0, a1] of o.arcs) { ctx.moveTo(Math.cos(a0) * o.r, Math.sin(a0) * o.r); ctx.arc(0, 0, o.r, a0, a1); }
  else ctx.arc(0, 0, o.r, 0, TAU);
  ctx.stroke();
  ctx.setLineDash([]);
  if (o.ticks) {
    ctx.beginPath();
    const n = o.ticks, inner = o.tickIn !== false;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * TAU;
      const major = o.major && i % o.major === 0;
      const len = major ? (o.majorLen || (o.tickLen || 8) * 2.2) : (o.tickLen || 8);
      const r0 = inner ? o.r - len : o.r, r1 = inner ? o.r : o.r + len;
      ctx.moveTo(Math.cos(a) * r0, Math.sin(a) * r0); ctx.lineTo(Math.cos(a) * r1, Math.sin(a) * r1);
    }
    ctx.lineWidth = o.tlw || 1;
    ctx.stroke();
  }
  if (o.dots) {
    ctx.fillStyle = o.color || P.ice;
    for (let i = 0; i < o.dots; i++) {
      const a = (i / o.dots) * TAU;
      ctx.fillRect(Math.cos(a) * (o.r + (o.dotOff || 14)) - 1.5, Math.sin(a) * (o.r + (o.dotOff || 14)) - 1.5, 3, 3);
    }
  }
  ctx.restore();
}
export function brackets(ctx, x, y, w, h, o = {}) {
  const l = o.len || 28;
  ctx.save();
  ctx.strokeStyle = o.color || P.ice; ctx.lineWidth = o.lw || 2; ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  ctx.beginPath();
  ctx.moveTo(x, y + l); ctx.lineTo(x, y); ctx.lineTo(x + l, y);
  ctx.moveTo(x + w - l, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + l);
  ctx.moveTo(x + w, y + h - l); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - l, y + h);
  ctx.moveTo(x + l, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - l);
  ctx.stroke();
  ctx.restore();
}
export function dotted(ctx, x1, y1, x2, y2, o = {}) {
  const gap = o.gap || 6, sz = o.size || 2;
  const d = Math.hypot(x2 - x1, y2 - y1), n = Math.floor(d / gap);
  const p = o.p == null ? 1 : o.p;
  ctx.save();
  ctx.fillStyle = o.color || P.ice; ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  for (let i = 0; i <= n * p; i++) {
    const k = n ? i / n : 0;
    ctx.fillRect(x1 + (x2 - x1) * k - sz / 2, y1 + (y2 - y1) * k - sz / 2, sz, sz);
  }
  if (o.ends) {
    ctx.strokeStyle = o.color || P.ice; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(x1, y1, 4, 0, TAU); ctx.stroke();
    if (p >= 1) { ctx.beginPath(); ctx.arc(x2, y2, 4, 0, TAU); ctx.fill(); }
  }
  ctx.restore();
}
export function line(ctx, x1, y1, x2, y2, colour, a = 1, lw = 1) {
  ctx.save(); ctx.strokeStyle = colour; ctx.globalAlpha *= a; ctx.lineWidth = lw;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
}
/** precomputed hex grid canvas (white lines on transparent) */
export function hexGridCanvas(w, h, r = 46, lw = 1) {
  const c = makeCanvas(w, h), x = c.getContext('2d');
  x.strokeStyle = '#fff'; x.lineWidth = lw;
  const hw = Math.sqrt(3) * r, vs = 1.5 * r;
  x.beginPath();
  for (let row = -1; row * vs < h + r; row++) {
    for (let col = -1; col * hw < w + hw; col++) {
      const cx = col * hw + (row % 2 ? hw / 2 : 0), cy = row * vs;
      for (let i = 0; i < 3; i++) { // half the edges per hex: neighbours draw the rest (no double strokes)
        const a0 = Math.PI / 6 + (i * Math.PI) / 3, a1 = a0 + Math.PI / 3;
        x.moveTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r);
        x.lineTo(cx + Math.cos(a1) * r, cy + Math.sin(a1) * r);
      }
    }
  }
  x.stroke();
  return c;
}
/** waveform polyline. amp(xNorm) gives amplitude; returns nothing */
export function waveform(ctx, x0, x1, cy, o) {
  const n = o.n || 360;
  const T = o.t || 0;
  ctx.save();
  ctx.strokeStyle = o.color || P.ice; ctx.lineJoin = 'round';
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n;
    const env = Math.sin(Math.PI * u) ** (o.taper || 1.2);
    let v = 0;
    v += Math.sin(u * 23.0 + T * 3.1) * 0.45;
    v += Math.sin(u * 61.0 - T * 5.3 + 1.3) * 0.28;
    v += Math.sin(u * 137.0 + T * 9.7 + 0.4) * 0.16 * (o.detail == null ? 1 : o.detail);
    v += Math.sin(u * 7.0 + T * 0.9 + 2.1) * 0.35;
    if (o.noise) v += (noise1(o.seed || 5, u * 180 + T * 40) - 0.5) * 2 * o.noise;
    const a = (o.amp || 100) * env * (o.ampAt ? o.ampAt(u) : 1);
    pts.push([lerp(x0, x1, u), cy + v * a]);
  }
  const strokeIt = (lw, alpha) => {
    ctx.lineWidth = lw; ctx.globalAlpha = alpha;
    ctx.beginPath();
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.stroke();
  };
  const a = o.alpha == null ? 1 : o.alpha;
  if (o.glow) strokeIt(o.glow, a * 0.12);
  strokeIt((o.lw || 2) * 2.2, a * 0.25);
  strokeIt(o.lw || 2, a);
  if (o.mirror) {
    ctx.globalAlpha = a * 0.25; ctx.lineWidth = 1;
    ctx.beginPath();
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, 2 * cy - y) : ctx.moveTo(x, 2 * cy - y)));
    ctx.stroke();
  }
  ctx.restore();
  return pts;
}
/** faux code columns (prebuilt text, scrolled by t) */
const CODE_TOKENS = ['voice.synth', 'f0=', 'formant[', 'vibrato', 'emotion=NULL', 'loop', 'return', '0x', 'buf.push', 'if(', 'phoneme', '/ka/', '/i/', 'sample', 'gain', 'pitch', 'ENV', 'adsr', 'feel()', 'void', 'null', '==', '!=', 'await', 'tts', 'mel', 'fft', 'z-1', 'model', 'loss', 'grad', '機械', '声', 'Claude', '//', '{', '}', ';'];
export function codeColumns(ctx, t, o) {
  const size = o.size || 14, colW = o.colW || 150, lh = size * 1.45;
  const cols = Math.ceil((o.w || W) / colW);
  ctx.save();
  ctx.font = fontStr(F.mono, size);
  ctx.fillStyle = o.color || P.ice;
  ctx.globalAlpha *= o.alpha == null ? 0.15 : o.alpha;
  const rows = Math.ceil((o.h || H) / lh) + 2;
  for (let c = 0; c < cols; c++) {
    const r = rng('code', c);
    const speed = 30 + r() * 90;
    const off = (t * speed * (o.speed == null ? 1 : o.speed)) + r() * 1000;
    const first = Math.floor(off / lh);
    for (let i = 0; i < rows; i++) {
      const rowId = first + i;
      const rr = rng('code', c, rowId);
      if (rr() < 0.18) continue;
      let s = '';
      const nTok = 1 + Math.floor(rr() * 3);
      for (let k = 0; k < nTok; k++) s += CODE_TOKENS[Math.floor(rr() * CODE_TOKENS.length)] + (rr() < 0.5 ? (rr() * 255 | 0).toString(16) : ' ');
      const y = (o.y || 0) + i * lh - (off % lh);
      ctx.fillText(s.slice(0, 18), (o.x || 0) + c * colW, y);
    }
  }
  ctx.restore();
}
/** particles: kind 'pixel' (static bits), 'dust' (motes), 'ember' (rising orange) */
export function particles(ctx, t, o) {
  const n = o.n || 80;
  const x0 = o.x0 || 0, x1 = o.x1 || W, y0 = o.y0 || 0, y1 = o.y1 || H;
  ctx.save();
  for (let i = 0; i < n; i++) {
    const r = rng(o.seed || 'pt', i);
    const life = (o.life || 6) * (0.6 + r() * 0.8);
    const ph = r() * life;
    const age = ((t + ph) % life), gen = Math.floor((t + ph) / life);
    const rg = rng(o.seed || 'pt', i, gen);
    const k = age / life;
    let x = lerp(x0, x1, rg()), y;
    const sz = (o.size || 2) * (0.5 + rg() * 1.2);
    let a = Math.sin(Math.PI * k);
    if (o.kind === 'pixel') {
      y = lerp(y0, y1, rg());
      a = rnd(o.seed, i, bucket(t, 12)) < 0.6 ? a : 0.15 * a;
      ctx.fillStyle = o.color || P.ice;
      ctx.globalAlpha = a * (o.alpha || 0.6);
      const s = Math.round(sz + 1);
      ctx.fillRect(Math.round(x), Math.round(y), s, s);
    } else {
      const rise = (o.rise == null ? 120 : o.rise) * (0.6 + rg() * 0.8);
      y = lerp(y1, y0, rg() * (o.spawnSpread == null ? 1 : o.spawnSpread)) - rise * age;
      x += Math.sin(age * (0.6 + rg()) + rg() * 6) * (o.sway || 18);
      if (o.kind === 'ember') a *= 0.6 + 0.4 * Math.sin(t * (6 + rg() * 8) + i);
      ctx.globalAlpha = clamp(a * (o.alpha || 0.7));
      ctx.fillStyle = o.color || P.orangeL;
      ctx.beginPath(); ctx.arc(x, y, sz, 0, TAU); ctx.fill();
      if (o.glow && sz > 1.2) {
        ctx.globalAlpha = clamp(a * (o.alpha || 0.7) * 0.18);
        ctx.beginPath(); ctx.arc(x, y, sz * 3.2, 0, TAU); ctx.fill();
      }
    }
  }
  ctx.restore();
}
/** radial glow */
export function glow(ctx, x, y, r, colour, a = 1, op = 'source-over') {
  if (a <= 0.003) return;
  ctx.save();
  ctx.globalCompositeOperation = op;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(colour, a)); g.addColorStop(0.45, rgba(colour, a * 0.4)); g.addColorStop(1, rgba(colour, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  ctx.restore();
}
/** barcode */
export function barcode(ctx, x, y, w, h, seed, colour, a = 1) {
  const r = rng('bar', seed);
  ctx.save(); ctx.fillStyle = colour; ctx.globalAlpha *= a;
  let xx = x;
  while (xx < x + w) {
    const bw = 1 + Math.floor(r() * 4);
    if (r() < 0.55) ctx.fillRect(xx, y, Math.min(bw, x + w - xx), h);
    xx += bw + 1 + Math.floor(r() * 2);
  }
  ctx.restore();
}
/** a rubber-stamp: text in a double rectangle, with eroded ink */
export function stamp(ctx, lines, x, y, o) {
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot || 0);
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  const sz = o.size || 40;
  ctx.font = fontStr(o.family || F.mono, sz, o.weight || 400);
  ctx.letterSpacing = `${(o.track || 0.15) * sz}px`;
  const widths = lines.map((l) => ctx.measureText(l).width);
  const w = Math.max(...widths) + sz * 1.2, h = lines.length * sz * 1.2 + sz * 0.6;
  ctx.strokeStyle = o.color; ctx.fillStyle = o.color;
  ctx.lineWidth = o.lw || 4; ctx.strokeRect(-w / 2, -h / 2, w, h);
  ctx.lineWidth = 1.5; ctx.strokeRect(-w / 2 + 7, -h / 2 + 7, w - 14, h - 14);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  lines.forEach((l, i) => {
    const s = i === 0 ? sz : sz * (o.sub || 0.55);
    ctx.font = fontStr(i === 0 ? (o.family || F.mono) : (o.subFamily || o.family || F.mono), s, o.weight || 400);
    ctx.letterSpacing = `${(o.track || 0.15) * s}px`;
    const yy = -h / 2 + sz * 0.3 + (i + 0.5) * sz * 1.2 - (i > 0 ? sz * 0.15 : 0);
    ctx.fillText(l, sz * (o.track || 0.15) * 0.5, yy);
  });
  // erosion: punch seeded holes
  ctx.globalCompositeOperation = 'destination-out';
  const r = rng('stamp', o.seed || 1);
  for (let i = 0; i < (o.holes || 160); i++) {
    const hx = (r() - 0.5) * w, hy = (r() - 0.5) * h, hr = 0.6 + r() * 2.4;
    ctx.globalAlpha = 0.5 + r() * 0.5;
    ctx.beginPath(); ctx.arc(hx, hy, hr, 0, TAU); ctx.fill();
  }
  ctx.restore();
  return { w, h };
}

/* --------------------------------------------------------------- post fx */
let grainTiles = null, scanCanvas = null, vignetteCanvas = null, vignetteWarm = null;
export function buildPost() {
  grainTiles = [];
  for (let k = 0; k < 6; k++) {
    const s = 256, c = makeCanvas(s, s), x = c.getContext('2d');
    const id = x.createImageData(s, s), r = rng('grain', k);
    for (let i = 0; i < s * s; i++) {
      const v = r() * 255;
      id.data[i * 4] = v; id.data[i * 4 + 1] = v; id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255;
    }
    x.putImageData(id, 0, 0);
    grainTiles.push(c);
  }
  scanCanvas = makeCanvas(W, H);
  const sx = scanCanvas.getContext('2d');
  sx.fillStyle = '#000';
  for (let y = 0; y < H; y += 2) sx.fillRect(0, y, W, 1);
  vignetteCanvas = makeCanvas(W, H);
  const vx = vignetteCanvas.getContext('2d');
  const g = vx.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 1.02);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.55, 'rgba(0,0,0,0.28)'); g.addColorStop(1, 'rgba(0,0,0,0.85)');
  vx.fillStyle = g; vx.fillRect(0, 0, W, H);
}
/** animated film grain: one of 6 seeded tiles, tiled with drawImage (no CanvasPattern: patterns created lazily
 *  rasterise slightly differently on first use, which would break bit-exact re-renders) */
export function grain(ctx, t, amount = 0.05) {
  if (!grainTiles) return;
  const b = bucket(t, 24);
  const tile = grainTiles[b % grainTiles.length];
  const r = rng('gr', b);
  const ox = -Math.floor(r() * 256), oy = -Math.floor(r() * 256);
  ctx.save();
  ctx.globalCompositeOperation = 'overlay';
  ctx.globalAlpha = amount * 2.2;
  for (let y = oy; y < H; y += 256) for (let x = ox; x < W; x += 256) ctx.drawImage(tile, x, y);
  ctx.restore();
}
export function scanlines(ctx, a = 0.06) {
  if (!scanCanvas || a <= 0) return;
  blit(ctx, scanCanvas, 0, 0, W, H, a);
}
export function vignette(ctx, a = 1, colour = null) {
  if (!vignetteCanvas || a <= 0) return;
  if (colour) {
    ctx.save();
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 1.0);
    g.addColorStop(0, rgba(colour, 0)); g.addColorStop(0.6, rgba(colour, 0.3 * a)); g.addColorStop(1, rgba(colour, 0.9 * a));
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.restore();
    return;
  }
  blit(ctx, vignetteCanvas, 0, 0, W, H, a);
}

/* ---------------------------------------------------------------- glitch */
let gbuf = null, gR = null, gGB = null;
function ensureG() {
  if (!gbuf) { gbuf = makeCanvas(W, H); gR = makeCanvas(W, H); gGB = makeCanvas(W, H); }
}
/** copy current frame */
export function snapshot(ctx) {
  ensureG();
  const x = gbuf.getContext('2d');
  x.globalCompositeOperation = 'copy'; x.drawImage(ctx.canvas, 0, 0);
  x.globalCompositeOperation = 'source-over';
  return gbuf;
}
/** horizontal slice displacement of the whole frame */
export function sliceGlitch(ctx, intensity, seed, o = {}) {
  if (intensity <= 0.01) return;
  const src = snapshot(ctx);
  const r = rng('sg', seed);
  const n = Math.floor(4 + intensity * (o.n || 14));
  const y0 = o.y0 || 0, y1 = o.y1 || H;
  for (let i = 0; i < n; i++) {
    const y = y0 + Math.floor(r() * (y1 - y0));
    const h = 2 + Math.floor(r() * r() * (o.maxH || 90));
    const dx = (r() - 0.5) * 2 * intensity * (o.amp || 120);
    ctx.drawImage(src, 0, y, W, h, dx, y, W, h);
    if (r() < 0.25 * intensity) {
      ctx.save(); ctx.globalAlpha = 0.12 * intensity; ctx.fillStyle = r() < 0.5 ? P.paper : P.cyan;
      ctx.fillRect(0, y, W, h); ctx.restore();
    }
  }
}
/** full-frame chromatic split */
export function rgbSplit(ctx, dx) {
  if (Math.abs(dx) < 0.5) return;
  const src = snapshot(ctx);
  const xr = gR.getContext('2d'), xg = gGB.getContext('2d');
  xr.globalCompositeOperation = 'copy'; xr.drawImage(src, 0, 0);
  xr.globalCompositeOperation = 'multiply'; xr.fillStyle = '#ff0000'; xr.fillRect(0, 0, W, H);
  xg.globalCompositeOperation = 'copy'; xg.drawImage(src, 0, 0);
  xg.globalCompositeOperation = 'multiply'; xg.fillStyle = '#00ffff'; xg.fillRect(0, 0, W, H);
  ctx.save();
  ctx.globalCompositeOperation = 'copy'; ctx.drawImage(gGB, dx, 0);
  ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(gR, -dx, 0);
  ctx.restore();
}
/** shake offset (decaying) */
export function shake(t, t0, amp, dur, seed) {
  const dt = t - t0;
  if (dt < 0 || dt > dur) return [0, 0];
  const k = 1 - dt / dur;
  const r = rng('shake', seed, bucket(t, 30));
  return [(r() - 0.5) * 2 * amp * k, (r() - 0.5) * 2 * amp * k];
}
