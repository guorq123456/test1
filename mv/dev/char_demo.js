// char_demo.js — preset harness for js/charfx.js.  ?preset=all|breathing|sway|float|rim|hologram|ghosts|crowd|monitor&t=…
// window.DEMO = { ready: Promise, render(t), bench(n), preset, opts }
import * as fx from '../js/fx.js';
import { drawCharacter, drawVoiceCrowd, drawMonitorFace, cameraShot, applyCamera, rimColour, prepareCharacter } from '../js/charfx.js';

const q = new URLSearchParams(location.search);
const PRESET = q.get('preset') || 'all';
const CPU = q.get('cpu') !== '0';                 // default: CPU raster like the MV's render mode
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: CPU });
fx.setCanvasOptions(CPU ? { willReadFrequently: true } : {});
const { W, H, P, TAU, clamp, rnd, bucket } = fx;
const A = {};

function loadImage(src) {
  return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(src)); im.src = src; });
}
async function load() {
  await Promise.all([document.fonts.load('400 32px "Share Tech Mono"', 'CHARFX 0123'), document.fonts.load('400 32px "DotGothic16"', 'BOOT'),
    document.fonts.load('700 32px "Zen Old Mincho"', '機械の声')]);
  await document.fonts.ready;
  const names = ['char_full', 'char_full_1080', 'char_mono', 'char_silhouette', 'char_face', 'char_bust', 'char_book'];
  await Promise.all(names.map(async (n) => { A[n] = await loadImage(`../assets/${n}.png`); }));
  prepareCharacter({ image: A.char_full, imageMono: A.char_mono, h: 1000 });   // warm caches like MV.ready would
}

// seeded "lyric onset" energy: decaying pulses on a 0.5 s grid
function energyAt(t) {
  let e = 0.25;
  for (let k = 0; k < 4; k++) {
    const b = Math.floor(t / 0.5) - k, tb = b * 0.5, dt = t - tb;
    if (rnd('beat', b) < 0.55) e += 0.75 * Math.exp(-dt / 0.35);
  }
  return clamp(e);
}

const BASE = { breathing: false, sway: false, float: false, rim: false, bloom: 0, hologram: 0, ghosts: 0, glitch: 0, mono: 0, energy: 0.5, tint: 1 };
let charOpts = function (t, preset) {
  const o = { image: A.char_full, imageMono: A.char_mono, x: W / 2, y: 1050, h: 1000, seed: 'claude' };
  switch (preset) {
    case 'breathing': return Object.assign(o, BASE, { breathing: true });
    case 'sway': return Object.assign(o, BASE, { sway: true });
    case 'float': return Object.assign(o, BASE, { float: true });
    case 'rim': return Object.assign(o, BASE, { breathing: true, sway: true, float: true, rim: true, bloom: 0.35, energy: energyAt(t), tint: 0.5 + 0.5 * Math.sin(TAU * t / 8) });
    case 'hologram': return Object.assign(o, BASE, { breathing: true, sway: true, float: true, rim: true, hologram: 1, tint: 0.1, energy: energyAt(t), mono: 0.6 });
    case 'ghosts': return Object.assign(o, BASE, { breathing: true, sway: true, float: true, rim: true, bloom: 0.3, ghosts: 1, cutAge: t % 2, energy: energyAt(t), tint: 0.8 });
    case 'crowd': return Object.assign(o, { breathing: true, sway: true, float: true, rim: true, bloom: 0.35, tint: 0.15, energy: energyAt(t), mono: 0.7, h: 760, y: 1035 });
    case 'all': default:
      return Object.assign(o, { breathing: true, sway: true, float: true, rim: true, bloom: 0.5, hologram: 0.35, ghosts: 0.7, cutAge: t % 2.5,
        glitch: 0.3, mono: 0.3, energy: energyAt(t), tint: 0.55 });
  }
}

function floorGlow(col) {
  const g = ctx.createRadialGradient(W / 2, 1040, 20, W / 2, 1040, 700);
  g.addColorStop(0, fx.rgba(col, 0.16)); g.addColorStop(1, fx.rgba(col, 0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function crowdPositions() {
  // two rows per side receding toward a vanishing point above the hero's head (hall of voices)
  const pos = [], vx = W / 2, vy = 430;
  for (let side of [-1, 1]) for (let k = 0; k < 4; k++) {
    const depth = 0.15 + k * 0.22;                 // 0 near .. 1 far
    const z = 1 / (1 + depth * 2.2);               // perspective scale
    const xw = side * (520 + 140 * (k % 2)) ;      // world x
    pos.push({ x: vx + xw * z, y: vy + (1000 - vy) * z, h: 900 * z, depth });
  }
  return pos;
}
function label(text) {
  ctx.save();
  ctx.font = '400 20px "Share Tech Mono"'; ctx.fillStyle = fx.rgba(P.gold, 0.85);
  ctx.fillText(text, 40, 50);
  ctx.restore();
}

function render(t) {
  fx.reset(ctx);
  ctx.fillStyle = P.ink; ctx.fillRect(0, 0, W, H);
  const o = charOpts(t, PRESET);
  if (PRESET === 'monitor') {
    renderMonitors(t);
  } else if (PRESET === 'crowd' || PRESET === 'all') {
    const cam = cameraShot(t, { from: { scale: 1.0, y: 0 }, to: { scale: 1.08, y: -20, rotate: 0.01 }, t0: 0, t1: 8, ease: 'inOutSine', drift: 6 });
    ctx.save(); applyCamera(ctx, cam);
    floorGlow(rimColour(o.tint));
    drawVoiceCrowd(ctx, t, { silhouette: A.char_silhouette, positions: crowdPositions(), color: rimColour(Math.min(o.tint, 0.4)).map(Math.round), blur: 0.5, alpha: 0.9 });
    drawCharacter(ctx, t, o);
    ctx.restore();
    if (PRESET === 'all') renderMonitors(t, true);
  } else {
    floorGlow(rimColour(o.tint));
    drawCharacter(ctx, t, o);
  }
  label(`charfx · preset=${PRESET} · t=${t.toFixed(2)}`);
}

function renderMonitors(t, small) {
  const mons = small
    ? [{ c: [1560, 300], w: 300, h: 230, yaw: 0.5, img: A.char_face, r: null }]
    : [
      { c: [560, 380], w: 560, h: 420, yaw: 0.45 * Math.sin(TAU * t / 9), img: A.char_face, r: null, hero: true },
      { c: [1300, 300], w: 360, h: 270, yaw: -0.6, pitch: 0.15, img: A.char_book, r: null },
      { c: [1350, 760], w: 420, h: 300, yaw: -0.3 + 0.2 * Math.sin(TAU * t / 7), pitch: -0.2, img: A.char_bust, r: null },
      { c: [520, 860], w: 300, h: 160, yaw: 0.7, img: A.char_face, r: [150, 200, 260, 120] },
    ];
  mons.forEach((m, i) => {
    const quad = projQuad(m.c[0], m.c[1] + 8 * Math.sin(TAU * t / 5 + i), m.w, m.h, m.yaw, m.pitch || 0, (i % 2 ? -1 : 1) * 0.03 * Math.sin(TAU * t / 6 + i));
    // cable to the top edge
    ctx.save(); ctx.strokeStyle = fx.rgba(P.steel, 0.4); ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo((quad[0][0] + quad[1][0]) / 2, (quad[0][1] + quad[1][1]) / 2); ctx.lineTo((quad[0][0] + quad[1][0]) / 2, 0); ctx.stroke();
    // bezel
    ctx.beginPath(); quad.forEach((p, k) => (k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
    ctx.lineWidth = 10; ctx.strokeStyle = '#2A1F19'; ctx.stroke(); ctx.lineWidth = 1.2; ctx.strokeStyle = fx.rgba(P.gold, 0.7); ctx.stroke();
    ctx.restore();
    drawMonitorFace(ctx, quad, m.img, m.r, { t, seed: 'm' + i, scanlines: 0.6, glitch: i === 0 ? 0.6 : 0.25, tint: i === 2 ? P.cyan : null, glow: 0.7 });
  });
}
// a w×h rectangle centred at (cx,cy) rotated by yaw (about y) / pitch (about x) / roll, perspective focal 1400
function projQuad(cx, cy, w, h, yaw, pitch, roll) {
  const f = 1400, pts = [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
  return pts.map(([x, y]) => {
    let X = x * Math.cos(roll) - y * Math.sin(roll), Y = x * Math.sin(roll) + y * Math.cos(roll), Z = 0;
    let X2 = X * Math.cos(yaw) + Z * Math.sin(yaw), Z2 = -X * Math.sin(yaw) + Z * Math.cos(yaw);
    let Y2 = Y * Math.cos(pitch) - Z2 * Math.sin(pitch), Z3 = Y * Math.sin(pitch) + Z2 * Math.cos(pitch);
    const s = f / (f + Z3);
    return [cx + X2 * s, cy + Y2 * s];
  });
}

/** ms per drawCharacter call (caches warmed first). opts preset defaults to 'all' effects on. */
function bench(n = 30, preset = 'all', t0 = 10, over = null) {
  const co = (t, p) => Object.assign(charOpts(t, p), over || {});
  const o0 = co(t0, preset); drawCharacter(ctx, t0, o0); drawCharacter(ctx, t0 + 0.5, co(t0 + 0.5, preset));
  const ts = [];
  for (let i = 0; i < n; i++) {
    const t = t0 + i / 30, o = co(t, preset);
    const a = performance.now(); drawCharacter(ctx, t, o); ctx.getImageData(0, 0, 1, 1); ts.push(performance.now() - a);
  }
  ts.sort((a, b) => a - b);
  return { n, mean: ts.reduce((a, b) => a + b, 0) / n, median: ts[n >> 1], p90: ts[Math.floor(n * 0.9)], max: ts[n - 1] };
}

/** draw only the character (ink bg) with preset opts + overrides — for tests (dolly continuity, cache build timing) */
function draw(t, over = {}, preset = 'sway') {
  fx.reset(ctx); ctx.fillStyle = P.ink; ctx.fillRect(0, 0, W, H);
  const a = performance.now();
  drawCharacter(ctx, t, Object.assign(charOpts(t, preset), over));
  ctx.getImageData(0, 0, 1, 1);
  return performance.now() - a;
}
// ?glow=nearest|bilinear overrides opts.glowFilter for every preset
const GLOW = q.get('glow');
if (GLOW) { const co = charOpts; charOpts = (t, p) => Object.assign(co(t, p), { glowFilter: GLOW }); }
window.DEMO = { preset: PRESET, render, bench, draw, get charOpts() { return charOpts; }, ready: load().then(() => { const t = parseFloat(q.get('t') || '0'); render(t); return true; }) };
