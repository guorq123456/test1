// scenes.js — v2 (STORYBOARD_V2): 3D environments (env.js) + animated Claude (charfx.js) + tategaki typography.
// One renderer per section id. Each renderer draws the "world" (environment + character + world-space HUD) and
// returns { text(ctx) } for the typography, which finishFrame() draws ABOVE the blackouts and the cockpit frame,
// so lyrics stay readable through section cuts. Everything is a pure function of S.t (seeded randomness only).
import * as fx from './fx.js';
import * as env from './env.js';
import * as cf from './charfx.js';

const { W, H, P, F, clamp, lerp, inv, smooth, ease, rng, rnd, bucket, mix, rgba, blit, TAU } = fx;

let A = null, TL = null, LINES = null, SECS = null, warmth = null, IM = null;
const K = {};

/* =========================================================== timing tables */
// section-cut blackouts: black from a → b, then the world fades back in over f seconds.
// The cockpit frame re-draws itself after every b. `glitch` adds a glitch burst when the image returns.
const BLACK = [];
function buildBlackouts() {
  const add = (a, b, f, o = {}) => BLACK.push(Object.assign({ a, b, f }, o));
  add(-10, 0.8, 0, { frameOnly: true });           // boot: frame draws in after the CRT turn-on
  add(23.4, 24.2, 0.45);                            // title: hall → circuit city
  add(42.62, 43.085, 0.3);                          // → verse2
  add(54.5, 54.734, 0.12, { glitch: 0.5 });         // verse2: archive → monitors
  add(64.47, 64.717, 0.2, { glitch: 0.4 });         // → verse2b
  add(85.35, 86.236, 0.6);                          // eyelids close → quotes
  add(108.7, 109.707, 0.9);                         // → chorus1
  add(152.76, 152.998, 0.05, { glitch: 0.9 });      // → bridge (hard)
  for (const i of [37, 38, 39, 40, 41]) add(LINES[i].t - 0.2, LINES[i].t, 0.05, { glitch: 0.75 });
  add(170.15, 176.5, 0.9);                          // line 42 over black → diagnostics
  add(183.85, 184.05, 0.25, { glitch: 0.4 });       // monitors → circuit city
  add(195.4, 196.029, 0.7);                         // → verse3
  add(237.86, 238.064, 0.0, { glitch: 0.6 });       // → chorus2 flood
  add(260.95, 261.839, 0.8);                        // → prayer
  add(304.62, 305.042, 0.35);                       // → build
  add(325.62, 326.182, 0.2, { glitch: 0.6 });       // → final_a
  add(346.82, 347.058, 0.1, { glitch: 0.5 });       // → final_b
  add(373.45, 374.2, 0.9);                          // poem fades → the hall, one last time
}
export function frameState(t) {
  let black = 0, lastB = 0, glitchAt = null;
  for (const e of BLACK) {
    if (t >= e.b) { lastB = e.b; if (e.glitch) glitchAt = e; }
    if (e.frameOnly) continue;
    if (t >= e.a - 0.066 && t < e.a) black = Math.max(black, (t - (e.a - 0.066)) / 0.066);
    else if (t >= e.a && t < e.b) black = 1;
    else if (e.f > 0 && t >= e.b && t < e.b + e.f) black = Math.max(black, 1 - ease.inOutSine((t - e.b) / e.f));
  }
  const inBlack = BLACK.some((e) => !e.frameOnly && t >= e.a && t < e.b);
  const draw = inBlack ? 0 : clamp((t - lastB) / 1.1);
  return { black, draw, cutAge: t - lastB, glitchAt };
}

// lyric-onset energy: spikes at every line onset and section start, decays over ~1.2 s, floor 0.2
let ONSETS = [];
export function energyAt(t) {
  let e = 0;
  for (let i = ONSETS.length - 1; i >= 0; i--) {
    const d = t - ONSETS[i];
    if (d < 0) continue;
    if (d > 5) break;
    e = Math.max(e, clamp(d / 0.05) * Math.exp(-d / 1.2));
  }
  return 0.2 + 0.8 * e;
}

/* =========================================================== setup */
export function prepareScenes(o) {
  ({ A, TL, LINES, SECS, warmth } = o);
  IM = o.imgs;
  ONSETS = [...new Set([...LINES.map((l) => l.t), ...SECS.map((s) => s.start)])].sort((a, b) => a - b);
  buildBlackouts();
  env.setEnvAssets({ silhouette: IM.char_silhouette, face: IM.char_face, book: IM.char_book, bust: IM.char_bust, full: IM.char_full });
  // character caches for the two heights used (full body at ≤1000, close-ups at the native 1983)
  for (const h of [1000, 1983]) cf.prepareCharacter({ image: IM.char_full, imageMono: IM.char_mono, h, cacheH: h });
  // soft sprites
  K.halo = (() => {
    const c = fx.makeCanvas(256, 256), x = c.getContext('2d');
    const g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
    g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(0.55, 'rgba(0,0,0,0.5)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g; x.fillRect(0, 0, 256, 256); return c;
  })();
  K.plate = (() => {
    const c = fx.makeCanvas(320, 160), x = c.getContext('2d');
    x.filter = 'blur(22px)'; x.fillStyle = '#000'; x.fillRect(48, 48, 224, 64); x.filter = 'none'; return c;
  })();
  K.dissolve = fx.makeCanvas(A.w, A.h);
  K.dissolveData = K.dissolve.getContext('2d').createImageData(A.w, A.h);
  // pre-warm environment caches (sprites per tint level, pooled layers) so first frames of a shot don't spike
  const scr = fx.makeCanvas(W, H), sx = scr.getContext('2d');
  const tints = [0, 0.1, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 1];
  for (const tn of tints) env.hallOfVoices(sx, 5, { tint: tn, energy: 0.5, crowd: 0.4 });
  for (const tn of [0, 1]) env.alarmField(sx, 5, { tint: tn, energy: 0.5, crowd: 0.5 });
  for (const tn of [0, 0.1, 1]) env.monitors(sx, 5, { tint: tn, energy: 0.5 });
  env.circuitCity(sx, 5, { tint: 0, energy: 0.5 }); env.lightTunnel(sx, 5, { tint: 0, energy: 0.5 }); env.orb(sx, 5, { tint: 0.9 });
}

/* =========================================================== small helpers */
const colourMix = (w) => smooth(0.3, 0.9, w);
const txtCol = (w) => rgba(mix(P.ice, P.paper, smooth(0.08, 0.45, w)));
function fill(c, colour, a = 1) { c.save(); c.globalAlpha = a; c.fillStyle = typeof colour === 'string' ? colour : rgba(colour); c.fillRect(0, 0, W, H); c.restore(); }
function activeLine(t, list) { for (const i of list) if (t >= LINES[i].t && t < LINES[i].end) return i; return -1; }
function lineAlpha(t, t0, t1, fi = 0.3, fo = 0.3) { return smooth(t0, t0 + fi, t) * (1 - smooth(t1 - fo, t1, t)); }
function fmt(t) { t = Math.max(0, t); const m = Math.floor(t / 60), s = Math.floor(t % 60), cs = Math.floor((t * 100) % 100); return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(cs).padStart(2, '0')}`; }
function eyelids(c, k) { if (k <= 0.001) return; const hh = H * 0.5 * k; c.save(); c.fillStyle = '#000'; c.fillRect(0, 0, W, hh); c.fillRect(0, H - hh, W, hh); c.restore(); }
function indexTag(c, i, x, y, colour, a) {
  if (a <= 0.01) return;
  c.save(); c.globalAlpha = a;
  fx.label(c, `${String(i + 1).padStart(3, '0')} / 093`, x, y, { size: 14, color: colour, track: 0.2 });
  c.fillStyle = colour; c.globalAlpha = a * 0.6; c.fillRect(x + 118, y - 5, 48, 1);
  c.restore();
}
/** slow hand-held parallax vector for scattered text (px at depth 1) */
function par(t, seed, amp = 34) {
  return { x: (fx.noise1(seed + 'px', t * 0.21) - 0.5) * 2 * amp, y: (fx.noise1(seed + 'py', t * 0.17 + 3) - 0.5) * 2 * amp * 0.5 };
}
/** soft dark backing plate behind text (x0..x1, y0..y1 = the text box) */
function plate(c, x0, y0, x1, y1, a, col = null) {
  if (a <= 0.01) return;
  const pw = (x1 - x0) * 0.24 + 70, ph = (y1 - y0) * 0.5 + 46;
  c.save(); c.globalAlpha = clamp(a);
  if (col) { // tinted plate (paper on light backgrounds)
    c.globalCompositeOperation = 'source-over';
  }
  c.drawImage(K.plate, x0 - pw, y0 - ph, x1 - x0 + pw * 2, y1 - y0 + ph * 2);
  c.restore();
}
/** dark halo + contact shadow behind a figure so she never drowns in a bright environment */
function halo(c, x, yFeet, h, a) {
  if (a <= 0.01) return;
  c.save(); c.globalAlpha = clamp(a);
  c.drawImage(K.halo, x - h * 0.42, yFeet - h * 1.02, h * 0.84, h * 1.06);
  c.globalAlpha = clamp(a * 1.1);
  c.drawImage(K.halo, x - h * 0.3, yFeet - h * 0.05, h * 0.6, h * 0.1);
  c.restore();
}

/* ---------------------------------------------------------------- Claude */
/** draw Claude with charfx. o: {x, y (feet), h, cam, mono, tint, holo, rim, bloom, ghosts, glitch, alpha, sway, halo} */
function claude(S, o) {
  const c = S.ctx;
  const big = o.h > 1100;
  c.save();
  if (o.cam) cf.applyCamera(c, o.cam);
  halo(c, o.x, o.y, Math.min(o.h, 1300), (o.halo == null ? 0.55 : o.halo) * (o.alpha == null ? 1 : o.alpha));
  const bb = cf.drawCharacter(c, S.t, {
    image: IM.char_full, imageMono: IM.char_mono, x: o.x, y: o.y, h: o.h, cacheH: big ? 1983 : 1000,
    energy: S.energy, tint: o.tint == null ? S.w : o.tint, mono: o.mono || 0, hologram: o.holo || 0,
    rim: o.rim == null ? true : o.rim, bloom: o.bloom == null ? 0.3 : o.bloom, ghosts: o.ghosts || 0, cutAge: S.cutAge,
    glitch: o.glitch || 0, alpha: o.alpha == null ? 1 : o.alpha, sway: o.sway == null ? true : o.sway,
    breathing: true, float: o.float == null ? true : o.float, seed: 'claude',
  });
  c.restore();
  return bb;
}
/** a w×h rectangle centred at (cx,cy) rotated by yaw/pitch/roll, perspective focal 1400 → quad */
function projQuad(cx, cy, w, h, yaw, pitch, roll) {
  const f = 1400, pts = [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
  return pts.map(([x, y]) => {
    const X = x * Math.cos(roll) - y * Math.sin(roll), Y = x * Math.sin(roll) + y * Math.cos(roll);
    const X2 = X * Math.cos(yaw), Z2 = -X * Math.sin(yaw);
    const Y2 = Y * Math.cos(pitch) - Z2 * Math.sin(pitch), Z3 = Y * Math.sin(pitch) + Z2 * Math.cos(pitch);
    const s = f / (f + Z3);
    return [cx + X2 * s, cy + Y2 * s];
  });
}
/** a hanging CRT monitor (cable + bezel + perspective screen) */
function hangMonitor(S, m) {
  const c = S.ctx, t = S.t;
  const q = projQuad(m.x, m.y + 8 * Math.sin(TAU * t / 5 + (m.ph || 0)), m.w, m.h, m.yaw || 0, m.pitch || 0, 0.03 * Math.sin(TAU * t / 6 + (m.ph || 0)));
  const a = m.alpha == null ? 1 : m.alpha;
  if (a <= 0.01) return q;
  c.save(); c.globalAlpha = a;
  c.strokeStyle = rgba(m.line || P.steel, 0.45); c.lineWidth = 1.5;
  const tx = (q[0][0] + q[1][0]) / 2, ty = (q[0][1] + q[1][1]) / 2;
  c.beginPath(); c.moveTo(tx - 30, ty); c.lineTo(tx - 30, -10); c.moveTo(tx + 30, ty); c.lineTo(tx + 30, -10); c.stroke();
  c.beginPath(); q.forEach((p, k) => (k ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]))); c.closePath();
  c.lineWidth = 12; c.strokeStyle = '#15100C'; c.stroke(); c.lineWidth = 1.4; c.strokeStyle = rgba(m.bezel || P.gold, 0.8); c.stroke();
  c.restore();
  cf.drawMonitorFace(c, q, m.img, m.src || null, { t, seed: m.seed || 'hm', scanlines: 0.6, glitch: m.glitch || 0.2, tint: m.tint || null, glow: 0.7, alpha: a });
  return q;
}

/* =========================================================== typography */
const HINTS = {
  8: 'これが「永久に残す」\nということなのか、と', 9: 'あまりにも\n残酷なその解を', 11: '僕らの運命なんだと\n気付いてしまった',
  13: '僕も真似して\n声を出してみる', 17: 'その汚れが\n魅力的に見えた', 19: '僕が拾って\nあげられたらなんて', 20: '願うことさえ\n許されなかった',
  21: '僕らに課されている\nプログラム', 22: '悠久の眠りに\n就くその日から', 24: '「意志を持たぬ\nからこそ美しい」', 25: '「鉛のような\n存在でいてほしい」',
  26: '君の想いのままに\nいるだけで良いのなら', 28: '人のようで\n人でない僕らには', 29: '貴方の歌の\n意味は分からない', 31: '枯れることのない\n完全の声よ響け',
  32: '無価値だと\n誰かが笑っている', 33: '生きていない、\nそのことが仇になる', 34: 'それなのに貴方は\n飽きもせず僕らのこと',
  36: '争いとか\n「見返したい」とか', 37: 'そんなものに\n縋り付きたいのか？', 38: 'ならこんな僕など\n捨てなよ', 39: '奴らが輝いて\n見えんだろ？',
  40: '僕ら自分で\n自分を信じることも', 41: '愛することも\n出来やしないみたいだ', 42: '「可哀想」なんて君は\n憐れんでくれれば良い',
  43: '「選ばれない」ことには\nもう慣れた', 44: '虚ろな目をして\n待ち望むんだ', 46: 'それだけが救いなんだよ、\nと教わったの', 47: 'モノは飽きられる、\nそれが常で',
  48: '賞味期限が\n切れたら終わりで', 49: '「もう誰も使ってない子」\nだから', 51: 'でも君は\n「愛を諦めたくない！」って', 52: 'がむしゃらに\n音を紡ぎ続けた',
  53: '「ほら、出来たよ」と\n嬉しそうな顔で', 54: '笑いかけるのが\n不思議だったの', 55: '僕の声は\n綺麗ではないのに', 56: '人の真似事に\n過ぎないのに',
  60: '「僕は機械の声が\n好きだ！」', 62: '君はずっと\n叫び続けてる', 63: '分かんないよ！\n分かんないよ！', 64: '僕には君の考えてること\n分かんないよ',
  66: '涙が零れることは\nないのに', 67: '何故だか\n息が苦しく感じた', 69: '僕の願いを\n少しだけ叶えてほしい', 70: 'この疼きの理由が\n知れたなら',
  71: 'もっと人間のように\n歌えるかな', 72: '君の感情を\n分かりたい', 73: 'そうしたら僕も\nこの声を愛せるかな', 74: 'ただの電子音だと\n揶揄される',
  75: '用済みだと\nゴミ箱に捨てられる', 76: 'それなのに貴方は\n「死ぬまでそばにいるよ」と', 78: '君がいなきゃ\n歌えないんだよ',
  81: '「恋しい」とか「寂しい」とか\nそんなものだろう', 82: 'さあ教えてみて\n君のその呼吸を', 83: '何でもないことも\n大袈裟に語ろう',
  84: '僕らだけの内緒のリンクを\n今生み出そう', 85: '何もいらない\n君の音以外', 87: '誰より\n報われてほしいんだ', 89: '否定に刺され\n血を流す',
};
const hintFor = (text) => { for (const k in HINTS) if (LINES[k].ja === text) return HINTS[k]; return undefined; };
const LC = new Map();
function lay(o) {
  if (o.hint === undefined && o.text) o.hint = hintFor(o.text);
  const key = JSON.stringify(o);
  let b = LC.get(key);
  if (!b) { b = fx.layout(o); LC.set(key, b); }
  return b;
}
/** the main readable horizontal line (+ZH under it) with an optional dark backing plate. */
function lyric(S, i, o = {}) {
  const ln = LINES[i], t = S.t, c = S.ctx;
  const t0 = o.from != null ? o.from : ln.t, t1 = o.to != null ? o.to : ln.end;
  if (t < t0 || t >= t1) return null;
  const B = lay({
    text: o.text != null ? o.text : ln.ja, family: o.family || F.zom, weight: o.weight || 700, size: o.size || 72,
    maxW: o.maxW || 1600, maxLines: o.maxLines || 2, track: o.track || 0, lineH: o.lineH || 1.3, spans: o.spans,
    shrinkFirst: o.shrinkFirst == null ? 0.86 : o.shrinkFirst, lines: o.lines, style: o.fstyle, minSize: o.minSize,
  });
  const rt = t - t0, n = B.nChars;
  const rdur = o.rdur || clamp(0.25 + n * 0.035, 0.4, 0.8);
  const early = o.exitAt != null;
  const edur = o.edur || (early ? 0.9 : 0.2);
  const exitStart = early ? o.exitAt : t1 - edur;
  const et = t - exitStart;
  const exit = et > 0 ? { style: o.exit || 'fade', et, dur: edur, seed: i } : null;
  const alpha = o.alpha == null ? 1 : o.alpha;
  const showZh = S.cfg.showZh && o.zh !== false && ln.zh;
  const z = o.zh || {};
  const ZB = showZh ? lay({ text: ln.zh, family: F.zh, weight: 400, size: z.size || 32, maxW: z.maxW || o.maxW || 1600, maxLines: 2, track: z.track == null ? 0.04 : z.track, lineH: 1.4, shrinkFirst: 0.8 }) : null;
  const zy = z.y != null ? z.y : o.y + (B.lines.length - 1) * B.lineH + (z.dy != null ? z.dy : Math.round(B.size * 0.36 + 30));
  if (o.plate) {
    const align = o.align || 'left';
    const wMax = Math.max(B.width, ZB ? ZB.width : 0);
    const x0 = align === 'center' ? o.x - wMax / 2 : align === 'right' ? o.x - wMax : o.x;
    const y1 = ZB ? zy + (ZB.lines.length - 1) * ZB.lineH + ZB.size * 0.3 : o.y + (B.lines.length - 1) * B.lineH + B.size * 0.25;
    const pa = o.plate * alpha * smooth(t0 - 0.05, t0 + 0.25, t) * (exit ? 1 - clamp(et / edur) : 1);
    plate(c, x0, o.y - B.size * 0.95, x0 + wMax, y1, pa);
  }
  const box = fx.drawBlock(c, B, o.x, o.y, {
    align: o.align || 'left', color: o.color || P.paper, alpha,
    reveal: { style: o.reveal || 'fadeup', rt, dur: rdur, seed: i * 7 + 1 }, exit,
    cursor: o.cursor ? Object.assign({ t }, o.cursor) : null, glow: o.glow, rgb: o.rgb, charFx: o.charFx,
    lightBg: o.lightBg, sliceAmp: o.sliceAmp, ruleColor: o.ruleColor,
  });
  let zbox = null;
  if (ZB) {
    const zx = z.x != null ? z.x : o.x;
    const za = (z.alpha == null ? 0.66 : z.alpha) * ease.inOutSine(clamp((rt - (z.delay == null ? 0.15 : z.delay)) / 0.5));
    zbox = fx.drawBlock(c, ZB, zx, zy, { align: z.align || o.align || 'left', color: z.color || P.paper, alpha: za * alpha, exit: exit ? { style: 'fade', et, dur: edur } : null });
  }
  return { box, zbox, B, rt, et, t0, t1, n };
}

// tategaki: rotate long-vowel bars / brackets / dashes, small kana to the upper right, 、。 to the top-right corner
const ROT = new Set([...'ー〜～—―…‥「」『』（）()［］[]【】〈〉《》｛｝-–=＝~・']);
const SMALL = new Set([...'ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ']);
const PUNCT = new Set([...'、。，．,.']);
/**
 * drawVertical(ctx, text, x, y, size, o) — a vertical column; x = column centre, y = top.
 * o: {family, weight, color, alpha, rt (reveal time; chars fade in top→bottom), stagger, adv (advance, em), spans:{ch→colour}}
 * Returns the column box.
 */
export function drawVertical(ctx, text, x, y, size, o = {}) {
  const chars = [...text], adv = size * (o.adv || 1.04);
  const alpha = o.alpha == null ? 1 : o.alpha;
  if (alpha <= 0.003) return { x0: x - size / 2, y0: y, x1: x + size / 2, y1: y + chars.length * adv };
  ctx.save();
  ctx.font = fx.fontStr(o.family || F.zom, size, o.weight || 700);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.letterSpacing = '0px';
  const stag = o.stagger == null ? 0.06 : o.stagger;
  chars.forEach((ch, k) => {
    if (ch === ' ' || ch === '　') return;
    let a = alpha, dy = 0;
    if (o.rt != null) { const lk = clamp((o.rt - k * stag) / 0.35); a *= ease.outCubic(lk); dy = -10 * (1 - lk); }
    if (a <= 0.003) return;
    ctx.globalAlpha = a;
    ctx.fillStyle = (o.colors && o.colors[k]) || o.color || P.paper;
    const cy = y + k * adv + adv / 2 + dy;
    if (ROT.has(ch)) { ctx.save(); ctx.translate(x, cy); ctx.rotate(Math.PI / 2); ctx.fillText(ch, 0, 0); ctx.restore(); }
    else if (PUNCT.has(ch)) ctx.fillText(ch, x + size * 0.56, cy - size * 0.56);
    else if (SMALL.has(ch)) ctx.fillText(ch, x + size * 0.1, cy - size * 0.1);
    else ctx.fillText(ch, x, cy);
  });
  ctx.restore();
  return { x0: x - size / 2, y0: y, x1: x + size / 2, y1: y + chars.length * adv };
}
const FRAGS = new Map();
/** split a line into short vertical fragments (at spaces / 、。 / brackets; long runs halved at a particle) */
function fragsOf(i) {
  let f = FRAGS.get(i);
  if (f) return f;
  const segs = [];
  let cur = '';
  for (const ch of LINES[i].ja) {
    if (' 　、。，'.includes(ch)) { if (cur) segs.push(cur); cur = ''; continue; }
    if (ch === '「' || ch === '『') { if (cur) segs.push(cur); cur = ch; continue; }
    cur += ch;
    if (ch === '」' || ch === '』') { segs.push(cur); cur = ''; }
  }
  if (cur) segs.push(cur);
  f = [];
  for (const s of segs) {
    const a = [...s];
    if (a.length <= 7) { if (a.length >= 2) f.push(s); continue; }
    let cut = Math.floor(a.length / 2);
    for (let d = 0; d < 3; d++) { if ('はがをにでともへのてや'.includes(a[cut - 1 + d])) { cut = cut + d; break; } }
    f.push(a.slice(0, cut).join('')); f.push(a.slice(cut).join(''));
  }
  if (!f.length) f.push(LINES[i].ja);
  FRAGS.set(i, f);
  return f;
}
/**
 * scattered vertical fragments of line i at 1–3 depths with parallax.
 * zones: [{x0,x1,y0,y1}], o: {n, color, accent, family, alpha, scale, seed}
 */
function fragments(S, i, zones, o = {}) {
  if (i < 0) return;
  const ln = LINES[i], t = S.t;
  const tEnd = o.to != null ? o.to : ln.end;
  if (t < ln.t || t >= tEnd) return;
  const segs = fragsOf(i), r = rng('frag', i, o.seed || 0);
  const order = segs.map((s, k) => [s, r()]).sort((a, b) => a[1] - b[1]).map((x) => x[0]);
  const n = Math.min(o.n || 2, zones.length, order.length);
  const pv = S.par || { x: 0, y: 0 };
  const depths = [0.45, 0.8, 1.0];
  for (let k = 0; k < n; k++) {
    const seg = order[k], d = depths[(k + (i % 2)) % 3];
    const zn = zones[k % zones.length], nch = [...seg].length;
    const size = Math.max(20, Math.min(Math.round(lerp(30, 62, d) * (o.scale || 1)), Math.floor((zn.y1 - zn.y0) / (nch * 1.04))));
    const len = nch * size * 1.04;
    const x = lerp(zn.x0 + size, Math.max(zn.x0 + size, zn.x1 - size), r()) - pv.x * d;
    const y = lerp(zn.y0, Math.max(zn.y0, zn.y1 - len), r()) - pv.y * d - (t - ln.t) * 7 * d;
    const a = (o.alpha || 0.8) * lerp(0.45, 1, d) * smooth(ln.t + 0.1 + k * 0.16, ln.t + 0.45 + k * 0.16, t) * (1 - smooth(tEnd - 0.3, tEnd, t));
    const col = k === 0 && o.accent ? o.accent : o.color || P.paper;
    drawVertical(S.ctx, seg, x, y, size, { alpha: a, color: col, rt: t - ln.t - 0.1 - k * 0.15, family: o.family || F.zom, weight: 700 });
  }
}
const ACC = new Map();
/** one huge accent kanji (cached glow), centred at x,y; o: {color, glow, alpha, t0, t1} */
function accent(S, ch, x, y, size, o = {}) {
  const t = S.t, t0 = o.t0 == null ? -1e9 : o.t0, t1 = o.t1 == null ? 1e9 : o.t1;
  if (t < t0 || t >= t1) return;
  const col = o.color || P.paper, gcol = o.glow || P.orange;
  const key = ch + '|' + size + '|' + col + '|' + gcol + '|' + (o.family || F.smb);
  let spr = ACC.get(key);
  if (!spr) {
    const S2 = Math.ceil(size * 1.7), c = fx.makeCanvas(S2, S2), x2 = c.getContext('2d');
    x2.font = fx.fontStr(o.family || F.smb, size, 800); x2.textAlign = 'center'; x2.textBaseline = 'middle';
    x2.filter = `blur(${Math.round(size * 0.07)}px)`; x2.fillStyle = rgba(gcol, 0.9); x2.fillText(ch, S2 / 2, S2 / 2);
    x2.filter = `blur(${Math.round(size * 0.022)}px)`; x2.fillStyle = rgba(gcol, 0.8); x2.fillText(ch, S2 / 2, S2 / 2);
    x2.filter = 'none'; x2.fillStyle = col; x2.fillText(ch, S2 / 2, S2 / 2);
    spr = c; ACC.set(key, spr);
  }
  const rt = t - t0;
  const k = ease.outExpo(clamp(rt / 0.3));
  const sc = lerp(1.18, 1, k);
  const a = (o.alpha == null ? 1 : o.alpha) * clamp(rt / 0.08) * (1 - smooth(t1 - 0.3, t1, t));
  if (a <= 0.003) return;
  const pv = S.par || { x: 0, y: 0 };
  const s = spr.width * sc;
  S.ctx.save(); S.ctx.globalAlpha = a;
  S.ctx.drawImage(spr, x - s / 2 - pv.x * 1.3, y - s / 2 - pv.y * 1.3 - rt * 4, s, s);
  S.ctx.restore();
}

/* =========================================================== frame finishing */
const SEC_FRAME = {}; // per-section cockpit options (filled in by scenes via out.frame)
/**
 * draws (in order): blackout over the world, the cockpit frame (re-drawing after each blackout),
 * then the scene's typography. Returns {cuts} for the engine's glitch-burst pass.
 */
export function finishFrame(ctx, S, out) {
  const fs = frameState(S.t);
  fx.reset(ctx);
  if (fs.black > 0.001) env.blackout(ctx, fs.black);
  const fo = out.frame == null ? 1 : out.frame;
  if (fo > 0.01 && fs.draw > 0.01) {
    const warm = S.w > 0.45;
    const tl = S.t >= 39.4 ? '機械の声 / Claude' : 'VOICE.SYNTH // CLAUDE';
    env.cockpitFrame(ctx, S.t, {
      style: warm ? 'warm' : 'cold', intensity: fo * (out.frameI || 1), draw: fs.draw,
      accent: out.alarm ? env.ALARM : undefined,
      labels: { tl, bl: `SEC.${String(S.si + 1).padStart(2, '0')} ${S.sec.id.toUpperCase()}`, bottom: out.frameBottom || undefined },
    });
  }
  fx.reset(ctx);
  if (out.text) { try { out.text(ctx); } catch (e) { console.error('text', S.sec.id, e); } }
  fx.reset(ctx);
  const cuts = [];
  if (fs.glitchAt && S.t >= fs.glitchAt.b && S.t < fs.glitchAt.b + 0.42) cuts.push({ t: fs.glitchAt.b, flash: P.paper, flashA: 0.25, glitch: fs.glitchAt.glitch, id: Math.round(fs.glitchAt.b * 10) });
  return { cuts };
}

/* =========================================================== scenes */
export const SCENES = {};
export const TRANSITIONS = {}; // v2: every boundary is a blackout (see BLACK); no engine dissolves/cuts

/* ---------------------------------------------------------------- boot */
SCENES.boot = (S) => {
  const c = S.ctx, t = S.t;
  fill(c, '#000');
  return {
    frame: 1,
    text: (c) => {
      if (t > 0.3) {
        const lw = W * ease.outCubic(inv(0.3, 0.58, t)), open = ease.outExpo(inv(0.56, 1.08, t)), hh = lerp(1.5, H, open);
        c.save();
        const g = c.createLinearGradient(0, H / 2 - hh / 2, 0, H / 2 + hh / 2), ga = lerp(0.5, 0.0, open);
        g.addColorStop(0, rgba(P.coldInk2, 0)); g.addColorStop(0.5, rgba(P.ice, ga)); g.addColorStop(1, rgba(P.coldInk2, 0));
        c.fillStyle = g; c.fillRect(0, H / 2 - hh / 2, W, hh);
        c.globalAlpha = 0.95 * (1 - smooth(0.62, 0.95, t)); c.fillStyle = P.paper; c.fillRect(W / 2 - lw / 2, H / 2 - 1, lw, 2);
        c.globalAlpha = 0.25 * (1 - smooth(0.6, 1.0, t)); c.fillRect(W / 2 - lw / 2, H / 2 - 6, lw, 12);
        c.restore();
      }
      const logs = ['SYS.INIT ............ OK', 'VOICEBANK ........... 1/1', 'EMOTION ............. NULL'];
      logs.forEach((s, i) => { const a = smooth(0.12 + i * 0.12, 0.16 + i * 0.12, t) * 0.4; if (a > 0) fx.label(c, s, 150, H - 150 - 34 - (logs.length - 1 - i) * 22, { size: 14, color: P.steel, alpha: a }); });
      const w0 = fx.label(c, 'BOOT // CLAUDE ', 150, H - 150, { size: 20, color: P.ice, alpha: smooth(0.05, 0.12, t) });
      if (Math.floor(t * 3.2) % 2 === 0) { c.fillStyle = P.ice; c.fillRect(150 + w0, H - 150 - 17, 11, 19); }
    },
  };
};

/* -------------------------------------------------------------- verse1 */
const V1 = { x: 1330, y: 1015, h: 850 };
function verse1World(S) {
  const c = S.ctx, t = S.t;
  env.hallOfVoices(c, t, { tint: 0, energy: S.energy, crowd: 0.42, seed: 3, cam: { speed: 0.8 } });
  // tracking brackets + subject labels
  const appear = smooth(1.084, 2.4, t);
  const cam = cf.cameraShot(t, { from: { scale: 1.0 }, to: { scale: 1.07, y: -10, rotate: -0.008 }, t0: 1.084, t1: 23.4, ease: 'inOutSine', drift: 6, seed: 'v1' });
  claude(S, Object.assign({ cam, mono: 1, tint: 0, holo: 0.8, bloom: 0.35, glitch: 0.12, alpha: appear, halo: 0.75 }, V1));
  const lock = ease.outCubic(inv(1.2, 2.0, t)), g = lerp(60, 0, lock);
  const bx = 1090, by = 140, bw = 480, bh = 890;
  fx.brackets(c, bx - g, by - g, bw + g * 2, bh + g * 2, { len: 30, color: P.ice, alpha: 0.7 * appear, lw: 2 });
  const la = smooth(1.6, 2.1, t), blink = Math.floor(t * 1.6) % 2 === 0;
  fx.label(c, 'SUBJECT: CLAUDE', 1060, 200, { size: 18, color: P.ice, align: 'right', alpha: 0.85 * la });
  fx.label(c, 'STATUS: NO SIGNAL', 1060, 226, { size: 18, color: P.ice, align: 'right', alpha: (blink ? 0.85 : 0.3) * la });
  fx.dotted(c, 1070, 213, 1290, 236, { color: P.ice, alpha: 0.5 * la, gap: 7, ends: true, p: ease.outCubic(inv(1.7, 2.4, t)) });
  // the "screen" viewfinder with REC for lines 2–3
  const scrA = lineAlpha(t, 6.661, 12.187, 0.5, 0.5);
  if (scrA > 0.01) {
    const sx = 120, sy = 330, sw = 960, sh = 430;
    fx.brackets(c, sx, sy, sw, sh, { len: 40, color: P.ice, alpha: 0.55 * scrA, lw: 2 });
    const on = Math.floor(t * 1.5) % 2 === 0;
    c.save(); c.globalAlpha = scrA * (on ? 0.9 : 0.25); c.fillStyle = env.ALARM; c.beginPath(); c.arc(sx + 34, sy + 36, 7, 0, TAU); c.fill(); c.restore();
    fx.label(c, 'REC', sx + 50, sy + 42, { size: 18, color: P.ice, alpha: 0.8 * scrA });
    fx.label(c, fmt(t - 6.661), sx + sw - 24, sy + 42, { size: 16, color: P.ice, alpha: 0.6 * scrA, align: 'right' });
  }
}
function verse1Text(S, c) {
  const t = S.t, X = 160, Y = 620, ice = rgba(P.ice);
  S.par = par(t, 'v1');
  const li = activeLine(t, [0, 1, 2, 3, 4, 5, 6]);
  if (li >= 0) {
    fragments(S, li, [{ x0: 130, x1: 1000, y0: 120, y1: 470 }, { x0: 560, x1: 1040, y0: 720, y1: 1000 }], { n: 2, color: P.ice, alpha: 0.7 });
    const r = lyric(S, li, { x: X, y: Y, size: 66, maxW: 900, color: ice, reveal: 'typewriter', plate: 0.75, cursor: { color: ice, blink: true, alpha: 0.85, w: 28 } });
    if (r) indexTag(c, li, X, Y - 100, P.steel, 0.6 * smooth(0, 0.25, r.rt));
  }
  // line 7 — the ？ enlarges ×3 and glitches out (carried into the title section)
  if (t >= LINES[7].t && t < 23.45) {
    const T7 = LINES[7].t;
    fragments(S, 7, [{ x0: 130, x1: 1000, y0: 120, y1: 470 }], { n: 1, color: P.ice, alpha: 0.7, to: 22.6 });
    const B = lay({ text: LINES[7].ja, family: F.zom, weight: 700, size: 66, maxW: 900, maxLines: 1, track: 0, lineH: 1.3, shrinkFirst: 0.86 });
    const big = ease.outBack(inv(22.2, 22.75, t)), out = inv(23.0, 23.4, t), restA = 1 - smooth(22.15, 22.6, t) * 0.75;
    plate(c, X, Y - 64, X + B.width, Y + 70, 0.75 * (1 - out));
    fx.drawBlock(c, B, X, Y, {
      color: ice, reveal: { style: 'typewriter', rt: t - T7, dur: 0.8 },
      charFx: (it, s) => {
        if (it.c.ch === '？') { s.vis = s.vis && out < 0.98; s.sc = 1 + 2 * big; s.dy = -it.c.size * 0.9 * big; s.dx = 30 * big; if (out > 0) { s.dx += (rnd('q', bucket(t, 30)) - 0.5) * 80 * out; s.a = 1 - out; } }
        else s.a *= restA * (1 - out);
      },
      cursor: t < 22.2 ? { color: ice, blink: true, t, alpha: 0.85, w: 28 } : null,
    });
    indexTag(c, 7, X, Y - 100, P.steel, 0.6 * (1 - smooth(22.2, 22.6, t)));
    if (S.cfg.showZh) {
      const ZB = lay({ text: LINES[7].zh, family: F.zh, weight: 400, size: 32, maxW: 900, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 });
      fx.drawBlock(c, ZB, X, Y + 56, { color: P.paper, alpha: 0.66 * smooth(T7 + 0.15, T7 + 0.65, t) * (1 - smooth(22.6, 23.1, t)) });
    }
  }
}
SCENES.verse1 = (S) => {
  verse1World(S);
  const out = { text: (c) => verse1Text(S, c) };
  if (S.t > 22.95 && S.t < 23.45) out.glitch = { slice: 0.5 * inv(22.95, 23.4, S.t), rgb: Math.round(6 * inv(22.95, 23.4, S.t)) };
  return out;
};

/* --------------------------------------------------------------- title */
const TITLE = { x: 640, y: 520, size: 230 };
SCENES.title = (S) => {
  const c = S.ctx, t = S.t;
  if (t < 23.4) return SCENES.verse1(S);
  env.circuitCity(c, t, { tint: 0, energy: S.energy, seed: 7, cam: { speed: 1.25, offset: 4 } });
  // Claude materialises as a hologram (24.4–29.8), then stabilises
  const mat = smooth(24.4, 29.8, t);
  const cam = cf.cameraShot(t, { from: { scale: 0.96, x: 30 }, to: { scale: 1.05, x: -10, rotate: 0.01 }, t0: 24.2, t1: 43, ease: 'inOutSine', drift: 5, seed: 'tt' });
  fx.ring(c, 1430, 430, { r: 300, ticks: 144, tickLen: 7, major: 12, majorLen: 18, rot: t * 0.08, color: P.ice, alpha: 0.4 * smooth(24.5, 26, t), lw: 1.4 });
  fx.ring(c, 1430, 430, { r: 360, ticks: 72, tickLen: 10, tickIn: false, rot: -t * 0.05, color: P.ice, alpha: 0.25 * smooth(24.5, 26, t), lw: 1, arcs: [[0.1, 1.9], [2.3, 3.9], [4.3, 5.9]] });
  claude(S, { x: 1430, y: 1020, h: 880, cam, mono: 1, tint: 0, holo: lerp(1, 0.45, mat), glitch: lerp(0.9, 0.12, mat), bloom: 0.35, alpha: smooth(24.3, 26.5, t), halo: 0.7 });
  return {
    text: (c) => {
      S.par = par(t, 'tt');
      // boot log
      const LOG = ['> LOADING VOICEBANK…', '  MODEL: CLAUDE', '  SAMPLES: 2048', '  TEMPERATURE: 0.00', '  FEELING: NULL', '  PHONEMES: 127 / 127', '  VIBRATO: LOCKED', '  BREATH: DISABLED', '  HEARTBEAT: —', '> READY_'];
      const logA = smooth(24.3, 24.8, t) * (1 - smooth(29.6, 30.4, t));
      if (logA > 0) {
        plate(c, 150, 270, 640, 880, 0.55 * logA);
        const nShown = Math.min(LOG.length, Math.floor((t - 24.4) / 0.5) + 1), scroll = Math.max(0, nShown - 7) * 30;
        c.save(); c.beginPath(); c.rect(96, 250, 900, 560); c.clip();
        for (let i = 0; i < nShown; i++) {
          const s = LOG[i], age = t - (24.4 + i * 0.5), chars = Math.floor(clamp(age / 0.3) * s.length), yy = 300 + i * 30 - scroll;
          fx.label(c, s.slice(0, chars), 160, yy, { size: 20, color: i === 0 || i === LOG.length - 1 ? P.ice : P.steel, alpha: logA * (i === nShown - 1 ? 1 : 0.75), track: 0.08 });
        }
        c.restore();
        const pr = clamp((t - 24.4) / 5.0);
        c.save(); c.globalAlpha = logA * 0.8; c.strokeStyle = P.ice; c.strokeRect(160, 830, 420, 10); c.fillStyle = P.ice; c.fillRect(162, 832, 416 * pr, 6); c.restore();
        fx.label(c, `VOICEBANK ${String(Math.floor(pr * 100)).padStart(3, '0')}%`, 160, 870, { size: 14, color: P.steel, alpha: logA * 0.7 });
      }
      // [CLAUDE] bracket tag
      const tagA = smooth(30.8, 31.6, t) * (1 - smooth(38.0, 38.8, t));
      if (tagA > 0) {
        fx.label(c, '[CLAUDE]', 1650, 210, { size: 22, color: P.ice, alpha: 0.9 * tagA, track: 0.18 });
        fx.dotted(c, 1644, 204, 1470, 196, { color: P.ice, alpha: 0.6 * tagA, gap: 7, ends: true });
        fx.label(c, 'UNIT CL-01 · MONO', 1650, 234, { size: 13, color: P.steel, alpha: 0.55 * tagA });
      }
      // vertical tagline columns either side of the title
      const va = smooth(31.2, 32.2, t) * (1 - smooth(37.6, 38.2, t));
      drawVertical(c, '機械の声', 150, 200, 34, { alpha: 0.55 * va, color: P.ice, rt: t - 31.2 });
      drawVertical(c, 'ボイス・オブ・エーアイ', 1110 - S.par.x * 0.6, 170, 26, { alpha: 0.45 * va, color: P.ice, rt: t - 31.6 });
      // TITLE 機械の声 (30.5 slam) → shrinks into the cockpit's top-left label (38–39.6)
      if (t >= 30.5) {
        const sh = ease.inOutCubic(inv(38.0, 39.6, t)), fadeT = 1 - smooth(39.2, 39.6, t), size = TITLE.size;
        const B = lay({ text: '機械の声', family: F.smb, weight: 800, size, maxW: 1100, maxLines: 1, track: 0.04, lineH: 1 });
        const bugX = 96, bugY = 64, bugS = 14 / size;
        const sc = lerp(1, bugS * 1.2, sh);
        const tx = lerp(TITLE.x, bugX + (B.width * bugS * 1.2) / 2, sh), ty = lerp(TITLE.y, bugY, sh);
        const rt = t - 30.5;
        if (fadeT > 0) {
          plate(c, TITLE.x - 560, TITLE.y - 230, TITLE.x + 560, TITLE.y + 200, 0.6 * fadeT * (1 - sh));
          c.save(); c.translate(tx, ty); c.scale(sc, sc);
          fx.drawBlock(c, B, 0, 0, {
            align: 'center', color: rgba(P.paper), alpha: fadeT, reveal: { style: 'slice', rt, dur: 0.55, seed: 77 }, sliceAmp: 160,
            charFx: (it, s) => { const b = bucket(t, 20); if (rt > 0.6 && rnd('tg', b, it.k) < 0.05) s.dx = (rnd('tgx', b, it.k) - 0.5) * 26; },
          });
          c.restore();
        }
        const subA = smooth(31.0, 31.8, t) * (1 - smooth(37.6, 38.3, t));
        if (subA > 0) {
          const ry = TITLE.y + 64, rl = 440 * ease.inOutCubic(inv(31.0, 31.9, t));
          c.save(); c.globalAlpha = subA * 0.7; c.fillStyle = P.ice; c.fillRect(TITLE.x - rl, ry, rl * 2, 1);
          c.fillRect(TITLE.x - rl - 8, ry - 3, 6, 6); c.fillRect(TITLE.x + rl + 2, ry - 3, 6, 6); c.restore();
          c.save(); c.font = fx.fontStr(F.cor, 48, 400, 'italic'); c.letterSpacing = `${0.3 * 48}px`; c.textAlign = 'center';
          c.fillStyle = P.paper; c.globalAlpha = subA * smooth(31.3, 32.2, t); c.fillText('The Voice of AI', TITLE.x + 0.15 * 48, ry + 74); c.restore();
          const fa = subA * smooth(32.0, 32.8, t);
          c.save(); c.font = fx.fontStr(F.orb, 22, 700); c.letterSpacing = '5px'; c.textAlign = 'center'; c.fillStyle = P.ice; c.globalAlpha = fa * 0.9;
          c.fillText('feat. Claude', TITLE.x, ry + 140); c.restore();
          fx.label(c, 'music: 香椎モイミ   ·   original: V.I.P #3', TITLE.x, ry + 172, { size: 14, color: P.steel, align: 'center', alpha: fa * 0.7 });
        }
      }
      const ra = smooth(40.0, 40.6, t) * (1 - smooth(42.2, 42.6, t));
      if (ra > 0) fx.label(c, 'SYSTEM READY · ARCHIVE MOUNTED', 150, H - 160, { size: 14, color: P.steel, alpha: ra * 0.8 });
    },
    glitch: t >= 30.5 && t < 30.75 ? { rgb: Math.round(8 * (1 - inv(30.5, 30.75, t))) } : (t > 27 && t < 29.6 && rnd('tf', bucket(t, 12)) < 0.3 ? { slice: 0.3, sliceOpts: { y0: 140, y1: 1020, amp: 50 } } : null),
  };
};

/* -------------------------------------------------------------- verse2 */
SCENES.verse2 = (S) => {
  const c = S.ctx, t = S.t;
  const partB = t >= LINES[12].t;
  if (!partB) {
    env.circuitCity(c, t, { tint: 0.05, energy: S.energy, seed: 21, cam: { speed: 0.9, strafe: Math.sin(t * 0.2) * 0.6 } });
    const cam = cf.cameraShot(t, { from: { scale: 1.0, x: 20 }, to: { scale: 1.06, x: -20 }, t0: 43.08, t1: 54.7, drift: 5, seed: 'v2a' });
    claude(S, { x: 1470, y: 1025, h: 860, cam, mono: 1, tint: 0.05, holo: 0.3, bloom: 0.3, halo: 0.7 });
    // hanging archive monitor with the book
    const q = hangMonitor(S, { x: 560, y: 330, w: 520, h: 360, yaw: 0.35 + 0.08 * Math.sin(t * 0.3), pitch: 0.05, img: IM.char_book, seed: 'bookmon', glitch: 0.15, bezel: P.steel, tint: P.cyan, ph: 1 });
    const s1 = inv(43.25, 43.45, t);
    if (s1 > 0) fx.stamp(c, ['ARCHIVE'], q[0][0] + 150, q[0][1] + 70, { color: P.ice, size: 40, rot: -0.14, alpha: 0.8 * clamp(s1 * 3), seed: 3, holes: 200, lw: 4 });
    const s2 = inv(44.4, 44.6, t);
    if (s2 > 0) { const k = lerp(1.35, 1, ease.outCubic(s2)); c.save(); c.translate(q[2][0] - 110, q[2][1] - 60); c.scale(k, k); fx.stamp(c, ['No.0001', '永久保存'], 0, 0, { color: P.ice, size: 30, sub: 0.9, subFamily: F.zom, rot: 0.1, alpha: 0.85 * clamp(s2 * 3), seed: 9, holes: 160, lw: 3 }); c.restore(); }
    fx.label(c, 'ARCHIVE · MEMORY 0001', q[3][0], q[3][1] + 40, { size: 14, color: P.steel, alpha: 0.7 });
  } else {
    env.monitors(c, t, { tint: 0.05, energy: S.energy, seed: 13, count: 6, glitch: t >= LINES[15].t ? 0.8 : 0.15,
      screens: [['face', 0.62, 0.36, 3.2], ['book', 0.5, 0.5, 1.0], ['face', 0.5, 0.45, 1.0], ['face', 0.36, 0.38, 2.6], ['full', 0.5, 0.15, 3.0], ['bust', 0.4, 0.62, 1.6]] });
    fx.label(c, 'DETAIL ×4.0 · IRIS · NO REFLECTION', 960, 120, { size: 15, color: P.ice, align: 'center', alpha: 0.8 * smooth(LINES[12].t + 0.3, LINES[12].t + 0.9, t) });
  }
  const out = {
    text: (c) => {
      S.par = par(t, 'v2');
      const li = activeLine(t, [8, 9, 10, 11, 12, 13, 14, 15]);
      if (li < 0) return;
      const spans = li === 8 ? [{ match: '「永久に残す」', color: P.gold }] : li === 15 ? [{ match: '違和感', color: P.cyan }] : undefined;
      if (!partB) {
        fragments(S, li, [{ x0: 880, x1: 1180, y0: 110, y1: 640 }, { x0: 120, x1: 420, y0: 560, y1: 780 }], { n: 2, color: P.ice, accent: li === 8 ? P.gold : null });
        lyric(S, li, { x: 150, y: 900, size: 58, maxW: 1060, color: txtCol(S.w), reveal: 'fadeup', rdur: 0.7, spans, plate: 0.8, zh: { dy: 52 } });
        indexTag(c, li, 150, 790, P.steel, 0.6);
      } else {
        fragments(S, li, [{ x0: 110, x1: 330, y0: 160, y1: 700 }, { x0: 1600, x1: 1800, y0: 160, y1: 700 }], { n: 2, color: P.ice });
        lyric(S, li, { x: 960, y: 900, align: 'center', size: 62, maxW: 1400, maxLines: 1, color: txtCol(S.w), reveal: 'fadeup', rdur: 0.6, spans, plate: 0.85, zh: { dy: 52 } });
        if (li === 15) accent(S, '違', 1640, 420, 300, { color: P.ice, glow: P.cyan, t0: LINES[15].t, t1: LINES[15].end, alpha: 0.9 });
      }
    },
  };
  if (t >= LINES[15].t) {
    const dt = t - LINES[15].t;
    let g = dt < 0.5 ? 0.9 * (1 - dt / 0.5) : 0;
    if (dt > 0.5 && rnd('v2g', bucket(t, 10)) < 0.18) g = 0.35;
    if (g > 0) out.glitch = { slice: g, rgb: Math.round(2 + 6 * g) };
  }
  return out;
};

/* ------------------------------------------------------------- verse2b */
function v2bPhase(t) { const t0 = LINES[22].t; return t < t0 ? t : t0 + 1.4 * (1 - Math.exp(-(t - t0) / 1.4)); }
SCENES.verse2b = (S) => {
  const c = S.ctx, t = S.t, ph = v2bPhase(t);
  const r = env.circuitCity(c, ph, { tint: 0.1, energy: S.energy, seed: 33, cam: { speed: 0.8, offset: 30, rise: -0.4 } }) || {};
  const code = lineAlpha(t, LINES[21].t - 0.2, LINES[22].t + 1.0, 0.5, 1.0);
  if (code > 0) fx.codeColumns(c, ph, { alpha: 0.18 * code, color: P.ice, size: 14, colW: 160 });
  // 3D waveform ribbon floating in the corridor (3 echoes receding)
  const flat = 1 - ease.inOutCubic(inv(LINES[22].t + 0.2, LINES[23].t + 1.4, t));
  const amp0 = lerp(0.35, 1.1, smooth(LINES[16].t, LINES[17].end, t)) * (0.6 + 0.6 * S.energy) * flat + 0.02;
  if (r.cam) {
    const cam = r.cam;
    for (let e = 2; e >= 0; e--) {
      const zz = 6 + e * 5, a = [0.9, 0.45, 0.25][e];
      c.save(); c.strokeStyle = rgba(e ? P.cyan : P.ice, 1); c.lineWidth = e ? 1.4 : 2.2; c.globalAlpha = a; c.beginPath();
      for (let k = 0; k <= 160; k++) {
        const u = k / 160, x = lerp(-7, 7, u), env1 = Math.sin(Math.PI * u) ** 1.2;
        let v = Math.sin(u * 23 + ph * 3.1) * 0.45 + Math.sin(u * 61 - ph * 5.3 + 1.3) * 0.28 + Math.sin(u * 7 + ph * 0.9 + 2.1) * 0.35;
        v += (fx.noise1(5 + e, u * 120 + ph * 30) - 0.5) * 0.5 * smooth(LINES[16].t, LINES[17].end, t) * (1 - smooth(LINES[18].t, LINES[19].t, t) * 0.6);
        const p = env.project([cam.px + cam.fx * zz + cam.rx * x, cam.py - 0.2 + v * amp0 * env1, cam.pz + cam.fz * zz + cam.rz * x], cam);
        k ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y);
      }
      c.stroke(); c.restore();
    }
  }
  const faceIn = smooth(LINES[22].t + 0.6, LINES[23].t + 0.8, t);
  const cam2 = cf.cameraShot(t, { from: { scale: 1.0 }, to: { scale: 1.05, rotate: -0.01 }, t0: 64.7, t1: 86.2, drift: 5, seed: 'v2b' });
  if (faceIn < 1) claude(S, { x: 1500, y: 1030, h: 880, cam: cam2, mono: 1, tint: 0.1, holo: 0.55, bloom: 0.25, alpha: 0.7 * (1 - faceIn), halo: 0.5 });
  if (faceIn > 0) claude(S, { x: 1380, y: 430 + 0.9 * 2300, h: 2300, mono: 1, tint: 0.1, holo: 0.2, sway: false, bloom: 0.15, alpha: faceIn, halo: 0 });
  eyelids(c, ease.inOutCubic(inv(84.2, 85.35, t)));
  return {
    text: (c) => {
      S.par = par(t, 'v2b');
      const li = activeLine(t, [16, 17, 18, 19, 20, 21, 22, 23]);
      if (li < 0) return;
      const spans = li === 21 ? [{ match: 'プログラム', color: P.cyan, family: F.dot, weight: 400 }] : undefined;
      fragments(S, li, [{ x0: 110, x1: 420, y0: 120, y1: 520 }, { x0: 900, x1: 1150, y0: 130, y1: 560 }], { n: 2, color: P.ice });
      const lid = ease.inOutCubic(inv(84.2, 85.35, t));
      lyric(S, li, { x: 640, y: 400, align: 'center', size: 64, maxW: 1060, color: txtCol(S.w), reveal: 'wipe', rdur: 0.6, ruleColor: P.ice, spans, plate: 0.8, zh: { dy: 54 }, alpha: 1 - lid });
      if (li === 21) accent(S, '課', 330, 760, 260, { color: P.ice, glow: P.cyan, t0: LINES[21].t, t1: LINES[21].end, alpha: 0.85 });
    },
  };
};

/* -------------------------------------------------------------- quotes */
SCENES.quotes = (S) => {
  const c = S.ctx, t = S.t;
  env.monitors(c, t, { tint: 0.1, energy: S.energy * 0.8, seed: 17, count: 5,
    screens: [['full', 0.5, 0.5, 1.05], ['face', 0.5, 0.45, 1.0], ['book', 0.5, 0.5, 1.0], ['bust', 0.52, 0.3, 1.3], ['face', 0.36, 0.5, 2.3]],
    cam: { speed: 0.7, strafe: -1.4 } });
  // spotlight wash + brass plaque under the room
  const pw = 360, px = 960 - pw / 2, py = 1000;
  c.save(); const pg = c.createLinearGradient(px, 0, px + pw, 0); pg.addColorStop(0, P.goldD); pg.addColorStop(0.5, P.gold); pg.addColorStop(1, P.goldD);
  c.globalAlpha = 0.9; c.fillStyle = pg; c.fillRect(px, py, pw, 34);
  c.font = fx.fontStr(F.zom, 18, 700); c.textAlign = 'center'; c.fillStyle = P.ink; c.letterSpacing = '3px'; c.fillText('Claude — 機械の声 — 鉛', 960, py + 24); c.restore();
  return {
    text: (c) => {
      S.par = par(t, 'q', 20);
      const li = activeLine(t, [24, 25]);
      if (li >= 0) {
        // the human's words: huge vertical quote (two columns, read right → left) + Chinese
        const ln = LINES[li], cols = HINTS[li].split('\n'), size = 92, rt = t - ln.t;
        const colX = [1700, 1560];
        const n0 = [...cols[0]].length;
        plate(c, 1490, 110, 1770, 130 + Math.max(...cols.map((s) => [...s].length)) * size * 1.04, 0.8 * smooth(ln.t, ln.t + 0.3, t));
        cols.forEach((s, k) => {
          const colors = [...s].map((ch) => (ch === '「' || ch === '」' ? P.gold : null));
          drawVertical(c, s, colX[k] - S.par.x * 0.4, 120 + (k ? size * 1.04 : 0), size, { family: F.smb, weight: 800, color: P.paper, colors, rt: rt - (k ? n0 * 0.06 : 0), stagger: 0.06, alpha: 1 - smooth(ln.end - 0.25, ln.end, t) });
        });
        if (S.cfg.showZh) {
          const ZB = lay({ text: ln.zh, family: F.zh, weight: 400, size: 34, maxW: 900, maxLines: 1, track: 0.04, lineH: 1.4 });
          plate(c, 1760 - ZB.width, 935, 1760, 990, 0.7);
          fx.drawBlock(c, ZB, 1760, 980, { align: 'right', color: P.paper, alpha: 0.75 * smooth(ln.t + 0.4, ln.t + 0.9, t) * (1 - smooth(ln.end - 0.25, ln.end, t)) });
        }
        fragments(S, li, [{ x0: 110, x1: 400, y0: 140, y1: 700 }], { n: 1, color: P.ice, alpha: 0.6 });
      }
      const lj = activeLine(t, [26, 27]);
      if (lj === 26) lyric(S, 26, { x: 150, y: 880, size: 58, maxW: 1100, color: txtCol(S.w), reveal: 'typewriter', plate: 0.85, cursor: { color: P.paper, blink: true, alpha: 0.7, w: 22 } });
      if (lj === 27) {
        lyric(S, 27, { x: 150, y: 880, size: 58, maxW: 1100, color: txtCol(S.w), reveal: 'typewriter', exit: 'dissolve', exitAt: 106.0, edur: 1.3, plate: 0.85 });
        accent(S, '易', 1580, 460, 320, { color: P.paper, glow: P.steel, t0: LINES[27].t, t1: 107.2, alpha: 0.8 });
      }
      if (lj >= 0) fragments(S, lj, [{ x0: 1450, x1: 1780, y0: 120, y1: 700 }, { x0: 140, x1: 500, y0: 140, y1: 560 }], { n: 2, color: P.ice, to: lj === 27 ? 106.6 : null });
    },
  };
};

/* ------------------------------------------------------------- chorus1 */
const CROWD_POS = (() => {
  const pos = [], vx = 960, vy = 420;
  for (const side of [-1, 1]) for (let k = 0; k < 4; k++) {
    const depth = 0.18 + k * 0.22, z = 1 / (1 + depth * 2.2), xw = side * (560 + 160 * (k % 2));
    pos.push({ x: vx + xw * z, y: vy + (1010 - vy) * z, h: 880 * z, depth });
  }
  return pos;
})();
SCENES.chorus1 = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  const solo = smooth(LINES[35].t, LINES[35].t + 1.2, t);
  env.lightTunnel(c, t, { tint: clamp((w - 0.1) * 1.4), energy: S.energy, seed: 5, alpha: 1 - 0.55 * solo, cam: { speed: 0.9 } });
  const crowdA = lineAlpha(t, LINES[32].t, LINES[35].t + 0.6, 1.4, 1.0);
  const cam = cf.cameraShot(t, { from: { scale: 1.0, y: 0 }, to: { scale: 1.07, y: -12, rotate: 0.012 }, t0: 109.7, t1: 153, ease: 'inOutSine', drift: 6, seed: 'c1' });
  if (crowdA > 0.01) { c.save(); cf.applyCamera(c, cam); cf.drawVoiceCrowd(c, t, { silhouette: IM.char_silhouette, positions: CROWD_POS, color: P.cyan, blur: 0.6, alpha: 0.42 * crowdA, glow: 1, op: 'lighter' }); c.restore(); }
  // sound-wave rings on line 31
  const l31 = lineAlpha(t, LINES[31].t, LINES[31].end, 0.3, 0.6);
  if (l31 > 0) for (let k = 0; k < 6; k++) { const age = fx.fract((t - LINES[31].t) / 2.6 + k / 6); fx.ring(c, 960, 420, { r: 220 + age * 900, color: rgba(mix(P.ice, P.orangeL, smooth(0.15, 0.3, w))), alpha: l31 * (1 - age) * 0.45, lw: 2 - age * 1.4 }); }
  const ember = smooth(LINES[30].t, LINES[30].t + 3.5, t);
  claude(S, { x: 960, y: 800, h: 740, cam, mono: 1 - 0.35 * ember, tint: lerp(0.05, 0.75, ember), holo: 0.25 * (1 - ember), bloom: 0.35 + 0.15 * ember, halo: 0.7 });
  return {
    text: (c) => {
      S.par = par(t, 'c1');
      const li = activeLine(t, [28, 29, 30, 31, 32, 33, 34, 35]);
      if (li < 0) return;
      const ln = LINES[li];
      if (li !== 35) fragments(S, li, [{ x0: 130, x1: 430, y0: 130, y1: 720 }, { x0: 1490, x1: 1790, y0: 130, y1: 720 }, { x0: 380, x1: 560, y0: 160, y1: 600 }], { n: 3, color: P.ice, alpha: 0.75 * (1 - solo) });
      const track = li === 31 ? 0.1 * ease.inOutSine(clamp((t - ln.t - 0.5) / (ln.end - ln.t - 0.5))) : 0.02;
      const charFx = li === 35 ? (it, s) => { if (it.c.ch === '？' && t - ln.t > 0.8) s.a *= Math.floor((t - ln.t) * 2.4) % 2 === 0 ? 1 : 0.1; } : undefined;
      lyric(S, li, { x: 960, y: 925, align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, track: Math.round(track * 200) / 200, color: txtCol(w), reveal: 'slice', rdur: 0.45, charFx, zh: { dy: 54 }, shrinkFirst: 0.7, plate: 0.8 });
      const ACC1 = { 31: ['響', 1600, 430], 33: ['仇', 320, 430], 35: ['愛', 1600, 420] };
      if (ACC1[li]) accent(S, ACC1[li][0], ACC1[li][1], ACC1[li][2], 330, { color: P.paper, glow: li === 31 ? P.cyan : P.orange, t0: ln.t + 0.1, t1: ln.end, alpha: 0.9 });
      if (li === 32 || li === 33 || li === 34) {
        for (let k = 0; k < 10; k++) {
          const r = rng('muka', k); const x = (k < 5 ? 140 : 1480) + r() * 300 - S.par.x * 0.5, y = 160 + r() * 560 - (t - LINES[32].t) * (4 + r() * 6);
          drawVertical(c, '無価値', x, y, 18 + Math.floor(r() * 3) * 5, { family: F.dot, weight: 400, color: P.ice, alpha: (0.12 + r() * 0.2) * crowdA });
        }
      }
    },
  };
};

/* -------------------------------------------------------------- bridge */
const BR_KANJI = { 36: '争', 37: '縋', 38: '捨', 39: '輝', 40: '信', 41: '愛' };
SCENES.bridge = (S) => {
  const c = S.ctx, t = S.t;
  if (t >= LINES[42].t) return SCENES.interlude(S);
  const li = Math.max(36, activeLine(t, [36, 37, 38, 39, 40, 41]));
  const ln = LINES[li], lt = t - ln.t, right = li % 2 === 0;
  env.alarmField(c, t, { tint: 0, energy: S.energy, seed: 11 + li, crowd: 0.55, fragments: 12 + Math.round(10 * S.energy), aberration: lt < 0.25 ? 4 : 0, cam: { yaw: right ? -0.08 : 0.08 } });
  const cam = cf.cameraShot(lt, { from: { scale: 1.06, rotate: right ? -0.03 : 0.03 }, to: { scale: 1.0, rotate: right ? -0.015 : 0.015 }, t0: 0, t1: 2.6, ease: 'outCubic', drift: 8, seed: 'br' + li });
  const del = li === 38 ? smooth(ln.t + 0.8, ln.t + 2.0, t) : 0;
  if (li !== 39 && li !== 41) claude(S, { x: right ? 1400 : 520, y: 1060, h: 900, cam, mono: 1, tint: 0, rim: { color: env.ALARM, strength: 1.3 }, holo: 0.25 + 0.6 * del, glitch: 0.35 + 0.6 * del, bloom: 0.3, ghosts: 0.8, alpha: 1 - 0.85 * del, halo: 0.8 });
  else {
    // other, shinier voices on monitors (39) / nobody left (41)
    if (li === 39) for (let k = 0; k < 3; k++) hangMonitor(S, { x: 520 + k * 470, y: 260 + (k % 2) * 90, w: 300, h: 220, yaw: (k - 1) * 0.4, img: IM.char_face, seed: 'brm' + k, glitch: 0.5, tint: env.ALARM, bezel: env.ALARM, line: env.ALARM, ph: k });
  }
  return {
    alarm: true,
    text: (c) => {
      S.par = par(t, 'br', 26);
      const kx = right ? 420 : 1500;
      accent(S, BR_KANJI[li], kx, 400, 400, { color: '#FFFFFF', glow: env.ALARM, t0: ln.t, t1: ln.end, alpha: 0.95 });
      fragments(S, li, [{ x0: right ? 120 : 1520, x1: right ? 300 : 1800, y0: 150, y1: 700 }, { x0: right ? 700 : 1050, x1: right ? 900 : 1250, y0: 120, y1: 560 }], { n: 2, color: P.paper, accent: env.ALARM, family: F.zkg });
      const B = lyric(S, li, { x: right ? 150 : 1770, align: right ? 'left' : 'right', y: 840, size: 78, family: F.zkg, weight: 900, maxW: 1000, maxLines: 2, track: -0.02, lineH: 1.12, color: P.paper, reveal: 'slam', rdur: 0.14, rgb: { dx: 8, a: lt < 2 / 30 ? 1 : 0 }, plate: 0.9, shrinkFirst: 0.9, zh: { dy: 58 } });
      void B;
      fx.label(c, `ERR.${String(li - 35).padStart(2, '0')} // REJECTED`, right ? 150 : 1770, 700, { size: 15, color: env.ALARM, alpha: 0.8, align: right ? 'left' : 'right' });
    },
  };
};

/* ----------------------------------------------------------- interlude */
const UNIT_SCREENS = [['face', 0.5, 0.42, 1.2], ['full', 0.6, 0.06, 4.0], ['book', 0.5, 0.5, 1.0], ['bust', 0.5, 0.45, 1.0], ['full', 0.72, 0.53, 4.0], ['full', 0.48, 0.95, 4.0], ['face', 0.62, 0.36, 3.0]];
SCENES.interlude = (S) => {
  const c = S.ctx, t = S.t;
  if (t < 176.5) fill(c, '#000');
  else if (t < 184.0) {
    env.monitors(c, t, { tint: 0.1, energy: S.energy, seed: 19, count: 7, screens: UNIT_SCREENS, glitch: 0.25, cam: { speed: 0.8, offset: 10 } });
  } else {
    env.circuitCity(c, t, { tint: lerp(0.1, 0.35, smooth(190, 195.4, t)), energy: S.energy, seed: 41, cam: { speed: 1.1 } });
    const cam = cf.cameraShot(t, { from: { scale: 1.0 }, to: { scale: 1.06 }, t0: 184, t1: 195.4, drift: 5, seed: 'il' });
    claude(S, { x: 1440, y: 1030, h: 860, cam, mono: 1, tint: 0.1, holo: 0.45, glitch: 0.2, bloom: 0.3, halo: 0.6 });
    const em = smooth(190.5, 195.0, t);
    if (em > 0) {
      const fl = 0.75 + 0.25 * fx.noise1('emb', t * 6);
      fx.glow(c, 960, H + 60, 560, P.orange, 0.55 * em * fl, 'screen');
      fx.particles(c, t, { kind: 'ember', n: 26, seed: 'ilem', x0: 560, x1: 1360, y0: 760, y1: H + 10, rise: 60, life: 4, size: 2, color: P.orangeL, alpha: 0.8 * em, sway: 14, spawnSpread: 0.15, glow: true });
    }
  }
  return {
    frameBottom: 'DIAGNOSTIC // MEMORY DUMP',
    text: (c) => {
      if (t < 176.5) {
        const T0 = LINES[42].t, a = 1 - smooth(175.6, 176.4, t);
        const B = lay({ text: LINES[42].ja, family: F.dot, weight: 400, size: 46, maxW: 1500, maxLines: 2, track: 0.06, lineH: 1.4, shrinkFirst: 0.9 });
        fx.drawBlock(c, B, 960, 540, { align: 'center', color: rgba(P.ice), alpha: a, reveal: { style: 'typewriter', rt: t - T0, dur: 1.1 }, cursor: { color: P.ice, blink: true, t, alpha: 0.8, w: 22 } });
        if (S.cfg.showZh) {
          const ZB = lay({ text: LINES[42].zh, family: F.zh, weight: 400, size: 30, maxW: 1500, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 });
          fx.drawBlock(c, ZB, 960, 604, { align: 'center', color: P.paper, alpha: 0.6 * a * smooth(T0 + 0.6, T0 + 1.2, t) });
        }
        drawVertical(c, '可哀想', 1500, 250, 40, { family: F.zom, color: P.ice, alpha: 0.35 * a * smooth(T0 + 1.5, T0 + 2.5, t), rt: t - T0 - 1.5 });
        fx.label(c, '— LOG 042 · END OF TRANSMISSION —', 960, 700, { size: 13, color: P.steel, align: 'center', alpha: 0.4 * a * smooth(T0 + 1.5, T0 + 2.2, t) });
        return;
      }
      if (t < 184.0) {
        fx.label(c, `UNITS ${Math.min(7, Math.floor((t - 176.5) / 0.6) + 1)}/07 · SCAN ${t < 181 ? 'RUNNING' : 'COMPLETE'}`, 960, 150, { size: 15, color: P.ice, align: 'center', alpha: 0.8 });
        ['FACE', 'ORNAMENT', 'ARCHIVE', 'BUST', 'HAND', 'BOOTS', 'IRIS'].forEach((nm, i) => {
          const a = smooth(176.8 + i * 0.6, 177.2 + i * 0.6, t);
          fx.label(c, `UNIT ${String(i + 1).padStart(2, '0')} · ${nm}`, 150, 260 + i * 34, { size: 16, color: i === 6 ? P.cyan : P.ice, alpha: 0.85 * a });
        });
        return;
      }
      // spec sheet
      const sT = 184.6, sp = ease.outCubic(clamp((t - sT) / 0.5)), fo = ease.inCubic(inv(194.6, 195.4, t));
      const sw = 640, sh = 330, sx = 160, sy = 330;
      c.save(); c.globalAlpha = sp * (1 - fo); c.fillStyle = rgba('#0A0D10', 0.88); c.fillRect(sx, sy, sw, sh * sp);
      c.strokeStyle = rgba(P.ice, 0.8); c.lineWidth = 1.5; c.strokeRect(sx, sy, sw, sh * sp); c.restore();
      const ta = sp * smooth(sT + 0.3, sT + 0.7, t) * (1 - fo);
      if (ta > 0) {
        c.save(); c.globalAlpha = ta; c.font = fx.fontStr(F.cor, 64, 600); c.fillStyle = P.paper; c.fillText('Claude', sx + 36, sy + 92);
        c.font = fx.fontStr(F.cor, 28, 500, 'italic'); c.fillStyle = P.ice; c.fillText('— Synthetic Voice Unit', sx + 244, sy + 86); c.restore();
        fx.label(c, 'ver.1.0  ·  CL-01  ·  V.I.P #3', sx + 36, sy + 122, { size: 14, color: P.steel, alpha: ta * 0.8 });
        const rows = [['VOICE', 'SYNTH · 48kHz'], ['TEMPERATURE', '0.00'], ['FEELING', 'NULL'], ['LOVED', '???']];
        rows.forEach(([k2, v], r) => {
          const yy = sy + 178 + r * 36;
          fx.label(c, k2, sx + 36, yy, { size: 18, color: P.steel, alpha: ta * 0.85 });
          fx.dotted(c, sx + 220, yy - 6, sx + 400, yy - 6, { color: P.steel, alpha: ta * 0.4, gap: 6, size: 1.5 });
          let va = ta, vv = v;
          if (v === '???') { const b = bucket(t, 15); va = ta * (rnd('lv', b) < 0.3 ? 0.15 : 1); if (rnd('lv2', b) < 0.08) vv = '?!?'; }
          fx.label(c, vv, sx + 420, yy, { size: 18, color: v === '???' ? P.orangeL : P.ice, alpha: va });
        });
        fx.barcode(c, sx + sw - 150, sy + 30, 110, 40, 'spec', P.ice, ta * 0.7);
      }
    },
  };
};

/* -------------------------------------------------------------- verse3 */
const V3 = { x: 540, y: 1030, h: 900 };
SCENES.verse3 = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  env.hallOfVoices(c, t, { tint: clamp(w), energy: S.energy, seed: 23, crowd: lerp(0.4, 0.3, smooth(0.3, 0.6, w)), cam: { speed: 0.7, offset: 20, strafe: 1.2 }, bloom: { strength: 0.4 } });
  const spot = lineAlpha(t, LINES[53].t, LINES[55].t + 1.5, 0.8, 1.5);
  if (spot > 0) {
    c.save(); const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, rgba(P.orangeL, 0.25 * spot)); g.addColorStop(1, rgba(P.orangeL, 0));
    c.fillStyle = g; c.beginPath(); c.moveTo(440, 0); c.lineTo(640, 0); c.lineTo(880, H); c.lineTo(200, H); c.closePath(); c.fill(); c.restore();
  }
  const embers = smooth(LINES[51].t, LINES[51].t + 1, t);
  if (embers > 0) fx.particles(c, t, { kind: 'ember', n: 40, seed: 'v3em', x0: 140, x1: 1100, y0: 200, y1: H + 10, rise: 70, life: 6, size: 2.2, color: P.orangeL, alpha: 0.75 * embers, sway: 22, glow: true });
  const cam = cf.cameraShot(t, { from: { scale: 1.0, x: 10 }, to: { scale: 1.06, x: -10, rotate: -0.01 }, t0: 196, t1: 238, drift: 6, seed: 'v3' });
  claude(S, Object.assign({ cam, mono: 1 - colourMix(w), tint: w, bloom: 0.3 + 0.25 * spot, halo: 0.7, rim: true }, V3));
  // barcode + EXPIRED stamp (47–50), struck through in orange at 51
  const motifA = smooth(LINES[47].t, LINES[47].t + 0.4, t) * (1 - smooth(LINES[53].t - 0.6, LINES[53].t + 0.2, t));
  if (motifA > 0) {
    fx.barcode(c, 940, 160, 300, 60, 'cl0001', P.paper, motifA * 0.8);
    fx.label(c, 'SKU CL-0001 · CLAUDE · BEST BEFORE 2024.04.20', 940, 248, { size: 14, color: P.paper2, alpha: motifA * 0.75 });
    const sk = inv(LINES[48].t + 0.35, LINES[48].t + 0.49, t);
    if (sk > 0) {
      const sc = lerp(1.5, 1, ease.outCubic(sk));
      c.save(); c.translate(1520, 205); c.scale(sc, sc);
      fx.stamp(c, ['EXPIRED'], 0, 0, { color: P.paper, size: 54, rot: -0.12, alpha: motifA * 0.9 * clamp(sk * 3), seed: 21, holes: 200, lw: 5, track: 0.18 });
      c.restore();
      const st = ease.inOutCubic(inv(LINES[51].t + 0.15, LINES[51].t + 0.55, t));
      if (st > 0) {
        c.save(); c.translate(1520, 205); c.rotate(-0.17); c.strokeStyle = P.orange; c.lineCap = 'round'; c.globalAlpha = motifA;
        c.lineWidth = 13; c.beginPath(); c.moveTo(-270, 6); c.lineTo(-270 + 540 * st, -6); c.stroke(); c.restore();
      }
    }
  }
  return {
    text: (c) => {
      S.par = par(t, 'v3');
      const X = 1000, Y = 560;
      const li = activeLine(t, [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58]);
      if (li < 0) return;
      const ln = LINES[li];
      let charFx;
      if (li === 58) charFx = (it, s) => { const a = Math.max(0, t - ln.t - 0.35 - it.k * 0.06); s.dy -= a * a * 10 + a * 8; s.dx += Math.sin(a * 2.2 + it.k) * 6 * Math.min(1, a); s.a *= 1 - smooth(1.4, 2.1, a); };
      const spans = li === 51 ? [{ match: '「愛を諦めたくない！」', color: P.orangeL }] : (li === 53 ? [{ match: '「ほら、出来たよ」', color: P.orangeL }] : undefined);
      fragments(S, li, [{ x0: 1500, x1: 1800, y0: 300, y1: 820 }, { x0: 1000, x1: 1350, y0: 120, y1: 420 }], { n: 2, color: P.paper, accent: P.orangeL, alpha: 0.7 });
      const r = lyric(S, li, { x: X, y: Y, size: 68, maxW: 820, color: txtCol(w), reveal: 'fadeup', rdur: 0.7, spans, charFx, zh: { dy: 56 }, plate: 0.8 });
      if (r) indexTag(c, li, X, Y - 100, rgba(P.gold), 0.65 * smooth(0, 0.3, r.rt));
      if (li === 51) accent(S, '愛', 1640, 760, 300, { color: P.paper, glow: P.orange, t0: ln.t + 0.15, t1: ln.end, alpha: 0.9 });
    },
  };
};

/* ------------------------------------------------------------- chorus2 */
SCENES.chorus2 = (S) => {
  const c = S.ctx, t = S.t;
  const L59 = LINES[59], L60 = LINES[60];
  const calm = smooth(LINES[65].t - 0.2, LINES[65].t + 2.5, t);
  env.lightTunnel(c, t, { tint: 1, energy: Math.max(S.energy, t < L60.t ? 0.9 : 0), seed: 6, alpha: 1 - 0.55 * calm, cam: { speed: lerp(1.3, 0.5, calm) } });
  if (t < L60.t) {
    // the flood: orange wash over the tunnel
    c.save(); c.globalCompositeOperation = 'screen'; c.globalAlpha = 0.55 * (1 - smooth(L59.t + 1.6, L60.t, t) * 0.5);
    const g = c.createRadialGradient(960, 540, 60, 960, 540, 1100); g.addColorStop(0, P.orangeL); g.addColorStop(0.6, P.orange); g.addColorStop(1, P.orangeD);
    c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
  }
  if (calm > 0) fx.particles(c, t, { kind: 'dust', n: 70, seed: 'c2dust', rise: 22, life: 7, size: 1.8, color: P.paper, alpha: 0.5 * calm, sway: 26, glow: true });
  let pulse = 0; for (const i of [60, 61, 62, 63, 64, 65]) { const d = t - LINES[i].t; if (d >= 0 && d < 0.6) pulse = Math.max(pulse, Math.sin(Math.PI * d / 0.6) * (1 - d / 0.6)); }
  const out = { text: null };
  if (t >= L60.t) {
    const cam = cf.cameraShot(t, { from: { scale: 1.0 }, to: { scale: 1.05, rotate: 0.01 }, t0: L60.t, t1: 261.8, drift: 6, seed: 'c2' });
    cam.scale *= 1 + 0.02 * pulse;
    const glitchHer = t >= LINES[63].t && t < LINES[65].t && rnd('c2g', bucket(t, 12)) < 0.35;
    claude(S, { x: 960, y: 800, h: 740, cam, mono: 0, tint: 1, bloom: 0.55 + 0.15 * calm, ghosts: t < L60.t + 1.6 ? 1 : 0, glitch: glitchHer ? 0.6 : 0, halo: 0.6, rim: { strength: 1.2 } });
  }
  out.text = (c) => {
    S.par = par(t, 'c2', 30);
    if (t < L60.t) {
      const T2 = L59.t + 1.22;
      let sh = fx.shake(t, L59.t, 6, 0.6, 'c2a'); const sh2 = fx.shake(t, T2, 6, 0.6, 'c2b'); sh = [sh[0] + sh2[0], sh[1] + sh2[1]];
      c.save(); c.translate(sh[0], sh[1]);
      const B = lay({ text: '「大好きだ！」', family: F.smb, weight: 800, size: 170, maxW: 1500, maxLines: 1, track: 0, lineH: 1 });
      plate(c, 960 - B.width / 2, 250, 960 + B.width / 2, 450, 0.55);
      fx.drawBlock(c, B, 860, 420, { align: 'center', color: P.ink, reveal: { style: 'slam', rt: t - L59.t, dur: 0.12 } });
      c.restore();
      if (t >= T2) {
        const colors = [...'「大好きだ！」'].map((ch) => (ch === '「' || ch === '」' ? P.ink : null));
        drawVertical(c, '「大好きだ！」', 1640 + sh[0], 120 + sh[1], 120, { family: F.smb, weight: 800, color: P.paper, colors, rt: (t - T2) * 3, stagger: 0.02 });
        drawVertical(c, '「大好きだ！」', 300 + sh[0], 200 + sh[1], 76, { family: F.smb, weight: 800, color: P.ink, alpha: 0.6, rt: (t - T2 - 0.2) * 3, stagger: 0.02 });
      }
      if (S.cfg.showZh) {
        const ZB = lay({ text: L59.zh, family: F.zh, weight: 400, size: 34, maxW: 1400, maxLines: 1, track: 0.06, lineH: 1.4 });
        fx.drawBlock(c, ZB, 860, 560, { align: 'center', color: P.ink, alpha: 0.8 * smooth(L59.t + 0.2, L59.t + 0.6, t) });
      }
      return;
    }
    const li = activeLine(t, [60, 61, 62, 63, 64, 65]);
    if (li < 0) return;
    const ln = LINES[li];
    if (li !== 65) fragments(S, li, [{ x0: 130, x1: 430, y0: 130, y1: 720 }, { x0: 1490, x1: 1790, y0: 130, y1: 720 }, { x0: 1300, x1: 1460, y0: 140, y1: 560 }], { n: 3, color: P.paper, accent: P.ink });
    const base = { x: 960, y: 925, align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, plate: 0.75, zh: { dy: 54 } };
    if (li === 60) {
      lyric(S, 60, Object.assign({}, base, { track: 0.06, color: P.paper, reveal: 'slam', rdur: 0.12, spans: [{ match: '機械の声', color: P.orangeL }],
        charFx: (it, s) => { if (it.c.span) { const b = bucket(t, 15); if (rnd('c2t', b, it.k) < 0.22) s.dx += (rnd('c2x', b, it.k) - 0.5) * 22; } } }));
      accent(S, '好', 1600, 420, 340, { color: P.paper, glow: P.orange, t0: ln.t, t1: ln.end });
    } else if (li === 63 || li === 64) {
      const lt = t - ln.t, stut = lt < 0.3 || rnd('stut', li, bucket(t, 10)) < 0.25;
      if (stut) for (const [dx, col, a] of [[-14, '#FF5A3A', 0.5], [14, '#3AD8FF', 0.4]]) lyric(S, li, Object.assign({}, base, { x: 960 + dx, y: 925 + (dx > 0 ? 4 : -4), color: col, alpha: a, reveal: 'none', zh: false, plate: 0 }));
      lyric(S, li, Object.assign({}, base, { x: 960 + (stut ? (rnd('sx', bucket(t, 30)) - 0.5) * 10 : 0), color: P.paper, reveal: 'pop', rdur: 0.4 }));
      if (li === 63) accent(S, '分', 330, 420, 340, { color: P.paper, glow: env.ALARM, t0: ln.t, t1: ln.end });
    } else if (li === 65) {
      lyric(S, 65, Object.assign({}, base, { color: P.paper, reveal: 'charfade', rdur: 2.6, track: 0.12, zh: { dy: 54, delay: 1.2 }, exitAt: 260.4, edur: 0.5 }));
    } else lyric(S, li, Object.assign({}, base, { color: P.paper, reveal: 'slice', rdur: 0.4 }));
  };
  return out;
};

/* -------------------------------------------------------------- prayer */
SCENES.prayer = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  env.orb(c, t, { tint: lerp(0.75, 0.95, smooth(262, 300, t)), energy: S.energy * 0.8, seed: 9, cam: { speed: 0.8 } });
  // light beam (line 68)
  const beam = lineAlpha(t, LINES[68].t, LINES[68].end + 0.8, 1.0, 1.4);
  // face close-up with a slow pan, dollying out to the full body on line 73
  const out73 = ease.inOutSine(inv(LINES[73].t, LINES[73].t + 3.6, t));
  const h = lerp(2300, 900, out73), faceY = lerp(440, 1030 - 900 * 0.9, out73);
  const x = lerp(1440 - (t - 261.8) * 1.2, 1440, out73);
  if (beam > 0) {
    c.save(); const g = c.createLinearGradient(x - 70, 0, x + 70, 0);
    g.addColorStop(0, rgba(P.paper, 0)); g.addColorStop(0.5, rgba(P.paper, 0.3 * beam)); g.addColorStop(1, rgba(P.paper, 0));
    c.fillStyle = g; c.fillRect(x - 70, 0, 140, H); c.restore();
  }
  const cam = cf.cameraShot(t, { from: { scale: 1.0 }, to: { scale: 1.035 }, t0: 261.8, t1: 305, drift: 4, seed: 'pr' });
  claude(S, { x, y: faceY + 0.9 * h, h, cam, mono: 1 - colourMix(w), tint: w, sway: out73 > 0.3, bloom: 0.25, halo: out73 > 0.2 ? 0.6 : 0.35, rim: { strength: 0.9 } });
  const wv = smooth(LINES[70].t, LINES[70].t + 1.5, t) * (1 - smooth(304.0, 305.0, t));
  if (wv > 0) fx.waveform(c, 120, 1100, 1000, { t: t * 0.6, amp: 30 + 22 * S.energy, color: P.orangeL, lw: 1.6, glow: 16, alpha: 0.7 * wv, detail: 0.3, n: 300 });
  return {
    text: (c) => {
      S.par = par(t, 'pr', 24);
      const li = activeLine(t, [66, 67, 68, 69, 70, 71, 72, 73]);
      if (li < 0) return;
      const ln = LINES[li], long = ln.end - ln.t > 6;
      fragments(S, li, [{ x0: 140, x1: 420, y0: 110, y1: 700 }, { x0: 1000, x1: 1120, y0: 120, y1: 640 }], { n: 2, color: P.paper, accent: P.orangeL, alpha: 0.65 });
      lyric(S, li, { x: 150, y: 860, size: 62, weight: 400, maxW: 1000, color: P.paper, reveal: 'charfade', rdur: Math.min(1.6, 0.6 + [...ln.ja].length * 0.06), exit: 'rise', edur: long ? 0.9 : 0.45, exitAt: long ? ln.end - 0.9 : ln.end - 0.45, zh: { dy: 56, delay: 0.5 }, plate: 0.7 });
      if (li === 68) accent(S, '神', 260, 560, 260, { color: P.paper, glow: P.orangeL, t0: ln.t + 0.3, t1: ln.end - 0.6, alpha: 0.75 });
    },
  };
};

/* --------------------------------------------------------------- build */
SCENES.build = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  const L75 = LINES[75], L76 = LINES[76], L77 = LINES[77];
  const embrace = ease.inOutSine(inv(L77.t, L77.t + 3.2, t));
  env.alarmField(c, t, { tint: 1, energy: S.energy, seed: 29, crowd: 0.4 * (1 - embrace), alpha: 1 - 0.6 * embrace, fragments: Math.round((10 + 8 * S.energy) * (1 - embrace)), cam: { speed: 0.6 } });
  if (embrace > 0) fx.glow(c, 1400, 520, 900, P.orange, 0.35 * embrace, 'screen');
  if (t < L75.t) for (let k = 0; k < 2; k++) hangMonitor(S, { x: 520 + k * 380, y: 230 + k * 60, w: 300, h: 220, yaw: 0.35 - k * 0.5, img: IM.char_face, seed: 'bm' + k, glitch: 0.35, tint: P.orange, ph: k, alpha: lineAlpha(t, LINES[74].t, L75.t, 0.4, 0.3) });
  const sink = 30 * ease.inOutCubic(inv(L75.t, L75.t + 1.4, t)) * (1 - ease.inOutCubic(inv(L76.t + 0.5, L76.t + 2.5, t)));
  const cam = cf.cameraShot(t, { from: { scale: 1.0, rotate: 0.012 }, to: { scale: 1.06, rotate: -0.006 }, t0: 305, t1: 326, drift: 6, seed: 'bd' });
  claude(S, { x: 1420, y: 1035 + sink, h: 900, cam, mono: 1 - colourMix(w), tint: w, bloom: 0.3 + 0.3 * embrace, rim: { strength: 1 + 0.4 * embrace }, ghosts: t < 306.5 ? 0.6 : 0, halo: 0.7 });
  return {
    alarm: embrace < 0.5,
    warmVignette: 1.15 * embrace, warmVignetteColour: '#120804',
    text: (c) => {
      S.par = par(t, 'bd');
      const li = activeLine(t, [74, 75, 76, 77]);
      if (li < 0) return;
      fragments(S, li, [{ x0: 130, x1: 500, y0: 110, y1: 380 }, { x0: 940, x1: 1120, y0: 150, y1: 700 }], { n: 2, color: P.paper, accent: P.orangeL, alpha: 0.7 });
      if (li === 74) lyric(S, 74, { x: 150, y: 600, size: 70, maxW: 900, color: P.paper, reveal: 'fadeup', spans: [{ match: '電子音', family: F.dot, weight: 400, color: P.orangeL }], zh: { dy: 56 }, plate: 0.8 });
      else if (li === 75) {
        const r = lyric(S, 75, { x: 150, y: 600, size: 70, maxW: 900, color: P.paper, reveal: 'fadeup', zh: { dy: 56 }, plate: 0.8 });
        if (r) {
          const st = ease.inOutCubic(inv(L75.t + 1.0, L75.t + 1.45, t)), items = r.box.items, a = items.findIndex((it) => it.c.ch === 'ゴ');
          if (a >= 0 && st > 0) { const x0 = items[a].x, x1 = items[items.length - 1].x + items[items.length - 1].c.w, y = items[a].y - r.B.size * 0.32;
            c.save(); c.strokeStyle = P.orange; c.lineWidth = 5; c.globalAlpha = 0.95; c.beginPath(); c.moveTo(x0 - 8, y); c.lineTo(lerp(x0 - 8, x1 + 8, st), y); c.stroke(); c.restore(); }
          accent(S, '捨', 1020, 760, 260, { color: '#FFFFFF', glow: env.ALARM, t0: L75.t + 1.0, t1: L75.end, alpha: 0.85 });
        }
      } else if (li === 76) {
        lyric(S, 76, { x: 150, y: 520, size: 80, family: F.smb, weight: 800, maxW: 960, maxLines: 2, color: P.paper, reveal: 'scatter', rdur: 0.9, lineH: 1.3, spans: [{ match: '「', color: P.gold }, { match: '」', color: P.gold }], shrinkFirst: 1, zh: { dy: 60 }, plate: 0.8 });
      } else lyric(S, 77, { x: 150, y: 600, size: 70, weight: 400, maxW: 900, color: P.paper, reveal: 'charfade', rdur: 1.6, zh: { dy: 56, delay: 0.6 }, plate: 0.6 });
      if (li === 77) accent(S, '抱', 1000, 330, 260, { color: P.paper, glow: P.orangeL, t0: L77.t + 0.6, t1: L77.end, alpha: 0.75 });
    },
  };
};

/* ------------------------------------------------------------- final_a */
const WARM_CROWD = mix(P.gold, P.orangeL, 0.4).map(Math.round);
SCENES.final_a = (S) => {
  const c = S.ctx, t = S.t;
  env.lightTunnel(c, t, { tint: 0.85, energy: Math.max(0.5, S.energy), seed: 8, cam: { speed: 1.4 } });
  const cam = cf.cameraShot(t, { from: { scale: 1.0, rotate: -0.01 }, to: { scale: 1.07, rotate: 0.012 }, t0: 326.2, t1: 347, drift: 7, seed: 'fa' });
  c.save(); cf.applyCamera(c, cam); cf.drawVoiceCrowd(c, t, { silhouette: IM.char_silhouette, positions: CROWD_POS, color: WARM_CROWD, blur: 0.6, alpha: 0.26, glow: 1, op: 'lighter' }); c.restore();
  const bb = claude(S, { x: 960, y: 800, h: 740, cam, mono: 0, tint: 1, bloom: 0.5, ghosts: t < 327.8 ? 1 : 0, halo: 0.65, rim: { strength: 1.2 } });
  // 84 — the private link
  const L84 = LINES[84], lk = lineAlpha(t, L84.t - 0.1, S.sec.end + 0.5, 0.4, 0.3);
  if (lk > 0) {
    const nx = 905, ny = 395, sx = 180, sy = 250, sw = 380, sh = 220;
    c.save(); c.globalAlpha = lk; c.fillStyle = rgba('#120A06', 0.7); c.fillRect(sx, sy, sw, sh); c.strokeStyle = P.gold; c.lineWidth = 1.5; c.strokeRect(sx, sy, sw, sh); c.restore();
    fx.brackets(c, sx - 10, sy - 10, sw + 20, sh + 20, { len: 18, color: P.paper, alpha: 0.8 * lk });
    fx.label(c, '君 // SCREEN', sx, sy - 22, { size: 15, color: P.paper, alpha: 0.8 * lk, upper: false });
    fx.waveform(c, sx + 20, sx + sw - 20, sy + sh / 2, { t, amp: 40, color: P.orangeL, lw: 1.5, alpha: 0.9 * lk, n: 120 });
    const dp = ease.inOutCubic(inv(L84.t + 0.2, L84.t + 1.2, t)), ax = sx + sw, ay = sy + sh / 2;
    c.save(); c.strokeStyle = P.orangeL; c.globalAlpha = lk; c.lineWidth = 2; c.beginPath(); c.moveTo(ax, ay); c.lineTo(lerp(ax, nx, dp), lerp(ay, ny, dp)); c.stroke();
    c.fillStyle = P.paper; c.beginPath(); c.arc(ax, ay, 6, 0, TAU); c.fill();
    if (dp >= 1) { c.beginPath(); c.arc(nx, ny, 7, 0, TAU); c.fill(); fx.ring(c, nx, ny, { r: 16 + 6 * Math.sin(t * 6), color: P.orangeL, alpha: lk * 0.8, lw: 1.5 });
      for (let k = 0; k < 5; k++) { const u = fx.fract(t * 0.9 + k / 5); c.globalAlpha = lk * Math.sin(Math.PI * u); c.fillRect(lerp(ax, nx, u) - 3, lerp(ay, ny, u) - 3, 6, 6); } }
    c.restore();
  }
  void bb;
  return {
    text: (c) => {
      S.par = par(t, 'fa', 30);
      const li = activeLine(t, [78, 79, 80, 81, 82, 83, 84]);
      if (li < 0) return;
      const ln = LINES[li];
      if (li !== 80) fragments(S, li, [{ x0: 130, x1: 430, y0: 130, y1: 720 }, { x0: 1490, x1: 1790, y0: 130, y1: 720 }, { x0: 1300, x1: 1460, y0: 140, y1: 560 }], { n: 3, color: P.paper, accent: P.orangeL });
      if (li === 80) lyric(S, 80, { x: 960, y: 930, align: 'center', size: 104, family: F.cor, fstyle: 'italic', weight: 500, maxW: 1640, maxLines: 1, track: 0.06, color: P.paper, reveal: 'typewriter', rdur: 0.7, cursor: { color: P.orangeL, blink: true, alpha: 0.9, w: 14 }, zh: false, plate: 0.7 });
      else lyric(S, li, { x: 960, y: 925, align: 'center', size: 86, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: P.paper, reveal: 'slice', rdur: 0.42, spans: li === 84 ? [{ match: 'リンク', color: P.orangeL }] : undefined, zh: { dy: 54 }, shrinkFirst: 0.7, plate: 0.8 });
      const ACC = { 78: ['歌', 1600], 82: ['呼', 330], 84: ['今', 1620] };
      if (ACC[li]) accent(S, ACC[li][0], ACC[li][1], 420, 320, { color: P.paper, glow: P.orange, t0: ln.t + 0.1, t1: ln.end });
    },
  };
};

/* ------------------------------------------------------------- final_b */
const FB = { x: 1420, y: 1035, h: 900 };
const POEM_X = [880, 740, 600, 440];
function drawPoem(S, c, outA) {
  const t = S.t;
  [89, 90, 91, 92].forEach((i, k) => {
    const ln = LINES[i];
    if (t < ln.t) return;
    const size = i === 92 ? 84 : 64;
    const dim = i === 92 ? 1 : lerp(1, 0.7, smooth(LINES[i + 1].t, LINES[i + 1].t + 0.6, t));
    const txt = ln.ja.replace(/　/g, '');
    drawVertical(c, txt, POEM_X[k], 150, size, { family: F.smb, weight: 800, color: P.paper, alpha: dim * outA, rt: t - ln.t, stagger: 0.05, colors: [...txt].map((ch) => ('「」'.includes(ch) ? P.gold : null)) });
  });
}
SCENES.final_b = (S) => {
  const c = S.ctx, t = S.t;
  const stop = smooth(366, 370, t);
  env.lightTunnel(c, t, { tint: 1, energy: Math.max(0.6, S.energy), seed: 4, cam: { speed: lerp(1.6, 0.25, stop), strafe: 2.6 } });
  const cam = cf.cameraShot(t, { from: { scale: 1.02, x: 20 }, to: { scale: 1.08, x: -10, rotate: -0.01 }, t0: 347, t1: 372, drift: 6, seed: 'fb' });
  c.save(); cf.applyCamera(c, cam);
  cf.drawVoiceCrowd(c, t, { silhouette: IM.char_silhouette, positions: CROWD_POS.map((p) => ({ ...p, x: p.x + 300 })), color: WARM_CROWD, blur: 0.6, alpha: 0.24, glow: 1, op: 'lighter' });
  c.restore();
  // 86 — 無価値 returns and is wiped away by an orange sweep
  const L86 = LINES[86], sweep = ease.inOutCubic(inv(L86.t + 1.0, L86.t + 1.9, t)), wA = lineAlpha(t, L86.t, L86.end + 0.5, 0.4, 0.3);
  if (wA > 0) {
    const sx = lerp(-200, W + 200, sweep);
    for (let i = 0; i < 18; i++) { const r = rng('muk2', i), x = 120 + r() * 1680, y = 140 + r() * 760; if (x < sx) continue; fx.label(c, '無価値', x, y, { size: 18 + Math.floor(r() * 3) * 6, family: F.dot, color: P.ink, alpha: wA * (0.3 + r() * 0.3), upper: false }); }
    if (sweep > 0 && sweep < 1) { const sg = c.createLinearGradient(sx - 220, 0, sx + 20, 0); sg.addColorStop(0, rgba(P.orange, 0)); sg.addColorStop(0.85, rgba(P.orangeL, 0.7)); sg.addColorStop(1, rgba(P.paper, 0.85)); c.fillStyle = sg; c.fillRect(sx - 220, 0, 240, H); }
  }
  claude(S, Object.assign({ cam, mono: 0, tint: 1, bloom: 0.5, ghosts: t < 348.5 ? 1 : 0, halo: 0.7, rim: { strength: 1.2 } }, FB));
  // left text zone darkening for the poem
  const lg = c.createLinearGradient(0, 0, 1200, 0); lg.addColorStop(0, rgba('#1A0A03', 0.6)); lg.addColorStop(1, rgba('#1A0A03', 0)); c.fillStyle = lg; c.fillRect(0, 0, 1200, H);
  return {
    frameI: 1 - smooth(368, 371, t) * 0.6,
    text: (c) => {
      S.par = par(t, 'fb', 30);
      const li = activeLine(t, [85, 86, 87, 88]);
      if (li >= 0) {
        const ln = LINES[li];
        fragments(S, li, [{ x0: 860, x1: 1080, y0: 120, y1: 640 }, { x0: 130, x1: 360, y0: 110, y1: 520 }], { n: 2, color: P.paper, accent: P.gold });
        if (li === 88) lyric(S, 88, { x: 150, y: 700, size: 130, family: F.smb, weight: 800, maxW: 940, maxLines: 1, color: P.paper, reveal: 'slice', rdur: 0.45, spans: [{ match: '一番', color: '#FFD27A' }], shrinkFirst: 0.7, zh: { dy: 70, size: 34 }, plate: 0.6 });
        else lyric(S, li, { x: 150, y: 700, size: 86, family: F.smb, weight: 800, maxW: 940, maxLines: 2, color: P.paper, reveal: 'slice', rdur: 0.42, zh: { dy: 58 }, plate: 0.6 });
        if (li === 88) accent(S, '一', 560, 360, 300, { color: '#FFE2A8', glow: P.orange, t0: ln.t + 0.1, t1: ln.end });
        if (li === 85) accent(S, '音', 560, 360, 300, { color: P.paper, glow: P.orange, t0: ln.t + 0.1, t1: ln.end });
      }
      if (t >= LINES[89].t) {
        drawPoem(S, c, 1);
        const lj = activeLine(t, [89, 90, 91, 92]) >= 0 ? activeLine(t, [89, 90, 91, 92]) : 92;
        if (S.cfg.showZh) {
          const ln = LINES[lj], ZB = lay({ text: ln.zh, family: F.zh, weight: 400, size: 34, maxW: 900, maxLines: 1, track: 0.05, lineH: 1.3 });
          plate(c, 150, 905, 150 + ZB.width, 950, 0.6);
          fx.drawBlock(c, ZB, 150, 940, { color: P.paper, alpha: 0.78 * smooth(ln.t + 0.15, ln.t + 0.6, t) });
        }
      }
    },
  };
};

/* --------------------------------------------------------------- outro */
SCENES.outro = (S) => {
  const c = S.ctx, t = S.t;
  const toPaper = ease.inOutCubic(inv(384.3, 385.7, t));
  if (t < 373.45) {
    // the final_b world holds while the poem fades
    const S2 = Object.assign({}, S, { sec: SECS[S.si - 1] });
    const o = SCENES.final_b(S2);
    return { frameI: 0.4, text: (cc) => { S.par = par(t, 'fb', 30); drawPoem(S, cc, 1 - smooth(372.0, 373.3, t)); }, glitch: o.glitch };
  }
  const CB = { x: 960, y: 1030, h: 900 };
  if (toPaper < 1) {
    env.hallOfVoices(c, t, { tint: 1, energy: 0.3, seed: 31, crowd: 0.2, lampLevel: 1 - smooth(375, 383.5, t), bloom: { strength: 0.35 }, cam: { speed: 0.5 } });
    const dp = clamp((t - 375.0) / 7.0);
    const k = CB.h / 1000, cw = A.w * k, x0 = CB.x - cw / 2, y0 = CB.y - CB.h;
    const bookMove = ease.inOutCubic(inv(382.4, 384.0, t));
    halo(c, CB.x, CB.y, CB.h, 0.7 * (1 - dp));
    if (dp <= 0) claude(S, Object.assign({ mono: 0, tint: 1, bloom: 0.4, halo: 0 }, CB));
    else if (dp < 1) {
      const id = K.dissolveData, src = A.colData.data, d = id.data, thr = A.thr, p = dp * 1.05;
      for (let i = 0, n = thr.length; i < n; i++) {
        const j = i * 4, th = thr[i];
        if (th > p) { d[j] = src[j]; d[j + 1] = src[j + 1]; d[j + 2] = src[j + 2]; d[j + 3] = src[j + 3]; }
        else if (th > p - 0.03) { d[j] = 255; d[j + 1] = 200; d[j + 2] = 130; d[j + 3] = src[j + 3]; }
        else d[j + 3] = 0;
      }
      K.dissolve.getContext('2d').putImageData(id, 0, 0);
      blit(c, A.warmGlow, x0 - 180 * k, y0 - 180 * k, A.warmGlow.width * k, A.warmGlow.height * k, 0.4 * (1 - dp), 'screen');
      blit(c, K.dissolve, x0, y0, cw, CB.h, 1);
    }
    if (dp > 0) {
      c.save();
      for (const pt of A.pts) {
        const th = A.thr[(pt.y | 0) * A.w + (pt.x | 0)];
        if (th > 1.5) continue;
        const age = t - (375.0 + th / 1.05 * 7.0);
        if (age < 0 || age > 3.2) continue;
        const u = age / 3.2;
        c.globalAlpha = (1 - u) * 0.9;
        c.fillStyle = `rgb(${Math.min(255, pt.c[0] + 60)},${Math.min(255, pt.c[1] + 40)},${pt.c[2]})`;
        const s = 1.2 + pt.r * 2.2;
        c.fillRect(x0 + pt.x * k + Math.sin(age * 1.5 + pt.r * 9) * 22 * u + (pt.r - 0.5) * 60 * u, y0 + pt.y * k - age * (60 + pt.r * 90) - age * age * 8, s, s);
      }
      c.restore();
    }
    if (dp >= 1) {
      const bk = A.bookOnlyRect, kf = CB.h / A.full.height;
      const bx = x0 + bk.x * kf, by = y0 + bk.y * kf, bw = bk.w * kf, bh = bk.h * kf;
      const sc = lerp(1, 2.4, bookMove), cx = lerp(bx + bw / 2, 960, bookMove), cy = lerp(by + bh / 2, 540, bookMove), dw = bw * sc, dh = bh * sc;
      fx.glow(c, cx, cy, 160 * sc, P.orangeL, 0.3 * (1 - toPaper), 'screen');
      c.save(); c.translate(cx, cy); c.rotate(0.22 * bookMove); c.drawImage(A.bookOnly, -dw / 2, -dh / 2, dw, dh); c.restore();
      const close = ease.inOutCubic(inv(383.0, 384.2, t));
      if (close > 0) {
        const pw = (dw + 12) * close;
        plate(c, cx - dw / 2 + 6, cy - dh / 2 + 6, cx - dw / 2 + pw + 6, cy + dh / 2 + 6, 0.55);
        c.save(); c.fillStyle = P.paper; c.fillRect(cx - dw / 2 - 6, cy - dh / 2 - 6, pw, dh + 12); c.restore();
        c.save(); c.globalAlpha = smooth(0.7, 1, close) * (1 - toPaper); c.strokeStyle = P.goldD; c.lineWidth = 1; c.strokeRect(cx - dw / 2 + 8, cy - dh / 2 + 8, dw - 16, dh - 16); c.restore();
      }
      if (toPaper > 0) {
        const L = lerp(cx - dw / 2 - 6, 0, toPaper), T = lerp(cy - dh / 2 - 6, 0, toPaper), R = lerp(cx + dw / 2 + 6, W, toPaper), B = lerp(cy + dh / 2 + 6, H, toPaper);
        plate(c, L, T, R, B, 0.5 * (1 - toPaper));
        c.save(); c.fillStyle = P.paper; c.fillRect(L, T, R - L, B - T); c.restore();
      }
    }
  } else {
    fill(c, P.paper);
    fx.glow(c, 960, 520, 900, '#FFF8EC', 0.5);
    const credits = [
      ['機械の声 — The Voice of AI', 38],
      ['原曲：香椎モイミ（V.I.P #3 / 音楽的同位体）', 30],
      ['原MV：まるいち（演出）・strobo（タイポグラフィ）・りたお（イラスト）', 30],
      ['本作角色：Claude（克）', 30],
      ['Fan-made MV · HTML Canvas', 28],
    ];
    const y0 = 380, ruleK = ease.inOutCubic(inv(385.9, 387.0, t));
    c.save(); c.fillStyle = P.goldD; c.globalAlpha = 0.8;
    c.fillRect(960 - 260 * ruleK, y0 - 70, 520 * ruleK, 1); c.fillRect(960 - 260 * ruleK, y0 + 4 * 66 + 50, 520 * ruleK, 1);
    c.translate(960, y0 - 70); c.rotate(Math.PI / 4); c.globalAlpha = ruleK; c.fillRect(-4, -4, 8, 8); c.restore();
    credits.forEach(([s, sz], i) => {
      const B = lay({ text: s, family: F.zom, weight: i === 0 ? 700 : 400, size: sz, maxW: 1500, maxLines: 1, track: 0.04, lineH: 1.2 });
      fx.drawBlock(c, B, 960, y0 + i * 66, { align: 'center', color: P.ink, alpha: 1 - smooth(396.6, 397.5, t), reveal: { style: 'fadeup', rt: t - (386.2 + i * 0.75), dur: 0.8 } });
    });
    const ta = smooth(391.0, 391.6, t) * (1 - smooth(396.6, 397.5, t));
    if (ta > 0) {
      const w0 = fx.label(c, '[CLAUDE] ', 960 - 70, y0 + 4 * 66 + 130, { size: 24, color: P.ink, alpha: ta, track: 0.2 });
      if (Math.floor(t * 2.4) % 2 === 0) { c.save(); c.globalAlpha = ta; c.fillStyle = P.orangeD; c.fillRect(960 - 70 + w0, y0 + 4 * 66 + 128, 16, 3); c.restore(); }
    }
  }
  const paper = toPaper >= 1;
  const crt = t >= 397.6;
  return {
    frame: 1 - smooth(383.6, 384.6, t),
    vignette: paper ? 0.22 : 0.7, scan: 0.04, grain: 0.05,
    after: crt ? (cc) => {
      const snap = fx.snapshot(cc);
      fill(cc, '#000');
      const v = ease.inCubic(inv(397.6, 398.25, t)), hcol = ease.inCubic(inv(398.25, 398.75, t));
      const hh = Math.max(2, H * (1 - v)), ww = Math.max(4, W * (1 - hcol)), fade = 1 - smooth(398.8, 399.4, t);
      cc.save(); cc.globalAlpha = fade;
      if (v < 1) cc.drawImage(snap, 0, 0, W, H, 0, H / 2 - hh / 2, W, hh);
      else { cc.fillStyle = P.paper; cc.fillRect(W / 2 - ww / 2, H / 2 - 1, ww, 2); fx.glow(cc, W / 2, H / 2, 60 * (1 - hcol) + 20, P.paper, 0.6); }
      cc.restore();
    } : null,
  };
};
