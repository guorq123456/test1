// env_demo.js — one-frame viewer for js/env.js.
//   env_demo.html?env=circuitCity&t=12.5&tint=0.3&energy=0.8[&seed=..&frame=0|1&style=cold|warm&alpha=1&fit=1&live=1&cpu=1]
//   cpu=1 → willReadFrequently canvases, like engine.js render mode; live=1 → animate from t
// window.DEMO = { ready: Promise, render(t, overrides?) → ms, envs, params }
import * as env from '../js/env.js';
import { setCanvasOptions } from '../js/fx.js';

const q = new URLSearchParams(location.search);
const num = (k, d) => (q.has(k) && q.get(k) !== '' && Number.isFinite(+q.get(k)) ? +q.get(k) : d);
const params = {
  env: q.get('env') || 'circuitCity',
  t: num('t', 0), tint: num('tint', 0), energy: num('energy', 0.3), alpha: num('alpha', 1),
  seed: q.has('seed') ? q.get('seed') : undefined,
  frame: num('frame', 1), style: q.get('style') || null, live: num('live', 0),
};
if (num('fit', 0)) document.body.classList.add('fit');
const ENVS = ['circuitCity', 'hallOfVoices', 'lightTunnel', 'orb', 'monitors', 'alarmField', 'cockpitFrame'];
if (num('cpu', 0) === 1) setCanvasOptions({ willReadFrequently: true }); // same as engine.js render mode
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', { willReadFrequently: num('cpu', 0) === 1 });

async function init() {
  const faces = ['14px "Share Tech Mono"'];
  await Promise.all([env.loadEnvAssets(new URL('../assets/', import.meta.url).href), ...faces.map((f) => document.fonts.load(f))]);
  await document.fonts.ready;
}

function render(t = params.t, o = {}) {
  const P = { ...params, ...o };
  const t0 = performance.now();
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 1920, 1080);
  const opts = { tint: P.tint, energy: P.energy, alpha: P.alpha, cam: P.cam };
  if (P.bloom !== undefined) opts.bloom = P.bloom;
  if (P._skip) opts._skip = P._skip;
  if (P.seed != null) opts.seed = P.seed;
  if (P.env !== 'cockpitFrame') env[P.env](ctx, t, opts);
  ctx.getImageData(0, 0, 1, 1); // flush deferred raster work so the timing is honest
  const tEnv = performance.now() - t0;
  if (P.frame || P.env === 'cockpitFrame') env.cockpitFrame(ctx, t, { style: P.style || (P.tint > 0.5 ? 'warm' : 'cold'), intensity: 1, draw: P.draw == null ? 1 : P.draw });
  const ms = performance.now() - t0;
  document.getElementById('info').textContent = `${P.env} t=${t.toFixed(2)} tint=${P.tint} energy=${P.energy} · env ${tEnv.toFixed(1)} ms · total ${ms.toFixed(1)} ms`;
  return { ms, env: tEnv };
}

const ready = init().then(() => { render(); return true; });
window.DEMO = { ready, render, envs: ENVS, params, env };
if (params.live) ready.then(() => { const s = performance.now(); const loop = () => { render(params.t + (performance.now() - s) / 1000); requestAnimationFrame(loop); }; loop(); });
