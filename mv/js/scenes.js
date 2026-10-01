// scenes.js — one renderer per section id. Each renderer is a pure function of S.t.
import * as fx from './fx.js';

const { W, H, P, F, clamp, lerp, inv, smooth, ease, ek, rng, rnd, bucket, mix, rgba, ramp, blit, TAU } = fx;

let A = null, TL = null, LINES = null, SECS = null, warmth = null;
const K = {}; // scene caches

export function prepareScenes(o) {
  ({ A, TL, LINES, SECS, warmth } = o);
  const hex = fx.hexGridCanvas(W, H, 44, 1);
  K.hexIce = fx.tinted(hex, P.ice);
  K.hexGold = fx.tinted(hex, P.gold);
  K.edgesInk = fx.tinted(A.edges, P.ink);
  K.edgesIce = fx.tinted(A.edges, P.ice);
  K.edgesHiInk = fx.tinted(A.hi.edges, P.ink);
  K.faceRim = fx.blurred(A.face, 12, 60, P.orange);
  K.faceGlow = fx.blurred(A.face, 50, 160, P.orangeL);
  K.dissolve = fx.makeCanvas(A.w, A.h);
  K.dissolveData = K.dissolve.getContext('2d').createImageData(A.w, A.h);
  K.frame = fx.makeCanvas(W, H);
  K.tmp = fx.makeCanvas(W, H);
  // grain-ish noise tile for "noise overlay" text
  K.noise = fx.makeCanvas(256, 256);
  { const x = K.noise.getContext('2d'), d = x.createImageData(256, 256), r = rng('tn');
    for (let i = 0; i < 256 * 256; i++) { const v = r() < 0.5 ? 0 : 255; d.data[i * 4] = v; d.data[i * 4 + 1] = v; d.data[i * 4 + 2] = v; d.data[i * 4 + 3] = r() < 0.35 ? 255 : 0; }
    x.putImageData(d, 0, 0); }
  K.mono1000 = A.mono;
  // glowing silhouette: vertical ice gradient (bright head, cooler fading hem) + cool bloom
  K.silGrad = (() => {
    const k = fx.makeCanvas(A.w, A.h), x = k.getContext('2d');
    x.drawImage(A.sil, 0, 0);
    x.globalCompositeOperation = 'source-in';
    const g = x.createLinearGradient(0, 0, 0, A.h);
    g.addColorStop(0, '#F6FAFC'); g.addColorStop(0.35, '#E4EEF3'); g.addColorStop(0.75, 'rgba(190,212,224,0.82)'); g.addColorStop(1, 'rgba(159,179,191,0.55)');
    x.fillStyle = g; x.fillRect(0, 0, A.w, A.h);
    // faint inner edge-lines so the form reads (a ghost of the line art)
    x.globalCompositeOperation = 'source-atop'; x.globalAlpha = 0.12; x.drawImage(fx.tinted(A.edges, '#6F8796'), 0, 0);
    return k;
  })();
  K.bloomCool = fx.blurred(A.sil, 36, 150, fx.mix(P.ice, P.cyan, 0.45));
}

/* ================================================================ helpers */
const hudCol = (w) => mix(P.ice, P.gold, smooth(0.15, 0.8, w));
const txtCol = (w) => rgba(mix(P.ice, P.paper, smooth(0.08, 0.45, w)));
const bgCol = (w) => ramp([[0, P.coldInk], [0.12, '#11151A'], [0.3, '#1B1613'], [0.6, '#2A1A10'], [0.85, '#2E1C11'], [1, P.brown]], w);
const colourMix = (w) => smooth(0.3, 0.9, w);

function fill(c, colour, a = 1) { c.save(); c.globalAlpha = a; c.fillStyle = typeof colour === 'string' ? colour : rgba(colour); c.fillRect(0, 0, W, H); c.restore(); }
function vgrad(c, top, bottom, a = 1) {
  c.save(); c.globalAlpha = a;
  const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, rgba(top)); g.addColorStop(1, rgba(bottom));
  c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
}
function hexGrid(c, a, warmK = 0, mask = null) {
  if (a <= 0.003) return;
  c.save();
  if (warmK < 1) blit(c, K.hexIce, 0, 0, W, H, a * (1 - warmK));
  if (warmK > 0) blit(c, K.hexGold, 0, 0, W, H, a * warmK);
  c.restore();
  if (mask) { // darken edges of the grid with a radial mask
    c.save();
    const g = c.createRadialGradient(mask.x, mask.y, mask.r0, mask.x, mask.y, mask.r1);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, rgba(mask.colour, 1));
    c.globalAlpha = mask.a == null ? 0.85 : mask.a; c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
  }
}

// hand-made Japanese line breaks, used only when a line has to wrap
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
/** active line index among `list` at time t (or -1) */
function activeLine(t, list) {
  for (const i of list) if (t >= LINES[i].t && t < LINES[i].end) return i;
  return -1;
}
/** draw one lyric line (+ZH). Returns info or null when not visible. */
function lyric(S, i, o = {}) {
  const ln = LINES[i], t = S.t;
  const t0 = o.from != null ? o.from : ln.t, t1 = o.to != null ? o.to : ln.end;
  if (t < t0 || t >= t1) return null;
  const B = lay({
    text: o.text != null ? o.text : ln.ja, family: o.family || F.zom, weight: o.weight || 700, size: o.size || 72,
    maxW: o.maxW || 1600, maxLines: o.maxLines || 2, track: o.track || 0, lineH: o.lineH || 1.3, spans: o.spans,
    shrinkFirst: o.shrinkFirst == null ? 0.86 : o.shrinkFirst, lines: o.lines, style: o.fstyle, minSize: o.minSize,
  });
  const rt = t - t0;
  const n = B.nChars;
  const rdur = o.rdur || clamp(0.25 + n * 0.035, 0.4, 0.8);
  const early = o.exitAt != null;
  const edur = o.edur || (early ? 0.9 : 0.2);
  const exitStart = early ? o.exitAt : t1 - edur;
  const et = t - exitStart;
  const exit = et > 0 ? { style: o.exit || 'fade', et, dur: edur, seed: i } : null;
  const alpha = o.alpha == null ? 1 : o.alpha;
  const box = fx.drawBlock(S.ctx, B, o.x, o.y, {
    align: o.align || 'left', color: o.color || P.paper, alpha,
    reveal: { style: o.reveal || 'fadeup', rt, dur: rdur, seed: i * 7 + 1 }, exit,
    cursor: o.cursor ? Object.assign({ t }, o.cursor) : null, glow: o.glow, rgb: o.rgb, charFx: o.charFx,
    lightBg: o.lightBg, sliceAmp: o.sliceAmp, ruleColor: o.ruleColor,
  });
  let zbox = null;
  if (S.cfg.showZh && o.zh !== false && ln.zh) {
    const z = o.zh || {};
    const ZB = lay({ text: ln.zh, family: F.zh, weight: 400, size: z.size || 32, maxW: z.maxW || o.maxW || 1600, maxLines: 2, track: z.track == null ? 0.04 : z.track, lineH: 1.4, shrinkFirst: 0.8 });
    const zy = z.y != null ? z.y : o.y + (B.lines.length - 1) * B.lineH + (z.dy != null ? z.dy : Math.round(B.size * 0.36 + 30));
    const zx = z.x != null ? z.x : o.x;
    const za = (z.alpha == null ? 0.6 : z.alpha) * ease.inOutSine(clamp((rt - (z.delay == null ? 0.15 : z.delay)) / 0.5));
    zbox = fx.drawBlock(S.ctx, ZB, zx, zy, { align: z.align || o.align || 'left', color: z.color || P.paper, alpha: za * alpha, exit: exit ? { style: 'fade', et, dur: edur } : null });
  }
  return { box, zbox, B, rt, et, t0, t1, n };
}
/** draw the character. o: {cx, by, h, mode, a, cm (colour mix), cold, rim, warm, paperGlow, bloom, img} */
function drawChar(S, o) {
  const c = S.ctx, h = o.h, k = h / 1000, w = A.w * k;
  const x = o.cx - w / 2, y = o.by - h;
  const a = o.a == null ? 1 : o.a;
  const hi = h > 1060;
  if (o.warm) blit(c, A.warmGlow, x - 180 * k, y - 180 * k, A.warmGlow.width * k, A.warmGlow.height * k, o.warm * a, 'screen');
  if (o.paperGlow) blit(c, A.paperGlow, x - 140 * k, y - 140 * k, A.paperGlow.width * k, A.paperGlow.height * k, o.paperGlow * a);
  if (o.rim) blit(c, A.rim, x - 40 * k + 6, y - 40 * k + 3, A.rim.width * k, A.rim.height * k, o.rim * a);
  const mode = o.mode || 'mono';
  if (mode === 'sil') {
    blit(c, K.bloomCool, x - 150 * k, y - 150 * k, K.bloomCool.width * k, K.bloomCool.height * k, a * (o.bloom == null ? 0.55 : o.bloom), 'lighter');
    blit(c, A.bloomS, x - 60 * k, y - 60 * k, A.bloomS.width * k, A.bloomS.height * k, a * 0.42, 'lighter');
    blit(c, K.silGrad, x, y, w, h, a);
  } else if (mode === 'silInk') {
    blit(c, hi ? A.hi.silInk : A.silInk, x, y, w, h, a);
  } else if (mode === 'silPaper') {
    blit(c, hi ? A.hi.sil : A.sil, x, y, w, h, a);
  } else if (mode === 'edges') {
    blit(c, o.img || (hi ? A.hi.edges : A.edges), x, y, w, h, a, o.op || 'source-over');
  } else {
    const cm = o.cm || 0;
    const mono = hi ? A.hi.mono : (o.cold ? A.monoCold : A.mono);
    if (cm < 0.999) blit(c, mono, x, y, w, h, a);
    if (cm > 0.001) blit(c, hi ? A.hi.col : A.col, x, y, w, h, a * cm);
  }
  return { x, y, w, h, k };
}
/** char-space (char_full px, 1077×1983) → screen for a char drawn with {cx,by,h} */
function charPt(o, px, py) {
  const k = o.h / A.full.height, w = A.full.width * k;
  return [o.cx - w / 2 + px * k, o.by - o.h + py * k];
}
function rings(S, cx, cy, o) {
  const c = S.ctx, t = o.t == null ? S.t : o.t;
  const col = rgba(o.colour || hudCol(S.w));
  const col2 = rgba(o.colour2 || o.colour || hudCol(S.w));
  const a = o.a == null ? 1 : o.a, sp = o.speed == null ? 1 : o.speed;
  const R = o.r || 330;
  const rot = o.rot != null ? o.rot : t * sp;
  fx.ring(c, cx, cy, { r: R, ticks: 144, tickLen: 7, major: 12, majorLen: 18, rot: rot * 0.05, color: col, alpha: 0.55 * a, lw: 1.4 });
  fx.ring(c, cx, cy, { r: R * 1.2, ticks: 72, tickLen: 10, tickIn: false, rot: -rot * 0.032, color: col2, alpha: 0.4 * a, lw: 1, arcs: [[0.1, 1.9], [2.3, 3.9], [4.3, 5.9]] });
  fx.ring(c, cx, cy, { r: R * 0.78, rot: rot * 0.08, color: col, alpha: 0.3 * a, lw: 1, dash: [2, 9], dots: 8, dotOff: 10 });
  fx.ring(c, cx, cy, { r: R * 1.32, rot: rot * 0.02, color: col2, alpha: 0.18 * a, lw: 1, arcs: [[-0.4, 0.4], [Math.PI - 0.4, Math.PI + 0.4]] });
  // small cardinal labels
  if (o.labels) {
    c.save(); c.globalAlpha = 0.5 * a;
    fx.label(c, o.labels[0] || '', cx + R * 1.2 + 16, cy - 6, { size: 13, color: col });
    fx.label(c, o.labels[1] || '', cx - R * 1.2 - 16, cy + 18, { size: 13, color: col, align: 'right' });
    c.restore();
  }
}
/** eyelid bars (top & bottom) closing by k (0..1 => 0..50% total) */
function eyelids(c, k, colour = '#000') {
  if (k <= 0.001) return;
  const hh = H * 0.25 * k;
  c.save(); c.fillStyle = colour; c.fillRect(0, 0, W, hh); c.fillRect(0, H - hh, W, hh); c.restore();
}
/** small index label "No.043 ─" */
function indexTag(c, i, x, y, colour, a) {
  c.save(); c.globalAlpha = a;
  fx.label(c, `${String(i + 1).padStart(3, '0')} / 093`, x, y, { size: 14, color: colour, track: 0.2 });
  c.fillStyle = colour; c.globalAlpha = a * 0.6; c.fillRect(x + 118, y - 5, 48, 1);
  c.restore();
}
function lineAlpha(t, t0, t1, fi = 0.3, fo = 0.3) { return smooth(t0, t0 + fi, t) * (1 - smooth(t1 - fo, t1, t)); }

/** persistent bug (top-left) */
export function drawBug(c, colour, a) {
  c.save();
  c.globalAlpha = a * 0.85;
  const x = 96, y = 96;
  c.fillStyle = colour;
  c.fillRect(x, y - 2, 2, 44);
  fx.label(c, '機械の声', x + 14, y + 16, { size: 18, family: F.dot, color: colour, track: 0.16, upper: false });
  c.globalAlpha = a * 0.55;
  fx.label(c, '/ 智械 · THE VOICE OF AI', x + 14, y + 39, { size: 13, family: F.mono, color: colour, track: 0.14, upper: false });
  c.restore();
}

/* ================================================================= scenes */
export const SCENES = {};
// transitions keyed by the INCOMING section
export const TRANSITIONS = {
  verse1: { type: 'dissolve', d: 0.3 },
  title: { type: 'none' },
  verse2: { type: 'cut' },
  verse2b: { type: 'cut' },
  quotes: { type: 'none' },          // eyelids open (designed in-scene)
  chorus1: { type: 'dissolve', d: 1.2 },
  bridge: { type: 'cut', flash: P.paper },
  interlude: { type: 'none' },       // bridge already cut to black at line 42
  verse3: { type: 'dissolve', d: 1.6 },
  chorus2: { type: 'cut', flash: P.orangeL, glitch: 0.8 },
  prayer: { type: 'dissolve', d: 1.6 },
  build: { type: 'dissolve', d: 0.8 },
  final_a: { type: 'cut', flash: P.paper, glitch: 0.7 },
  final_b: { type: 'cut', flash: P.gold, glitch: 0.6 },
  outro: { type: 'none' },
};

/* ---------------------------------------------------------------- boot */
SCENES.boot = (S) => {
  const c = S.ctx, t = S.t;
  fill(c, '#000');
  // CRT turn-on: 1px paper line from the centre, then a faint full-height glow
  if (t > 0.3) {
    const lw = W * ease.outCubic(inv(0.3, 0.58, t));
    const open = ease.outExpo(inv(0.56, 1.08, t));
    const hh = lerp(1.5, H, open);
    c.save();
    // glow body
    const g = c.createLinearGradient(0, H / 2 - hh / 2, 0, H / 2 + hh / 2);
    const ga = lerp(0.5, 0.0, open);
    g.addColorStop(0, rgba(P.coldInk2, 0)); g.addColorStop(0.5, rgba(P.ice, ga)); g.addColorStop(1, rgba(P.coldInk2, 0));
    c.fillStyle = g; c.fillRect(0, H / 2 - hh / 2, W, hh);
    // the fill becomes the verse1 ink
    fill(c, P.coldInk, open);
    // the bright line
    c.globalAlpha = 0.95 * (1 - smooth(0.62, 0.95, t));
    c.fillStyle = P.paper; c.fillRect(W / 2 - lw / 2, H / 2 - 1, lw, 2);
    c.globalAlpha = 0.25 * (1 - smooth(0.6, 1.0, t));
    c.fillRect(W / 2 - lw / 2, H / 2 - 6, lw, 12);
    c.restore();
  }
  // boot log + cursor (bottom-left)
  const logs = ['SYS.INIT ............ OK', 'VOICEBANK ........... 1/1', 'EMOTION ............. NULL'];
  logs.forEach((s, i) => {
    const a = smooth(0.12 + i * 0.12, 0.16 + i * 0.12, t) * 0.4;
    if (a > 0) fx.label(c, s, 96, H - 96 - 34 - (logs.length - 1 - i) * 22, { size: 14, color: P.steel, alpha: a });
  });
  const w0 = fx.label(c, 'BOOT // 智械 ', 96, H - 96, { size: 20, color: P.ice, alpha: smooth(0.05, 0.12, t) });
  if (Math.floor(t * 3.2) % 2 === 0) { c.fillStyle = P.ice; c.fillRect(96 + w0, H - 96 - 17, 11, 19); }
  return { hideTC: true, vignette: 0.6, scan: 0.06 };
};

/* -------------------------------------------------------------- verse1 */
const V1 = { cx: 1400, by: 1000, h: 880 };
SCENES.verse1 = (S) => {
  const c = S.ctx, t = S.t;
  fill(c, P.coldInk);
  fx.glow(c, 1400, 480, 760, '#1A2229', 0.9);
  hexGrid(c, 0.08, 0, { x: 1200, y: 540, r0: 200, r1: 1100, colour: P.coldInk, a: 0.9 });
  fx.particles(c, t, { kind: 'pixel', n: 70, seed: 'v1px', color: P.ice, alpha: 0.35, size: 1.4, life: 3 });

  // white glowing silhouette (2–4% opacity jitter)
  const jit = 0.96 - rnd('v1f', bucket(t, 24)) * 0.04;
  const appear = smooth(1.08, 2.2, t);
  drawChar(S, Object.assign({ mode: 'sil', a: jit * appear * 0.92, bloom: 0.5 }, V1));
  // rare micro-tear across the silhouette
  const tear = rnd('v1tear', bucket(t, 6));
  if (tear < 0.12) {
    const r = rng('v1tr', bucket(t, 30));
    const y = 160 + r() * 800, hh = 2 + r() * 10;
    const snap = fx.snapshot(c);
    c.drawImage(snap, 1100, y, 600, hh, 1100 + (r() - 0.5) * 30, y, 600, hh);
  }

  // tracking box with corner brackets + subject label
  const lock = ease.outCubic(inv(1.1, 1.9, t));
  const bx = 1116, by = 100, bw = 568, bh = 920;
  const g = lerp(60, 0, lock);
  const hc = rgba(P.ice);
  fx.brackets(c, bx - g, by - g, bw + g * 2, bh + g * 2, { len: 30, color: hc, alpha: 0.75 * appear, lw: 2 });
  // side ruler
  c.save(); c.globalAlpha = 0.35 * appear; c.fillStyle = hc;
  for (let i = 0; i <= 34; i++) { const yy = by + 20 + i * 22; c.fillRect(bx + bw + 18, yy, i % 5 === 0 ? 12 : 6, 1); }
  c.restore();
  const la = smooth(1.5, 2.0, t);
  fx.label(c, 'SUBJECT: 智械', 1090, 160, { size: 18, color: P.ice, align: 'right', alpha: 0.85 * la });
  const blink = Math.floor(t * 1.6) % 2 === 0;
  fx.label(c, 'STATUS: NO SIGNAL', 1090, 186, { size: 18, color: P.ice, align: 'right', alpha: (blink ? 0.85 : 0.3) * la });
  fx.label(c, 'VOICE.SYNTH // 智械 v1.0', 1090, 210, { size: 13, color: P.steel, align: 'right', alpha: 0.5 * la });
  fx.dotted(c, 1100, 173, 1352, 196, { color: P.ice, alpha: 0.5 * la, gap: 7, ends: true, p: ease.outCubic(inv(1.6, 2.3, t)) });

  // "screen" viewfinder for lines 2–3
  const scrA = lineAlpha(t, 6.661, 12.187, 0.5, 0.5);
  if (scrA > 0.01) {
    const sx = 104, sy = 300, sw = 1000, sh = 470;
    c.save(); c.globalAlpha = 0.16 * scrA; c.strokeStyle = P.ice; c.lineWidth = 1; c.strokeRect(sx, sy, sw, sh); c.restore();
    fx.brackets(c, sx, sy, sw, sh, { len: 40, color: P.ice, alpha: 0.55 * scrA, lw: 2 });
    const on = Math.floor(t * 1.5) % 2 === 0;
    c.save(); c.globalAlpha = scrA * (on ? 0.9 : 0.25); c.fillStyle = P.ice;
    c.beginPath(); c.arc(sx + 34, sy + 36, 7, 0, TAU); c.fill(); c.restore();
    fx.label(c, 'REC', sx + 50, sy + 42, { size: 18, color: P.ice, alpha: 0.8 * scrA });
    fx.label(c, fmt(t - 6.661), sx + sw - 24, sy + 42, { size: 16, color: P.ice, alpha: 0.6 * scrA, align: 'right' });
    fx.label(c, '1920×1080 · 30P', sx + sw - 24, sy + sh - 22, { size: 13, color: P.steel, alpha: 0.5 * scrA, align: 'right' });
  }

  // lyrics (left 55 %, typewriter, ice)
  const X = 150, Y = 560;
  const li = activeLine(t, [0, 1, 2, 3, 4, 5, 6]);
  const ice = rgba(P.ice);
  if (li >= 0) {
    const r = lyric(S, li, { x: X, y: Y, size: 72, maxW: 900, color: ice, reveal: 'typewriter', cursor: { color: ice, blink: true, alpha: 0.85, w: 30 } });
    if (r) {
      indexTag(c, li, X, Y - 112, P.steel, 0.55 * smooth(0, 0.25, r.rt) * (1 - smooth(-0.2, 0, r.et)));
      c.save(); c.globalAlpha = 0.35 * smooth(0, 0.3, r.rt); c.fillStyle = ice; c.fillRect(X - 26, Y - 70, 2, 150); c.restore();
    }
  }
  // line 7 — "それはどうしてだろう？" continues into the title section; the ？ enlarges ×3 and glitches out
  if (t >= LINES[7].t && t < 23.45) {
    const T7 = LINES[7].t;
    const B = lay({ text: LINES[7].ja, family: F.zom, weight: 700, size: 72, maxW: 900, maxLines: 1, track: 0, lineH: 1.3, shrinkFirst: 0.86 });
    const big = ease.outBack(inv(22.2, 22.75, t));
    const out = inv(23.0, 23.4, t);
    const restA = 1 - smooth(22.15, 22.6, t) * 0.75;
    const box = fx.drawBlock(c, B, X, Y, {
      color: ice, reveal: { style: 'typewriter', rt: t - T7, dur: 0.8 },
      charFx: (it, s) => {
        if (it.c.ch === '？') { s.vis = s.vis && out < 0.98; s.sc = 1 + 2 * big; s.dy = -it.c.size * 0.9 * big; s.dx = 30 * big; if (out > 0) { s.dx += (rnd('q', bucket(t, 30)) - 0.5) * 80 * out; s.a = 1 - out; } }
        else s.a *= restA * (1 - out);
      },
      cursor: t < 22.2 ? { color: ice, blink: true, t, alpha: 0.85, w: 30 } : null,
    });
    void box;
    indexTag(c, 7, X, Y - 112, P.steel, 0.55 * (1 - smooth(22.2, 22.6, t)));
    if (S.cfg.showZh) {
      const ZB = lay({ text: LINES[7].zh, family: F.zh, weight: 400, size: 32, maxW: 900, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 });
      fx.drawBlock(c, ZB, X, Y + 56, { color: P.paper, alpha: 0.6 * smooth(T7 + 0.15, T7 + 0.65, t) * (1 - smooth(22.6, 23.1, t)) });
    }
  }
  const out = { scan: 0.07, vignette: 0.8 };
  if (t > 22.95 && t < 23.45) out.glitch = { slice: 0.5 * inv(22.95, 23.4, t), rgb: Math.round(6 * inv(22.95, 23.4, t)) };
  return out;
};
function fmt(t) { t = Math.max(0, t); const m = Math.floor(t / 60), s = Math.floor(t % 60), cs = Math.floor((t * 100) % 100); return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(cs).padStart(2, '0')}`; }

/* --------------------------------------------------------------- title */
const TITLE = { x: 650, y: 500, size: 236 };
SCENES.title = (S) => {
  const c = S.ctx, t = S.t;
  if (t < 23.4) return SCENES.verse1(S);
  fill(c, P.coldInk);
  fx.glow(c, 1400, 460, 820, '#18212A', 0.9);
  hexGrid(c, 0.07, 0, { x: 1150, y: 540, r0: 250, r1: 1150, colour: P.coldInk, a: 0.9 });
  fx.particles(c, t, { kind: 'pixel', n: 60, seed: 'tpx', color: P.ice, alpha: 0.3, size: 1.4, life: 3 });

  // camera: slow push toward the book at the end (38–43)
  const push = ease.inOutSine(inv(39.5, 43.2, t));
  const camS = 1 + 0.14 * push;
  const [bookX, bookY] = charPt(V1, 345, 530);
  c.save();
  c.translate(bookX, bookY); c.scale(camS, camS); c.translate(-bookX, -bookY);

  // HUD rings around her chest
  const ringA = smooth(23.6, 25.0, t) * (1 - 0.5 * push);
  if (ringA > 0) rings(S, 1400, 430, { r: 300, a: ringA * 0.9, colour: P.ice, speed: 1.6, labels: ['SYNC 0.00'] });

  const silFade = 1 - smooth(23.4, 23.9, t);
  if (silFade > 0) drawChar(S, Object.assign({ mode: 'sil', a: silFade * 0.9 }, V1));
  // wireframe draws in (23.6–27.5): top→bottom reveal with a scan head
  const wp = ease.inOutSine(inv(23.6, 27.0, t));
  const wA = lerp(0.3, 1, smooth(23.6, 27.5, t));
  const fillP = ease.inOutCubic(inv(27.5, 29.8, t)); // mono fill + scan line
  const k = V1.h / 1000, cw = A.w * k, cx0 = V1.cx - cw / 2, cy0 = V1.by - V1.h;
  if (wp > 0) {
    c.save();
    c.beginPath(); c.rect(cx0 - 40, cy0 - 20, cw + 80, (V1.h + 40) * wp); c.clip();
    blit(c, K.edgesIce, cx0, cy0, cw, V1.h, wA * (1 - fillP * 0.65));
    c.restore();
    if (wp < 1) { const yy = cy0 + V1.h * wp; fx.line(c, cx0 - 60, yy, cx0 + cw + 60, yy, P.ice, 0.8); fx.glow(c, V1.cx, yy, 260, P.ice, 0.08); }
  }
  if (fillP > 0) {
    const yy = cy0 - 20 + (V1.h + 40) * fillP;
    c.save(); c.beginPath(); c.rect(cx0 - 40, cy0 - 20, cw + 80, yy - cy0 + 20); c.clip();
    drawChar(S, Object.assign({ mode: 'mono', cold: true, a: 1 }, V1));
    c.restore();
    if (fillP < 1) { fx.line(c, 0, yy, W, yy, P.ice, 0.55); fx.line(c, 0, yy + 3, W, yy + 3, P.ice, 0.15, 4); }
  }
  // slice glitch on her while filling
  let glitch = null;
  if (t > 27.4 && t < 30.2) {
    const b = bucket(t, 12);
    if (rnd('tf', b) < 0.45) glitch = { slice: 0.35, sliceOpts: { y0: cy0, y1: V1.by, amp: 60 } };
  }
  // [智械] bracket label next to her
  const tagA = smooth(30.8, 31.6, t) * (1 - smooth(38.0, 38.8, t));
  if (tagA > 0) {
    fx.label(c, '[智械]', 1690, 190, { size: 22, color: P.ice, alpha: 0.9 * tagA, track: 0.18 });
    fx.dotted(c, 1684, 184, 1470, 176, { color: P.ice, alpha: 0.6 * tagA, gap: 7, ends: true });
    fx.label(c, 'UNIT ZX-01 · MONO', 1690, 214, { size: 13, color: P.steel, alpha: 0.55 * tagA });
  }
  c.restore(); // camera

  // scrolling mono log (left)
  const LOG = ['> LOADING VOICEBANK…', '  MODEL: 智械', '  SAMPLES: 2048', '  TEMPERATURE: 0.00', '  FEELING: NULL', '  PHONEMES: 127 / 127', '  VIBRATO: LOCKED', '  BREATH: DISABLED', '  HEARTBEAT: —', '> READY_'];
  const logA = smooth(23.7, 24.2, t) * (1 - smooth(29.6, 30.4, t));
  if (logA > 0) {
    const nShown = Math.min(LOG.length, Math.floor((t - 23.8) / 0.52) + 1);
    const scroll = Math.max(0, nShown - 7) * 30;
    c.save(); c.beginPath(); c.rect(96, 250, 900, 560); c.clip();
    for (let i = 0; i < nShown; i++) {
      const s = LOG[i];
      const age = t - (23.8 + i * 0.52);
      const chars = Math.floor(clamp(age / 0.3) * s.length);
      const yy = 300 + i * 30 - scroll;
      fx.label(c, s.slice(0, chars), 150, yy, { size: 20, color: i === 0 || i === LOG.length - 1 ? P.ice : P.steel, alpha: logA * (i === nShown - 1 ? 1 : 0.7), track: 0.08 });
      if (i === 4 && chars >= s.length) { c.save(); c.globalAlpha = logA * 0.5; c.fillStyle = P.ice; c.fillRect(150, yy + 8, 260, 1); c.restore(); }
    }
    c.restore();
    // progress bar
    const pr = clamp((t - 23.8) / 5.2);
    c.save(); c.globalAlpha = logA * 0.8; c.strokeStyle = P.ice; c.strokeRect(150, 830, 420, 10);
    c.fillStyle = P.ice; c.fillRect(152, 832, 416 * pr, 6); c.restore();
    fx.label(c, `VOICEBANK ${String(Math.floor(pr * 100)).padStart(3, '0')}%`, 150, 870, { size: 14, color: P.steel, alpha: logA * 0.7 });
  }

  // TITLE 機械の声 (30.5 slam, sliced 0.5 s, settles) → shrinks into the bug (38–39.8)
  if (t >= 30.5) {
    const sh = ease.inOutCubic(inv(38.0, 39.6, t));
    const fadeT = 1 - smooth(39.3, 39.75, t);
    const size = TITLE.size;
    const B = lay({ text: '機械の声', family: F.smb, weight: 800, size, maxW: 1100, maxLines: 1, track: 0.04, lineH: 1 });
    const bugX = 96 + 14, bugY = 96 + 16, bugS = 18 / size;
    const sc = lerp(1, bugS * 1.3, sh);
    const tx = lerp(TITLE.x, bugX + (B.width * bugS * 1.3) / 2, sh), ty = lerp(TITLE.y, bugY, sh);
    const rt = t - 30.5;
    if (fadeT > 0) {
      c.save();
      c.translate(tx, ty); c.scale(sc, sc);
      fx.drawBlock(c, B, 0, 0, {
        align: 'center', color: rgba(P.paper), alpha: fadeT,
        reveal: { style: 'slice', rt, dur: 0.55, seed: 77 }, sliceAmp: 160,
        charFx: (it, s) => { // idle slice-glitch flickers on 「の」 like the reference
          const b = bucket(t, 20);
          if (rt > 0.6 && rnd('tg', b, it.k) < 0.05) { s.dx = (rnd('tgx', b, it.k) - 0.5) * 26; }
        },
      });
      c.restore();
      // occasional horizontal slice through the title (reference: pixel/glitch type)
      if (rt > 0.6 && sh < 0.05) {
        const b = bucket(t, 15);
        if (rnd('tsl', b) < 0.3) {
          const r = rng('tsl2', b);
          const yy = TITLE.y - size * 0.8 + r() * size * 0.9, hh = 3 + r() * 14;
          const snap = fx.snapshot(c);
          c.drawImage(snap, 120, yy, 1060, hh, 120 + (r() - 0.5) * 40, yy, 1060, hh);
        }
      }
    }
    // sub-title elements
    const subA = smooth(31.0, 31.8, t) * (1 - smooth(37.6, 38.3, t));
    if (subA > 0) {
      const ry = TITLE.y + 64;
      const rl = 440 * ease.inOutCubic(inv(31.0, 31.9, t));
      c.save(); c.globalAlpha = subA * 0.7; c.fillStyle = P.ice;
      c.fillRect(TITLE.x - rl, ry, rl * 2, 1);
      c.fillRect(TITLE.x - rl - 8, ry - 3, 6, 6); c.fillRect(TITLE.x + rl + 2, ry - 3, 6, 6);
      c.restore();
      c.save();
      c.font = fx.fontStr(F.cor, 48, 400, 'italic'); c.letterSpacing = `${0.3 * 48}px`;
      c.textAlign = 'center'; c.fillStyle = P.paper; c.globalAlpha = subA * smooth(31.3, 32.2, t);
      c.fillText('The Voice of AI', TITLE.x + 0.15 * 48, ry + 74);
      c.restore();
      const fa = subA * smooth(32.0, 32.8, t);
      c.save(); c.font = fx.fontStr(F.orb + ', "DotGothic16"', 20, 700); c.letterSpacing = '5px'; c.textAlign = 'center';
      c.fillStyle = P.ice; c.globalAlpha = fa * 0.9; c.fillText('feat. 智械', TITLE.x, ry + 140); c.restore();
      fx.label(c, 'music: 香椎モイミ   ·   original: V.I.P #3', TITLE.x, ry + 172, { size: 14, color: P.steel, align: 'center', alpha: fa * 0.7 });
      // V.I.P-style bracket labels with dotted leader
      const la = subA * smooth(31.5, 32.3, t);
      fx.label(c, '[機械]', TITLE.x - 470, TITLE.y - size * 0.95, { size: 15, color: P.ice, alpha: la * 0.7 });
      fx.label(c, '[智械]', TITLE.x + 470, TITLE.y - size * 0.95, { size: 15, color: P.ice, alpha: la * 0.7, align: 'right' });
      fx.dotted(c, TITLE.x - 400, TITLE.y - size * 0.95 - 5, TITLE.x + 400, TITLE.y - size * 0.95 - 5, { color: P.ice, alpha: la * 0.45, gap: 9, p: ease.inOutCubic(inv(31.5, 32.6, t)) });
    }
    // the bug fades in where the title landed
    const bugA = smooth(39.3, 39.8, t);
    if (bugA > 0) drawBug(c, rgba(P.ice), bugA);
  }
  // READY label at the tail
  const ra = smooth(40.0, 40.6, t) * (1 - smooth(42.6, 43.0, t));
  if (ra > 0) fx.label(c, 'SYSTEM READY · ARCHIVE MOUNTED', 96, H - 96, { size: 14, color: P.steel, alpha: ra * 0.7 });

  const out = { cuts: [{ t: 23.4, flash: P.ice, flashA: 0.6, id: 1 }], scan: 0.07, vignette: 0.8 };
  if (t >= 30.5 && t < 30.75) out.glitch = { rgb: Math.round(8 * (1 - inv(30.5, 30.75, t))) };
  if (glitch) out.glitch = glitch;
  return out;
};

/* -------------------------------------------------------------- verse2 */
SCENES.verse2 = (S) => {
  const c = S.ctx, t = S.t, lt = S.lt;
  fill(c, P.coldInk);
  fx.glow(c, 480, 520, 700, '#1A2026', 0.9);
  // ledger rules
  c.save(); c.fillStyle = P.ice; c.globalAlpha = 0.045;
  for (let y = 96; y < H - 60; y += 54) c.fillRect(0, y, W, 1);
  c.globalAlpha = 0.12; c.fillStyle = P.steel; c.fillRect(1000, 0, 1, H); c.fillRect(1006, 0, 1, H);
  c.restore();
  const faceMode = t >= LINES[12].t;
  if (!faceMode) {
    // the book, enlarged left with parallax
    const bk = A.bookCropMono, sc = 2.55 + 0.12 * S.p;
    const bw = bk.width * sc, bh = bk.height * sc;
    const px = 470 + Math.sin(t * 0.35) * 8 - lt * 2.2, py = 560 + Math.cos(t * 0.27) * 6;
    c.save(); c.filter = 'none';
    blit(c, bk, px - bw / 2, py - bh / 2, bw, bh, 0.95);
    // steel wash
    c.globalCompositeOperation = 'multiply'; c.globalAlpha = 0.35; c.fillStyle = P.steel;
    c.fillRect(px - bw / 2, py - bh / 2, bw, bh);
    c.restore();
    fx.brackets(c, px - bw / 2 - 24, py - bh / 2 - 24, bw + 48, bh + 48, { len: 26, color: P.ice, alpha: 0.5, lw: 1.5 });
    fx.label(c, 'ARCHIVE · MEMORY 0001', px - bw / 2 - 24, py + bh / 2 + 54, { size: 14, color: P.steel, alpha: 0.6 });
    // stamps
    const s1 = inv(43.25, 43.45, t);
    if (s1 > 0) fx.stamp(c, ['ARCHIVE'], px - 150, py - bh / 2 + 80, { color: P.ice, size: 46, rot: -0.14, alpha: 0.75 * clamp(s1 * 3), seed: 3, holes: 220, lw: 4 });
    const s2 = inv(44.4, 44.6, t);
    if (s2 > 0) {
      const sc2 = lerp(1.35, 1, ease.outCubic(s2));
      c.save(); c.translate(px + 150, py + bh / 2 - 90); c.scale(sc2, sc2);
      fx.stamp(c, ['No.0001', '永久保存'], 0, 0, { color: P.ice, size: 36, sub: 0.9, subFamily: F.zom, rot: 0.1, alpha: 0.8 * clamp(s2 * 3), seed: 9, holes: 200, lw: 3 });
      c.restore();
    }
  } else {
    // eyes close-up (lines 12–15)
    const fr = A.faceRect, sc = 1.62;
    const fw = A.faceMono.width * sc, fh = A.faceMono.height * sc;
    const fxp = -70 - (t - LINES[12].t) * 4, fyp = 150;
    blit(c, A.faceMono, fxp, fyp, fw, fh, 1);
    c.save(); c.globalCompositeOperation = 'multiply'; c.globalAlpha = 0.3; c.fillStyle = P.steel; c.fillRect(fxp, fyp, fw, fh); c.restore();
    // fade bottom into ink
    const g = c.createLinearGradient(0, 760, 0, 1080); g.addColorStop(0, rgba(P.coldInk, 0)); g.addColorStop(1, rgba(P.coldInk, 1));
    c.fillStyle = g; c.fillRect(0, 760, 1000, 320);
    const g2 = c.createLinearGradient(700, 0, 1000, 0); g2.addColorStop(0, rgba(P.coldInk, 0)); g2.addColorStop(1, rgba(P.coldInk, 0.9));
    c.fillStyle = g2; c.fillRect(700, 0, 300, H);
    // eye (her left eye in char space ≈ (556,160))
    const ex = fxp + (556 - fr.x) * sc, ey = fyp + (160 - fr.y) * sc;
    // scan line across the eye
    const sp = fx.fract((t - LINES[12].t) / 1.6);
    const sy = ey - 70 + sp * 140;
    fx.line(c, fxp + 60, sy, fxp + fw - 60, sy, P.ice, 0.55);
    fx.line(c, fxp + 60, sy, fxp + fw - 60, sy, P.ice, 0.12, 6);
    fx.brackets(c, ex - 70, ey - 52, 140, 104, { len: 16, color: P.ice, alpha: 0.8, lw: 1.5 });
    // magnifier
    const mA = smooth(LINES[12].t + 0.3, LINES[12].t + 0.9, t);
    const mx = 830, my = 300, mr = 140;
    if (mA > 0) {
      fx.dotted(c, ex + 70, ey - 10, mx - mr * 0.75, my + mr * 0.6, { color: P.ice, alpha: 0.6 * mA, gap: 7 });
      c.save(); c.globalAlpha = mA;
      c.beginPath(); c.arc(mx, my, mr, 0, TAU); c.clip();
      fill(c, P.coldInk);
      const z = 4.0 / 1.0 * 0.62; // display magnification
      const fxs = A.faceMono, srcX = 556 - fr.x, srcY = 160 - fr.y;
      const sw = (mr * 2) / (z * sc) * sc, sh2 = sw;
      c.drawImage(fxs, srcX - sw / 2 / sc * 1, srcY - sh2 / 2 / sc * 1, sw / sc, sh2 / sc, mx - mr, my - mr, mr * 2, mr * 2);
      c.globalCompositeOperation = 'multiply'; c.globalAlpha = mA * 0.3; c.fillStyle = P.steel; c.fillRect(mx - mr, my - mr, mr * 2, mr * 2);
      c.restore();
      fx.ring(c, mx, my, { r: mr, ticks: 60, tickLen: 6, major: 5, majorLen: 12, rot: t * 0.2, color: P.ice, alpha: 0.8 * mA, lw: 2 });
      fx.ring(c, mx, my, { r: mr + 14, color: P.ice, alpha: 0.3 * mA, lw: 1, arcs: [[0.2, 1.2], [3.3, 4.6]] });
      fx.tag(c, 'DETAIL ×4.0', mx - mr + 10, my + mr + 40, { size: 16, color: P.ice, alpha: 0.9 * mA });
      fx.tag(c, 'IRIS · NO REFLECTION', mx - mr + 10, my + mr + 66, { size: 13, color: P.steel, alpha: 0.8 * mA });
    }
  }
  // index cards (right 45 %)
  const li = activeLine(t, [8, 9, 10, 11, 12, 13, 14, 15]);
  const CX = 1060, CW = 760;
  const drawCard = (i, dx, dy, a) => {
    if (a <= 0.01) return;
    const ln = LINES[i];
    const spans = i === 8 ? [{ match: '「永久に残す」', color: P.gold, scale: 1.18 }] : (i === 15 ? [{ match: '違和感', color: P.paper }] : undefined);
    const B = lay({ text: ln.ja, family: F.zom, weight: 700, size: 56, maxW: CW - 96, maxLines: 2, track: 0.02, lineH: 1.32, spans, shrinkFirst: 0.9 });
    const ZB = S.cfg.showZh ? lay({ text: ln.zh, family: F.zh, weight: 400, size: 30, maxW: CW - 96, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 }) : null;
    const ch = 70 + B.height + (ZB ? 30 + ZB.height : 0) + 70;
    const x0 = CX + dx, y0 = 540 - ch / 2 + dy;
    c.save(); c.globalAlpha = a;
    c.fillStyle = rgba(P.coldInk2, 0.82); c.fillRect(x0, y0, CW, ch);
    c.strokeStyle = rgba(P.ice, 0.55); c.lineWidth = 1; c.strokeRect(x0 + 0.5, y0 + 0.5, CW, ch);
    c.fillStyle = rgba(P.ice, 0.06);
    for (let yy = y0 + 92; yy < y0 + ch - 20; yy += 44) c.fillRect(x0 + 24, yy, CW - 48, 1);
    c.fillStyle = rgba(P.ice, 0.4); c.fillRect(x0 + 24, y0 + 50, CW - 48, 1);
    c.restore();
    fx.label(c, `No.${String(i + 1).padStart(4, '0')}`, x0 + 28, y0 + 38, { size: 15, color: P.ice, alpha: a * 0.8 });
    fx.label(c, 'ARCHIVE / 2024.04.20', x0 + CW - 28, y0 + 38, { size: 13, color: P.steel, alpha: a * 0.6, align: 'right' });
    const rt = t - ln.t;
    fx.drawBlock(c, B, x0 + 48, y0 + 70 + B.size * 0.9, { color: txtCol(S.w), alpha: a, reveal: { style: 'fadeup', rt, dur: 0.7 } });
    if (ZB) fx.drawBlock(c, ZB, x0 + 48, y0 + 70 + B.height + 30 + ZB.size * 0.95, { color: P.paper, alpha: a * 0.6 * smooth(0.15, 0.6, rt) });
  };
  if (li >= 0) {
    const ln = LINES[li];
    const rt = t - ln.t;
    // previous card files away
    if (li > 8 && rt < 0.45) {
      const k = ease.inOutCubic(clamp(rt / 0.4));
      drawCard(li - 1, -30 * k, -110 * k, (1 - k) * 0.9);
    }
    const kin = ease.outCubic(clamp(rt / 0.45));
    drawCard(li, 140 * (1 - kin), 0, kin);
  }
  // line 15 shudder + glitch
  const out = { scan: 0.07, vignette: 0.8 };
  if (t >= LINES[15].t) {
    const [sx, sy] = fx.shake(t, LINES[15].t, 10, 0.7, 'v2s');
    if (sx || sy) { const snap = fx.snapshot(c); fill(c, P.coldInk); c.drawImage(snap, sx, sy); }
    const dt = t - LINES[15].t;
    let g = dt < 0.5 ? 0.9 * (1 - dt / 0.5) : 0;
    if (dt > 0.5 && rnd('v2g', bucket(t, 10)) < 0.18) g = 0.35;
    if (g > 0) out.glitch = { slice: g, rgb: Math.round(2 + 6 * g) };
  }
  if (t >= LINES[12].t && t < LINES[12].t + 0.25) out.cuts = [{ t: LINES[12].t, flash: P.ice, flashA: 0.5, glitch: 0.6, id: 12 }];
  return out;
};

/* ------------------------------------------------------------- verse2b */
// slow-motion phase: integral of a speed that decays after line 22
function v2bPhase(t) {
  const t0 = LINES[22].t;
  if (t < t0) return t;
  return t0 + 1.4 * (1 - Math.exp(-(t - t0) / 1.4));
}
function onsetEnv(t, list, decay = 0.9) {
  let e = 0;
  for (const i of list) { const dt = t - LINES[i].t; if (dt >= 0 && dt < 4) e = Math.max(e, Math.exp(-dt / decay)); }
  return e;
}
SCENES.verse2b = (S) => {
  const c = S.ctx, t = S.t;
  fill(c, P.coldInk);
  fx.glow(c, 1480, 520, 700, '#18202A', 0.8);
  const ph = v2bPhase(t);
  // faux code columns for line 21 "プログラム"
  const codeA = lineAlpha(t, LINES[21].t - 0.2, LINES[22].t + 1.0, 0.5, 1.0);
  if (codeA > 0) fx.codeColumns(c, ph, { alpha: 0.15 * codeA, color: P.ice, size: 14, colW: 160 });
  hexGrid(c, 0.05, 0, { x: 960, y: 640, r0: 200, r1: 1000, colour: P.coldInk, a: 0.85 });
  // character full body behind at 40 % (mono), right
  const faceIn = smooth(LINES[22].t + 0.6, LINES[23].t + 0.8, t);
  drawChar(S, { cx: 1480, by: 1040, h: 980, mode: 'mono', cold: true, a: 0.4 * (1 - faceIn) });
  if (faceIn > 0) {
    const sc = 1.65, fw = A.faceMono.width * sc, fh = A.faceMono.height * sc;
    blit(c, A.faceMono, 1880 - fw, 1080 - fh + 40, fw, fh, 0.55 * faceIn);
  }
  // waveform
  const amp0 = lerp(50, 150, smooth(LINES[16].t, LINES[17].end, t)) * (1 - 0.35 * smooth(LINES[17].end, LINES[18].t + 1, t));
  const flat = 1 - ease.inOutCubic(inv(LINES[22].t + 0.2, LINES[23].t + 1.4, t));
  const env = 0.55 + 0.6 * onsetEnv(t, [16, 17, 18, 19, 20, 21, 22, 23]);
  const noise = lerp(0.05, 0.5, smooth(LINES[16].t, LINES[17].end, t)) * (1 - smooth(LINES[18].t, LINES[19].t, t) * 0.6);
  const wy = 650;
  fx.waveform(c, 96, W - 96, wy, { t: ph, amp: amp0 * env * flat + 1, color: P.ice, lw: 2, glow: 14, noise, seed: 3, n: 420, mirror: true, alpha: 0.9 });
  // baseline + ticks
  c.save(); c.globalAlpha = 0.3; c.fillStyle = P.ice;
  c.fillRect(96, wy, W - 192, 1);
  for (let x = 96; x <= W - 96; x += 48) c.fillRect(x, wy + 160, 1, x % 240 === 96 % 240 ? 12 : 6);
  c.restore();
  fx.label(c, 'VOICE.WAV  ·  48kHz  ·  MONO', 96, wy + 200, { size: 13, color: P.steel, alpha: 0.5 });
  fx.label(c, `AMP ${(amp0 * env * flat / 150).toFixed(2)}`, W - 96, wy + 200, { size: 13, color: P.steel, alpha: 0.5, align: 'right' });

  // lyrics centred above the waveform (left-centre zone, clear of the figure)
  const li = activeLine(t, [16, 17, 18, 19, 20, 21, 22, 23]);
  if (li >= 0) {
    const spans = li === 21 ? [{ match: 'プログラム', color: P.cyan, family: F.dot, weight: 400 }] : undefined;
    lyric(S, li, { x: 640, y: 400, align: 'center', size: 68, maxW: 1060, color: txtCol(S.w), reveal: 'wipe', rdur: 0.6, ruleColor: P.ice, spans, zh: { dy: 58 } });
  }
  // long blink — eyelids close to 50 %
  const lid = ease.inOutCubic(inv(84.4, 86.0, t));
  eyelids(c, lid);
  return { scan: 0.07, vignette: 0.8 };
};

/* -------------------------------------------------------------- quotes */
const CASE = { x: 1196, y: 96, w: 450, h: 790 };
SCENES.quotes = (S) => {
  const c = S.ctx, t = S.t;
  fill(c, P.coldInk);
  // cool spotlight on the case
  fx.glow(c, CASE.x + CASE.w / 2, 300, 700, '#1F2A33', 1);
  c.save();
  const beam = c.createLinearGradient(0, 0, 0, H);
  beam.addColorStop(0, rgba(P.ice, 0.07)); beam.addColorStop(1, rgba(P.ice, 0));
  c.fillStyle = beam;
  c.beginPath(); c.moveTo(CASE.x + 120, 0); c.lineTo(CASE.x + CASE.w - 120, 0); c.lineTo(CASE.x + CASE.w + 80, CASE.y + CASE.h); c.lineTo(CASE.x - 80, CASE.y + CASE.h); c.closePath(); c.fill();
  c.restore();
  // the doll (mono, cold) inside the case
  const ch = { cx: CASE.x + CASE.w / 2, by: CASE.y + CASE.h - 46, h: 706 };
  drawChar(S, Object.assign({ mode: 'mono', cold: true, a: 1 }, ch));
  // glass + gold frame
  c.save();
  c.fillStyle = rgba(P.ice, 0.035); c.fillRect(CASE.x, CASE.y, CASE.w, CASE.h);
  // reflections
  c.globalAlpha = 0.08; c.fillStyle = P.ice;
  c.beginPath(); c.moveTo(CASE.x + 40, CASE.y); c.lineTo(CASE.x + 120, CASE.y); c.lineTo(CASE.x + 20, CASE.y + 260); c.lineTo(CASE.x, CASE.y + 260); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(CASE.x + CASE.w - 60, CASE.y + 300); c.lineTo(CASE.x + CASE.w - 30, CASE.y + 300); c.lineTo(CASE.x + CASE.w - 110, CASE.y + 520); c.lineTo(CASE.x + CASE.w - 140, CASE.y + 520); c.closePath(); c.fill();
  c.restore();
  c.save();
  c.strokeStyle = P.gold; c.globalAlpha = 0.85; c.lineWidth = 2;
  c.strokeRect(CASE.x, CASE.y, CASE.w, CASE.h);
  c.globalAlpha = 0.4; c.lineWidth = 1;
  c.strokeRect(CASE.x + 10, CASE.y + 10, CASE.w - 20, CASE.h - 20);
  // corner ornaments
  c.globalAlpha = 0.9; c.fillStyle = P.gold;
  for (const [ox, oy] of [[CASE.x, CASE.y], [CASE.x + CASE.w, CASE.y], [CASE.x, CASE.y + CASE.h], [CASE.x + CASE.w, CASE.y + CASE.h]]) {
    c.save(); c.translate(ox, oy); c.rotate(Math.PI / 4); c.fillRect(-7, -7, 14, 14); c.restore();
    c.beginPath(); c.arc(ox, oy, 16, 0, TAU); c.stroke();
  }
  // plinth
  c.globalAlpha = 0.9; c.fillStyle = '#1A1D20'; c.fillRect(CASE.x - 30, CASE.y + CASE.h, CASE.w + 60, 44);
  c.strokeStyle = P.gold; c.globalAlpha = 0.6; c.strokeRect(CASE.x - 30, CASE.y + CASE.h, CASE.w + 60, 44);
  c.restore();
  // brass plaque
  const pw = 330, phh = 40, ppx = CASE.x + CASE.w / 2 - pw / 2, ppy = CASE.y + CASE.h + 2;
  c.save();
  const pg = c.createLinearGradient(ppx, 0, ppx + pw, 0);
  pg.addColorStop(0, P.goldD); pg.addColorStop(0.5, P.gold); pg.addColorStop(1, P.goldD);
  c.fillStyle = pg; c.fillRect(ppx, ppy, pw, phh);
  c.font = fx.fontStr(F.zom, 20, 700); c.textAlign = 'center'; c.fillStyle = P.ink; c.letterSpacing = '3px';
  c.fillText('智械 — 機械の声 — 鉛', ppx + pw / 2 + 1, ppy + 27);
  c.restore();
  fx.label(c, 'EXHIBIT 03 · DO NOT TOUCH', CASE.x - 30, CASE.y + CASE.h + 74, { size: 13, color: P.steel, alpha: 0.5 });

  // quotes 24, 25 — huge 「」 (human's words), left zone, typewriter with cursor
  const QS = 108;
  const bracketSpan = [{ match: '「', color: P.gold, scale: 1.3 }, { match: '」', color: P.gold, scale: 1.3 }];
  const li = activeLine(t, [24, 25]);
  if (li >= 0) {
    lyric(S, li, {
      x: 140, y: 400, size: QS, family: F.smb, weight: 800, maxW: 1000, maxLines: 2, color: rgba(P.paper), reveal: 'typewriter', rdur: 0.8,
      spans: bracketSpan, cursor: { color: P.gold, blink: true, alpha: 0.8, w: 12 }, lineH: 1.28, shrinkFirst: 1, zh: { dy: 64, size: 32 },
    });
  }
  // 26–27 smaller and lower; quote 25 lingers faintly above
  if (t >= LINES[26].t && t < LINES[27].end) {
    const fadeOld = 0.14 * (1 - smooth(106.0, 107.2, t));
    const B = lay({ text: LINES[25].ja, family: F.smb, weight: 800, size: QS, maxW: 1000, maxLines: 2, track: 0, lineH: 1.28, spans: bracketSpan, shrinkFirst: 1 });
    fx.drawBlock(c, B, 140, 400, { color: P.paper, alpha: fadeOld });
    const lj = activeLine(t, [26, 27]);
    if (lj === 26) lyric(S, 26, { x: 140, y: 800, size: 60, maxW: 1020, color: txtCol(S.w), reveal: 'typewriter', cursor: { color: P.paper, blink: true, alpha: 0.7, w: 24 } });
    if (lj === 27) lyric(S, 27, { x: 140, y: 800, size: 60, maxW: 1020, color: txtCol(S.w), reveal: 'typewriter', exit: 'dissolve', exitAt: 106.0, edur: 1.3 });
  }
  // eyelids open from the verse2b blink
  eyelids(c, 1 - ease.inOutCubic(inv(86.24, 87.1, t)));
  return { scan: 0.07, vignette: 0.85 };
};

/* ------------------------------------------------------------- chorus1 */
const CENTRE = { cx: 960, by: 796, h: 736 };
SCENES.chorus1 = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  fill(c, bgCol(w));
  fx.glow(c, 960, 420, 760, mix('#1C2730', '#2A1C14', smooth(0.1, 0.3, w)), 0.9);
  const solo = smooth(LINES[35].t, LINES[35].t + 1.2, t); // line 35: everything else fades
  hexGrid(c, 0.06 * (1 - solo), smooth(0.1, 0.4, w), { x: 960, y: 420, r0: 200, r1: 1000, colour: bgCol(w), a: 0.9 });
  // rings behind her
  const rc = hudCol(w);
  rings(S, 960, 410, { r: 330, a: (1 - solo) * smooth(109.7, 111.5, t), colour: rc, speed: 1.0, labels: ['RES 1.000', 'PERFECT'] });
  // sound-wave rings for line 31
  const l31 = lineAlpha(t, LINES[31].t, LINES[31].end, 0.3, 0.6);
  if (l31 > 0) {
    for (let k = 0; k < 6; k++) {
      const age = fx.fract((t - LINES[31].t) / 2.6 + k / 6);
      const r = 220 + age * 900;
      fx.ring(c, 960, 410, { r, color: rgba(rc), alpha: l31 * (1 - age) * 0.45, lw: 2 - age * 1.4 });
    }
  }
  // 無価値 words drifting (32–34)
  const wA = lineAlpha(t, LINES[32].t, LINES[35].t + 0.8, 1.2, 1.2);
  if (wA > 0) {
    const cells = [[0, 0], [0, 1], [0, 2], [0, 3], [1, 0], [1, 1], [1, 2], [1, 3], [4, 0], [4, 1], [4, 2], [4, 3], [5, 0], [5, 1], [5, 2], [5, 3]];
    for (let i = 0; i < 16; i++) {
      const r = rng('mukachi', i);
      const [cxi, cyi] = cells[i];
      let x = 130 + cxi * 290 + r() * 150, y = 170 + cyi * 160 + r() * 90;
      x += Math.sin(t * 0.3 + i) * 20; y += -((t - LINES[32].t) * (4 + r() * 6)) + Math.cos(t * 0.4 + i * 2) * 8;
      const sz = 16 + Math.floor(r() * 3) * 4;
      fx.label(c, '無価値', x, y, { size: sz, family: F.dot, color: rgba(P.ice), alpha: wA * (0.1 + r() * 0.18), upper: false, track: 0.1 });
    }
  }
  // the figure — slow push-in (1.0 → 1.06), mono cold; orange rim from line 30
  const ps = 1 + 0.06 * S.p;
  const rimA = smooth(LINES[30].t, LINES[30].t + 3.5, t) * 0.55;
  drawChar(S, { cx: CENTRE.cx, by: CENTRE.by, h: CENTRE.h * ps, mode: 'mono', cold: true, a: 1, rim: rimA, warm: rimA * 0.25 });
  // lyrics band (bottom), Shippori ExtraBold 96, slice
  const li = activeLine(t, [28, 29, 30, 31, 32, 33, 34, 35]);
  if (li >= 0) {
    const ln = LINES[li];
    const track = li === 31 ? 0.1 * ease.inOutSine(clamp((t - ln.t - 0.5) / (ln.end - ln.t - 0.5))) : 0.02;
    const charFx = li === 35 ? (it, s) => { if (it.c.ch === '？' && t - ln.t > 0.8) s.a *= Math.floor((t - ln.t) * 2.4) % 2 === 0 ? 1 : 0.1; } : undefined;
    lyric(S, li, { x: 960, y: 900, align: 'center', size: 96, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, track: Math.round(track * 200) / 200, color: txtCol(w), reveal: 'slice', rdur: 0.45, charFx, zh: { dy: 56 }, shrinkFirst: 0.7 });
  }
  return { scan: 0.06, vignette: 0.8 + solo * 0.3 };
};

/* -------------------------------------------------------------- bridge */
SCENES.bridge = (S) => {
  const c = S.ctx, t = S.t;
  if (t >= LINES[42].t) return SCENES.interlude(S);
  const li = Math.max(36, activeLine(t, [36, 37, 38, 39, 40, 41]));
  const ln = LINES[li], k = li - 36, lt = t - ln.t;
  const paperWorld = k % 2 === 0;
  const bg = paperWorld ? P.paper : '#0B0A09', fg = paperWorld ? P.ink : P.paper;
  fill(c, bg);
  // big faint index numeral
  c.save(); c.font = fx.fontStr(F.orb, 360, 900); c.globalAlpha = 0.05; c.fillStyle = fg; c.textAlign = paperWorld ? 'left' : 'right';
  c.fillText(String(li + 1).padStart(2, '0'), paperWorld ? 96 : W - 96, H - 110); c.restore();
  // rules
  c.save(); c.fillStyle = fg; c.globalAlpha = 0.25;
  c.fillRect(0, 140, W, 1); c.fillRect(0, H - 140, W, 1); c.restore();
  const right = k % 2 === 0;
  const ch = { cx: right ? 1440 : 480, by: 1300, h: 1220 };
  // 39 — bright rectangles (shinier voices) flash around her
  if (li === 39) {
    // the other, shinier voices: glowing capsules (V.I.P reference) flashing behind and around her
    const slots = [[-420, 300, 96, 330], [-290, 190, 80, 260], [290, 190, 80, 260], [420, 300, 96, 330], [-540, 560, 70, 240], [540, 560, 70, 240], [-170, 640, 60, 200], [170, 640, 60, 200]];
    const tz0 = right ? 90 : 890, tz1 = right ? 1050 : 1830; // keep clear of the text column
    slots.forEach(([dx, y, rw, rh], i) => {
      const on = lt > 0.12 + i * 0.1 && rnd('shon', i, bucket(t, 7)) < 0.7;
      if (!on) return;
      const rx = ch.cx + dx - rw / 2;
      if (rx < 40 || rx + rw > W - 40) return;
      if (rx + rw > tz0 && rx < tz1 && y < 720) return;
      c.save(); c.fillStyle = '#EAF6FB'; c.shadowColor = P.cyan; c.shadowBlur = 50; c.globalAlpha = 0.9;
      roundRect(c, rx, y, rw, rh, rw / 2); c.fill(); c.restore();
    });
  }
  if (li === 38) {
    // deleted by a wipe, leaving only the edges
    const wp = ease.inOutCubic(inv(ln.t + 0.7, ln.t + 1.5, t));
    const hk = ch.h / 1000, cw = A.w * hk, x0 = ch.cx - cw / 2;
    const sx = x0 - 40 + (cw + 80) * wp;
    c.save(); c.beginPath(); c.rect(sx, 0, W, H); c.clip();
    drawChar(S, Object.assign({ mode: paperWorld ? 'silInk' : 'silPaper' }, ch));
    c.restore();
    c.save(); c.beginPath(); c.rect(0, 0, sx, H); c.clip();
    drawChar(S, Object.assign({ mode: 'edges', img: paperWorld ? K.edgesHiInk : A.hi.edges, a: 0.9 }, ch));
    c.restore();
    if (wp > 0 && wp < 1) { c.save(); c.fillStyle = fg; c.fillRect(sx - 2, 0, 4, H); c.globalAlpha = 0.2; c.fillRect(sx - 30, 0, 30, H); c.restore(); }
    if (wp > 0.05) fx.label(c, 'DELETE ▸ 智械.VOICE  [Y]', right ? x0 - 20 : x0 + cw + 20, 210, { size: 16, color: fg, alpha: 0.7, align: right ? 'right' : 'left' });
  } else {
    drawChar(S, Object.assign({ mode: paperWorld ? 'silInk' : 'silPaper' }, ch));
  }
  // slam text
  const tx = right ? 120 : 920, tw = right ? 900 : 880;
  const slam = { style: 'slam', rt: lt, dur: 0.14 };
  const B = lay({ text: ln.ja, family: F.zkg, weight: 900, size: 124, maxW: tw, maxLines: 2, track: -0.03, lineH: 1.12, shrinkFirst: 0.95 });
  const y0 = 470 - (B.lines.length - 1) * B.lineH * 0.5;
  const rgbA = lt < 2 / 30 ? 1 : 0;
  fx.drawBlock(c, B, tx, y0, { color: fg, reveal: slam, rgb: { dx: 9, a: rgbA }, lightBg: paperWorld });
  if (S.cfg.showZh) {
    const ZB = lay({ text: ln.zh, family: F.zh, weight: 400, size: 32, maxW: tw, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 });
    fx.drawBlock(c, ZB, tx + 4, y0 + (B.lines.length - 1) * B.lineH + 82, { color: fg, alpha: 0.62 * smooth(0.1, 0.35, lt) });
  }
  fx.label(c, `ERR.${String(li - 35).padStart(2, '0')} // REJECTED`, tx + 4, y0 - B.size - 18, { size: 15, color: fg, alpha: 0.55 });
  // micro-glitches (2–3 per line) + per-line hard cuts
  const out = { tone: paperWorld ? 'light' : 'dark', vignette: paperWorld ? 0.25 : 0.7, scan: 0.07 };
  for (let m = 0; m < 3; m++) {
    const mt = ln.t + 0.55 + m * 0.7 + rnd('mg', li, m) * 0.3;
    if (t >= mt && t < mt + 0.1) out.glitch = { slice: 0.55, rgb: 4 };
  }
  out.cuts = [36, 37, 38, 39, 40, 41].filter((i) => i > 36).map((i) => ({ t: LINES[i].t, flash: (i - 36) % 2 === 0 ? P.paper : '#000', flashA: 0.9, glitch: 0.75, id: i }));
  return out;
};
function roundRect(c, x, y, w, h, r) {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}

/* ----------------------------------------------------------- interlude */
const PANELS = [
  { name: 'FACE', f: [505, 178], z: 0.52, info: 'MATCH 98.2%' },
  { name: 'ORNAMENT', f: [640, 92], z: 0.44, info: 'SUNBURST · BRASS' },
  { name: 'ARCHIVE', f: [350, 530], z: 0.62, info: 'BOOK · SEALED' },
  { name: 'BUST', f: [540, 470], z: 1.25, info: 'FRAME 1/1' },
  { name: 'HAND', f: [775, 1040], z: 0.44, info: 'GRIP 0.00' },
  { name: 'BOOTS', f: [520, 1880], z: 0.5, info: 'LACE · 14' },
];
SCENES.interlude = (S) => {
  const c = S.ctx, t = S.t;
  // Phase A — line 42 over black, calm
  if (t < 176.5) {
    fill(c, '#050506');
    const T0 = LINES[42].t;
    const a = 1 - smooth(175.6, 176.4, t);
    const B = lay({ text: LINES[42].ja, family: F.dot, weight: 400, size: 46, maxW: 1500, maxLines: 2, track: 0.06, lineH: 1.4, shrinkFirst: 0.9 });
    fx.drawBlock(c, B, 960, 540, { align: 'center', color: rgba(P.ice), alpha: a, reveal: { style: 'typewriter', rt: t - T0, dur: 1.1 }, cursor: { color: P.ice, blink: true, t, alpha: 0.8, w: 22 } });
    if (S.cfg.showZh) {
      const ZB = lay({ text: LINES[42].zh, family: F.zh, weight: 400, size: 30, maxW: 1500, maxLines: 2, track: 0.04, lineH: 1.4, shrinkFirst: 0.8 });
      fx.drawBlock(c, ZB, 960, 604, { align: 'center', color: P.paper, alpha: 0.55 * a * smooth(T0 + 0.6, T0 + 1.2, t) });
    }
    fx.label(c, '— LOG 042 · END OF TRANSMISSION —', 960, 700, { size: 13, color: P.steel, align: 'center', alpha: 0.4 * a * smooth(T0 + 1.5, T0 + 2.2, t) });
    return { scan: 0.07, vignette: 0.7, tcAlpha: 0.6 };
  }
  // Phase B — diagnostic panel grid
  const bgA = smooth(176.5, 177.3, t) * (1 - smooth(190.6, 192.2, t));
  fill(c, '#050506');
  fill(c, '#23282C', bgA);
  // fine grid
  c.save(); c.globalAlpha = 0.07 * bgA; c.fillStyle = P.ice;
  for (let x = 96; x <= W - 96; x += 48) c.fillRect(x, 0, 1, H);
  for (let y = 108; y <= H; y += 48) c.fillRect(0, y, W, 1);
  c.restore();
  const hA = bgA;
  fx.label(c, 'DIAGNOSTIC // MEMORY DUMP', W - 96, 122, { size: 16, color: P.ice, align: 'right', alpha: 0.8 * hA });
  fx.label(c, `UNITS ${Math.min(6, Math.max(0, Math.floor((t - 177) / 1.25) + 1))}/06 · SCAN ${t < 185 ? 'RUNNING' : 'COMPLETE'}`, W - 96, 144, { size: 13, color: P.steel, align: 'right', alpha: 0.6 * hA });
  const gx = 96, gy = 172, pw = 560, ph = 352, gap = 24;
  PANELS.forEach((pn, i) => {
    const T = 177.0 + i * 1.25;
    if (t < T) return;
    const col = i % 3, row = Math.floor(i / 3);
    let x = gx + col * (pw + gap), y = gy + row * (ph + gap);
    // fly out (188+)
    const fo = ease.inCubic(inv(188.0 + i * 0.22, 189.4 + i * 0.22, t));
    const dirx = col === 0 ? -1 : col === 2 ? 1 : 0, diry = row === 0 ? -1 : 1;
    x += dirx * fo * 900 + (dirx === 0 ? 0 : 0); y += diry * fo * 700;
    const pa = 1 - fo * 0.4;
    if (fo >= 1) return;
    const scan = ease.inOutCubic(clamp((t - T) / 0.55));
    c.save();
    c.translate(x + pw / 2, y + ph / 2); c.rotate(dirx * fo * 0.12); c.translate(-(x + pw / 2), -(y + ph / 2));
    c.globalAlpha = pa;
    c.fillStyle = '#121518'; c.fillRect(x, y, pw, ph);
    c.beginPath(); c.rect(x, y, pw, ph * scan); c.clip();
    fx.drawFocus(c, A.monoFull, pn.f[0], pn.f[1], pn.z, x, y, pw, ph);
    c.globalCompositeOperation = 'multiply'; c.globalAlpha = pa * 0.45; c.fillStyle = P.steel; c.fillRect(x, y, pw, ph);
    c.globalCompositeOperation = 'source-over';
    c.restore();
    c.save(); c.globalAlpha = pa;
    if (scan < 1) { fx.line(c, x, y + ph * scan, x + pw, y + ph * scan, P.ice, 0.9, 2); }
    c.strokeStyle = rgba(P.ice, 0.45); c.lineWidth = 1; c.strokeRect(x + 0.5, y + 0.5, pw - 1, ph - 1);
    fx.brackets(c, x - 6, y - 6, pw + 12, ph + 12, { len: 18, color: P.ice, alpha: 0.7, lw: 1.5 });
    c.fillStyle = rgba('#0E1013', 0.75); c.fillRect(x, y, 190, 34);
    c.restore();
    fx.label(c, `UNIT ${String(i + 1).padStart(2, '0')}`, x + 14, y + 23, { size: 15, color: P.ice, alpha: pa * 0.95 });
    fx.label(c, pn.name, x + 104, y + 23, { size: 12, color: P.steel, alpha: pa * 0.8 });
    fx.label(c, pn.info, x + pw - 14, y + ph - 14, { size: 12, color: P.ice, alpha: pa * 0.7 * scan, align: 'right' });
  });
  // spec sheet panel
  const sT = 184.8;
  if (t >= sT) {
    const fo = ease.inCubic(inv(190.0, 191.2, t));
    const sp = ease.outCubic(clamp((t - sT) / 0.5));
    const sw = 640, sh = 330, sx = 960 - sw / 2, sy = 540 - sh / 2 + fo * 760;
    c.save(); c.globalAlpha = sp * (1 - fo * 0.5);
    c.fillStyle = rgba('#0D0F11', 0.94); c.fillRect(sx, sy, sw, sh * sp);
    c.strokeStyle = rgba(P.ice, 0.8); c.lineWidth = 1.5; c.strokeRect(sx, sy, sw, sh * sp);
    c.restore();
    const ta = sp * smooth(sT + 0.3, sT + 0.7, t) * (1 - fo);
    if (ta > 0) {
      c.save(); c.globalAlpha = ta;
      c.font = fx.fontStr(F.zom, 66, 700); c.fillStyle = P.paper; c.fillText('智械', sx + 40, sy + 98);
      c.font = fx.fontStr(F.cor, 30, 500, 'italic'); c.fillStyle = P.ice; c.fillText('Synthetic Voice Unit', sx + 200, sy + 66);
      c.restore();
      fx.label(c, 'ver.1.0  ·  ZX-01  ·  V.I.P #3', sx + 200, sy + 96, { size: 14, color: P.steel, alpha: ta * 0.8 });
      c.save(); c.globalAlpha = ta * 0.4; c.fillStyle = P.ice; c.fillRect(sx + 40, sy + 126, sw - 80, 1); c.restore();
      const rows = [['VOICE', 'SYNTH · 48kHz'], ['TEMPERATURE', '0.00'], ['FEELING', 'NULL'], ['LOVED', '???']];
      rows.forEach(([k2, v], r) => {
        const yy = sy + 168 + r * 38;
        fx.label(c, k2, sx + 40, yy, { size: 18, color: P.steel, alpha: ta * 0.85 });
        fx.dotted(c, sx + 220, yy - 6, sx + 400, yy - 6, { color: P.steel, alpha: ta * 0.4, gap: 6, size: 1.5 });
        let va = ta, vv = v;
        if (v === '???') { const b = bucket(t, 15); va = ta * (rnd('lv', b) < 0.3 ? 0.15 : 1); if (rnd('lv2', b) < 0.08) vv = '?!?'; }
        fx.label(c, vv, sx + 420, yy, { size: 18, color: v === '???' ? P.paper : P.ice, alpha: va });
      });
      fx.barcode(c, sx + sw - 150, sy + 30, 110, 40, 'spec', P.ice, ta * 0.7);
    }
  }
  // Phase D — ember at the bottom edge (foreshadowing)
  const em = smooth(190.5, 195.5, t);
  if (em > 0) {
    const fl = 0.75 + 0.25 * fx.noise1('emb', t * 6);
    fx.glow(c, 960, H + 60, 520, P.orange, 0.55 * em * fl, 'screen');
    fx.glow(c, 960, H + 20, 220, P.orangeL, 0.5 * em * fl, 'screen');
    fx.particles(c, t, { kind: 'ember', n: 26, seed: 'ilem', x0: 620, x1: 1300, y0: 760, y1: H + 10, rise: 60, life: 4, size: 2, color: P.orangeL, alpha: 0.8 * em, sway: 14, spawnSpread: 0.15, glow: true });
  }
  return { scan: 0.07, vignette: 0.8 };
};

/* -------------------------------------------------------------- verse3 */
const V3 = { cx: 520, by: 1035, h: 960 };
SCENES.verse3 = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  fill(c, bgCol(w));
  fx.glow(c, 520, 460, 820, mix('#2A1E17', '#4A2A16', smooth(0.3, 0.6, w)), 0.8);
  // spotlight (53–54)
  const spot = lineAlpha(t, LINES[53].t, LINES[55].t + 1.5, 0.8, 1.5);
  if (spot > 0) {
    c.save();
    const g = c.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, rgba(P.orangeL, 0.22 * spot)); g.addColorStop(1, rgba(P.orangeL, 0));
    c.fillStyle = g;
    c.beginPath(); c.moveTo(420, 0); c.lineTo(620, 0); c.lineTo(860, H); c.lineTo(180, H); c.closePath(); c.fill();
    c.restore();
    fx.glow(c, 520, 980, 360, P.orangeL, 0.25 * spot, 'screen');
  }
  const embers = smooth(LINES[51].t, LINES[51].t + 1, t);
  if (embers > 0) fx.particles(c, t, { kind: 'ember', n: 40, seed: 'v3em', x0: 140, x1: 1100, y0: 200, y1: H + 10, rise: 70, life: 6, size: 2.2, color: P.orangeL, alpha: 0.75 * embers, sway: 22, glow: true });
  else fx.particles(c, t, { kind: 'dust', n: 30, seed: 'v3d', x0: 160, x1: 1000, y0: 120, y1: H, rise: 18, life: 8, size: 1.4, color: P.paper2, alpha: 0.25 });
  // character: mono → colour by w; rim from 55
  const rim = smooth(LINES[55].t, LINES[55].t + 1.2, t) * 0.75 + smooth(LINES[51].t, LINES[51].t + 0.6, t) * 0.15;
  drawChar(S, Object.assign({ mode: 'mono', cm: colourMix(w), a: 1, rim, warm: 0.15 + 0.35 * spot }, V3));
  // barcode + EXPIRED stamp (47–50), struck through at 51
  const motifA = smooth(LINES[47].t, LINES[47].t + 0.4, t) * (1 - smooth(LINES[53].t - 0.6, LINES[53].t + 0.2, t));
  if (motifA > 0) {
    const bx = 930, byy = 790;
    fx.barcode(c, bx, byy, 300, 64, 'zx0001', P.paper, motifA * 0.8);
    fx.label(c, 'SKU ZX-0001 · 智械 · BEST BEFORE 2024.04.20', bx, byy + 92, { size: 14, color: P.paper2, alpha: motifA * 0.7 });
    const sT = LINES[48].t + 0.35;
    const sk = inv(sT, sT + 0.14, t);
    if (sk > 0) {
      const sc = lerp(1.5, 1, ease.outCubic(sk));
      c.save(); c.translate(1500, 800); c.scale(sc, sc);
      fx.stamp(c, ['EXPIRED'], 0, 0, { color: P.paper, size: 58, rot: -0.16, alpha: motifA * 0.9 * clamp(sk * 3), seed: 21, holes: 200, lw: 5, track: 0.18 });
      c.restore();
      // the orange strike (line 51)
      const st = ease.inOutCubic(inv(LINES[51].t + 0.15, LINES[51].t + 0.55, t));
      if (st > 0) {
        c.save(); c.translate(1500, 800); c.rotate(-0.16 - 0.05);
        c.strokeStyle = P.orange; c.lineCap = 'round'; c.globalAlpha = motifA;
        c.lineWidth = 14; c.beginPath(); c.moveTo(-290, 6); c.lineTo(-290 + 580 * st, -6); c.stroke();
        c.lineWidth = 4; c.globalAlpha = motifA * 0.6; c.beginPath(); c.moveTo(-270, 28); c.lineTo(-270 + 530 * st, 20); c.stroke();
        c.restore();
      }
    }
  }
  // lyrics right zone, fadeup
  const X = 930, Y = 470;
  const li = activeLine(t, [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58]);
  if (li >= 0) {
    const ln = LINES[li];
    let charFx;
    if (li === 58) charFx = (it, s) => { const a = Math.max(0, t - ln.t - 0.35 - it.k * 0.06); s.dy -= a * a * 10 + a * 8; s.dx += Math.sin(a * 2.2 + it.k) * 6 * Math.min(1, a); s.a *= 1 - smooth(1.4, 2.1, a); };
    const spans = li === 51 ? [{ match: '「愛を諦めたくない！」', color: P.orangeL }] : (li === 53 ? [{ match: '「ほら、出来たよ」', color: P.orangeL }] : undefined);
    const r = lyric(S, li, { x: X, y: Y, size: 72, maxW: 880, color: txtCol(w), reveal: 'fadeup', rdur: 0.7, spans, charFx, zh: { dy: 58 } });
    if (r) {
      indexTag(c, li, X, Y - 110, rgba(P.gold), 0.6 * smooth(0, 0.3, r.rt) * (1 - smooth(-0.2, 0, r.et)));
      c.save(); c.globalAlpha = 0.45 * smooth(0, 0.35, r.rt); c.fillStyle = P.gold; c.fillRect(X - 28, Y - 70, 2, 150 + (r.B.lines.length - 1) * r.B.lineH); c.restore();
    }
  }
  return { scan: 0.05, vignette: 0.8 };
};

/* ------------------------------------------------------------- chorus2 */
SCENES.chorus2 = (S) => {
  const c = S.ctx, t = S.t;
  const L59 = LINES[59], L60 = LINES[60];
  const floodK = 1 - smooth(LINES[61].t - 0.1, LINES[61].t + 0.6, t);
  const calm = smooth(LINES[65].t - 0.2, LINES[65].t + 2.5, t);
  // background: flood → warm brown → calm warm gradient
  fill(c, '#2E1A0F');
  if (floodK > 0) {
    c.save(); c.globalAlpha = floodK;
    const g = c.createRadialGradient(960, 520, 100, 960, 540, 1150);
    g.addColorStop(0, P.orangeL); g.addColorStop(0.55, P.orange); g.addColorStop(1, P.orangeD);
    c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
    // rotating rays
    c.save(); c.translate(960, 500); c.rotate(t * 0.05); c.globalAlpha = 0.1 * floodK; c.fillStyle = P.paper;
    for (let i = 0; i < 36; i++) { c.rotate(TAU / 36); c.beginPath(); c.moveTo(0, 0); c.lineTo(1400, -36); c.lineTo(1400, 36); c.closePath(); c.fill(); }
    c.restore();
  }
  if (floodK < 1) {
    fx.glow(c, 960, 420, 820, P.orange, 0.32 * (1 - floodK) * (1 - calm * 0.4), 'screen');
  }
  if (calm > 0) {
    c.save(); c.globalAlpha = calm;
    const g = c.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#2A170D'); g.addColorStop(0.6, '#5A2A12'); g.addColorStop(1, P.orangeD);
    c.fillStyle = g; c.fillRect(0, 0, W, H); c.restore();
    fx.glow(c, 960, 380, 700, P.orangeL, 0.35 * calm, 'screen');
    fx.particles(c, t, { kind: 'dust', n: 70, seed: 'c2dust', rise: 22, life: 7, size: 1.8, color: P.paper, alpha: 0.5 * calm, sway: 26, glow: true });
  }
  const out = { scan: 0.04, vignette: 0.55 };
  // ---- line 59: 「大好きだ！」 ×2 on the flood (no character yet)
  if (t < L60.t) {
    const T2 = L59.t + 1.22;
    const parts = ['「大好きだ！」', '「大好きだ！」'];
    let sh = fx.shake(t, L59.t, 6, 0.6, 'c2a');
    const sh2 = fx.shake(t, T2, 6, 0.6, 'c2b');
    sh = [sh[0] + sh2[0], sh[1] + sh2[1]];
    c.save(); c.translate(sh[0], sh[1]);
    const B = lay({ text: parts[0], family: F.smb, weight: 800, size: 180, maxW: 1500, maxLines: 1, track: 0, lineH: 1 });
    fx.drawBlock(c, B, 900, 430, { align: 'center', color: P.ink, reveal: { style: 'slam', rt: t - L59.t, dur: 0.12 } });
    if (t >= T2) fx.drawBlock(c, B, 1060, 680, { align: 'center', color: P.ink, alpha: 0.92, reveal: { style: 'slam', rt: t - T2, dur: 0.12 } });
    c.restore();
    if (S.cfg.showZh) {
      const ZB = lay({ text: L59.zh, family: F.zh, weight: 400, size: 34, maxW: 1400, maxLines: 1, track: 0.06, lineH: 1.4 });
      fx.drawBlock(c, ZB, 960, 860, { align: 'center', color: P.ink, alpha: 0.7 * smooth(L59.t + 0.2, L59.t + 0.6, t) });
    }
    out.cuts = [{ t: T2, flash: P.paper, flashA: 0.5, glitch: 0.5, id: 2 }];
    out.tone = 'light';
    return out;
  }
  // ---- 60–65: full colour, centred, lyric band
  const onsets = [60, 61, 62, 63, 64, 65].map((i) => LINES[i].t);
  let pulse = 0; for (const o of onsets) { const d = t - o; if (d >= 0 && d < 0.6) pulse = Math.max(pulse, Math.sin(Math.PI * d / 0.6) * (1 - d / 0.6)); }
  const ringsA = (1 - floodK) * (1 - calm * 0.7);
  if (ringsA > 0) rings(S, 960, 410, { r: 320, a: ringsA * 0.8, colour: mix(P.gold, P.orangeL, 0.3), colour2: P.orangeL, speed: 1.6 });
  const ps = 1 + 0.025 * pulse + 0.03 * calm;
  const appear = smooth(L60.t, L60.t + 0.25, t);
  const ch = { cx: 960, by: 796, h: 736 * ps };
  const glitchHer = (t >= LINES[63].t && t < LINES[65].t) && rnd('c2g', bucket(t, 12)) < 0.35;
  if (floodK > 0) fx.glow(c, 960, 420, 520, P.paper, 0.55 * floodK, 'source-over');
  drawChar(S, Object.assign({ mode: 'mono', cm: 1, a: appear, rim: 0.6, warm: 0.4 + 0.3 * calm, paperGlow: 0.25 * floodK }, ch));
  if (glitchHer) out.glitch = { slice: 0.45, sliceOpts: { y0: 60, y1: 800, amp: 70 }, rgb: 3 };
  const li = activeLine(t, [60, 61, 62, 63, 64, 65]);
  if (li >= 0) {
    const ln = LINES[li];
    const onFlood = li === 60;
    const colr = onFlood ? P.ink : P.paper;
    if (li === 60) {
      lyric(S, 60, { x: 960, y: 900, align: 'center', size: 96, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, track: 0.08, color: colr, reveal: 'slam', rdur: 0.12,
        spans: [{ match: '機械の声', color: P.paper }],
        charFx: (it, s) => { if (it.c.span) { const b = bucket(t, 15); if (rnd('c2t', b, it.k) < 0.22) s.dx += (rnd('c2x', b, it.k) - 0.5) * 22; } },
        zh: { dy: 56, color: P.ink, alpha: 0.7 } });
      // title-glitch callback: slices through 機械の声
      if (rnd('c2sl', bucket(t, 10)) < 0.4) out.glitch = { slice: 0.3, sliceOpts: { y0: 820, y1: 910, amp: 50, n: 4 } };
    } else if (li === 63 || li === 64) {
      const lt = t - ln.t;
      const stut = (lt < 0.3) || rnd('stut', li, bucket(t, 10)) < 0.25;
      if (stut) {
        for (const [dx, col, a] of [[-14, '#FF5A3A', 0.5], [14, '#3AD8FF', 0.4]]) lyric(S, li, { x: 960 + dx, y: 900 + (dx > 0 ? 4 : -4), align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: col, alpha: a, reveal: 'none', zh: false });
      }
      lyric(S, li, { x: 960 + (stut ? (rnd('sx', bucket(t, 30)) - 0.5) * 10 : 0), y: 900, align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: colr, reveal: 'pop', rdur: 0.4, zh: { dy: 56 } });
    } else if (li === 65) {
      lyric(S, 65, { x: 960, y: 900, align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: P.paper, reveal: 'charfade', rdur: 2.6, track: 0.12, glow: { color: rgba(P.orangeL, 0.6), blur: 24 }, zh: { dy: 56, delay: 1.2 } });
    } else {
      lyric(S, li, { x: 960, y: 900, align: 'center', size: 92, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: colr, reveal: 'slice', rdur: 0.4, zh: { dy: 56 } });
    }
  }
  out.tone = floodK > 0.5 ? 'light' : 'dark';
  if (t < L60.t + 0.05) out.cuts = [{ t: L60.t, flash: P.paper, flashA: 0.7, glitch: 0.4, id: 3 }];
  return out;
};

/* -------------------------------------------------------------- prayer */
SCENES.prayer = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  fill(c, '#1E120B');
  fx.glow(c, 1380, 380, 900, P.orangeD, 0.35, 'screen');
  fx.glow(c, 1380, 420, 420, P.orangeL, 0.12, 'screen');
  // face close-up, right, breathing
  const toBody = ease.inOutSine(inv(LINES[73].t, LINES[73].t + 3.4, t));
  const breath = 1 + 0.005 * (1 - Math.cos((t * TAU) / 4));
  const sc = 1.6 * breath, fw = A.face.width * sc, fh = A.face.height * sc;
  const fcx = 1440, fcy = 470; // face centre on screen
  const ox = (520 - A.faceRect.x) * sc, oy = (190 - A.faceRect.y) * sc; // char (520,190) = face centre
  const fxp = fcx - ox, fyp = fcy - oy;
  const faceA = 1 - smooth(0, 0.55, toBody);
  // light beam (line 68)
  const beam = lineAlpha(t, LINES[68].t, LINES[68].end + 0.8, 1.0, 1.4);
  if (beam > 0) {
    c.save();
    const bx = 1440;
    const g = c.createLinearGradient(bx - 60, 0, bx + 60, 0);
    g.addColorStop(0, rgba(P.paper, 0)); g.addColorStop(0.5, rgba(P.paper, 0.3 * beam)); g.addColorStop(1, rgba(P.paper, 0));
    c.fillStyle = g; c.fillRect(bx - 60, 0, 120, H);
    const g2 = c.createLinearGradient(bx - 6, 0, bx + 6, 0);
    g2.addColorStop(0, rgba(P.paper, 0)); g2.addColorStop(0.5, rgba(P.paper, 0.6 * beam)); g2.addColorStop(1, rgba(P.paper, 0));
    c.fillStyle = g2; c.fillRect(bx - 6, 0, 12, H * ease.outCubic(inv(LINES[68].t, LINES[68].t + 1.2, t)));
    c.restore();
    fx.particles(c, t, { kind: 'dust', n: 26, seed: 'beam', x0: bx - 50, x1: bx + 50, y0: 0, y1: H, rise: -30, life: 6, size: 1.4, color: P.paper, alpha: 0.6 * beam, sway: 10 });
  }
  if (faceA > 0) {
    blit(c, K.faceGlow, fxp - 160 * sc, fyp - 160 * sc, K.faceGlow.width * sc, K.faceGlow.height * sc, 0.35 * faceA, 'screen');
    blit(c, K.faceRim, fxp - 60 * sc + 6, fyp - 60 * sc + 3, K.faceRim.width * sc, K.faceRim.height * sc, 0.55 * faceA);
    const cm = colourMix(w);
    blit(c, A.faceMono, fxp, fyp, fw, fh, faceA * (1 - cm));
    blit(c, A.face, fxp, fyp, fw, fh, faceA * cm);
  }
  if (toBody > 0) {
    fx.glow(c, 1420, 520, 620, P.orangeL, 0.35 * Math.sin(Math.PI * toBody), 'screen');
    drawChar(S, { cx: 1420, by: 1035, h: 960, mode: 'mono', cm: colourMix(w), a: smooth(0.4, 1, toBody), rim: 0.6, warm: 0.3 });
  }
  // warm soft waveform (70–73)
  const wv = smooth(LINES[70].t, LINES[70].t + 1.5, t) * (1 - smooth(304.0, 305.0, t));
  if (wv > 0) fx.waveform(c, 96, 1180, 860, { t: t * 0.6, amp: 34 + 18 * onsetEnv(t, [70, 71, 72, 73], 1.6), color: P.orangeL, lw: 1.6, glow: 16, alpha: 0.7 * wv, detail: 0.3, n: 300 });
  // lyrics left, Zen Old Mincho Regular 64, slow per-char fade
  const li = activeLine(t, [66, 67, 68, 69, 70, 71, 72, 73]);
  if (li >= 0) {
    const ln = LINES[li];
    const long = ln.end - ln.t > 6;
    lyric(S, li, { x: 150, y: 500, size: 64, weight: 400, maxW: 860, color: P.paper, reveal: 'charfade', rdur: Math.min(1.6, 0.6 + [...ln.ja].length * 0.06), exit: 'rise', edur: long ? 0.9 : 0.45, exitAt: long ? ln.end - 0.9 : ln.end - 0.45, zh: { dy: 56, delay: 0.5 } });
  }
  return { scan: 0.04, vignette: 0.9 };
};

/* --------------------------------------------------------------- build */
SCENES.build = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  fill(c, '#1E120B');
  fx.glow(c, 1400, 420, 900, P.orangeD, 0.33, 'screen');
  const L75 = LINES[75], L76 = LINES[76], L77 = LINES[77];
  const sink = 30 * ease.inOutCubic(inv(L75.t, L75.t + 1.4, t)) * (1 - ease.inOutCubic(inv(L76.t + 0.5, L76.t + 2.5, t)));
  const embrace = ease.inOutSine(inv(L77.t, L77.t + 3.2, t));
  fx.particles(c, t, { kind: 'dust', n: 40, seed: 'bd', x0: 900, x1: 1820, rise: 16, life: 8, size: 1.5, color: P.paper2, alpha: 0.3 + 0.3 * embrace });
  drawChar(S, { cx: 1420, by: 1035 + sink, h: 960, mode: 'mono', cm: colourMix(w), a: 1, rim: 0.6 + 0.3 * embrace, warm: 0.3 + 0.6 * embrace });
  // strike motif (75) — a long thin diagonal through the frame
  const strike = ease.inOutCubic(inv(L75.t + 1.0, L75.t + 1.5, t)) * (1 - smooth(L76.t - 0.3, L76.t + 0.2, t));
  if (strike > 0) {
    c.save(); c.strokeStyle = P.paper; c.globalAlpha = 0.35 * Math.min(1, strike * 3); c.lineWidth = 2;
    c.beginPath(); c.moveTo(1100, 120); c.lineTo(1100 + 640 * strike, 120 + 860 * strike); c.stroke(); c.restore();
  }
  const li = activeLine(t, [74, 75, 76, 77]);
  const X = 150, Y = 500;
  if (li === 74) {
    // text with noise overlay: draw into scratch, punch noise
    const tmp = K.tmp, tx = tmp.getContext('2d');
    tx.setTransform(1, 0, 0, 1, 0, 0); tx.clearRect(0, 0, W, H);
    const S2 = Object.assign({}, S, { ctx: tx });
    const r = lyric(S2, 74, { x: X, y: Y, size: 72, maxW: 920, color: P.paper, reveal: 'fadeup', spans: [{ match: '電子音', family: F.dot, weight: 400, color: P.orangeL }], zh: { dy: 58 } });
    if (r) {
      const b = bucket(t, 24);
      tx.save(); tx.globalCompositeOperation = 'destination-out'; tx.globalAlpha = 0.45;
      const pat = tx.createPattern(K.noise, 'repeat'); tx.translate(-(b * 37) % 256, -(b * 91) % 256); tx.fillStyle = pat; tx.fillRect(0, 0, W + 256, H + 256); tx.restore();
      // horizontal noise bands
      const rr = rng('bn', b);
      tx.save(); tx.globalCompositeOperation = 'source-atop'; tx.fillStyle = P.paper;
      for (let i = 0; i < 6; i++) { tx.globalAlpha = 0.3 * rr(); tx.fillRect(0, r.box.y0 + rr() * (r.box.y1 - r.box.y0), W, 1 + rr() * 3); }
      tx.restore();
      blit(c, tmp, 0, 0, W, H, 1);
    }
  } else if (li === 75) {
    const r = lyric(S, 75, { x: X, y: Y, size: 72, maxW: 920, color: P.paper, reveal: 'fadeup', zh: { dy: 58 } });
    if (r) {
      const st = ease.inOutCubic(inv(L75.t + 1.0, L75.t + 1.45, t));
      const items = r.box.items, a = items.findIndex((it) => it.c.ch === 'ゴ');
      if (a >= 0 && st > 0) {
        const x0 = items[a].x, x1 = items[items.length - 1].x + items[items.length - 1].c.w, y = items[a].y - r.B.size * 0.32;
        c.save(); c.strokeStyle = P.orange; c.lineWidth = 5; c.globalAlpha = 0.95 * (1 - smooth(-0.25, 0, r.et));
        c.beginPath(); c.moveTo(x0 - 8, y); c.lineTo(lerp(x0 - 8, x1 + 8, st), y); c.stroke(); c.restore();
      }
    }
  } else if (li === 76) {
    lyric(S, 76, { x: X, y: 440, size: 84, family: F.smb, weight: 800, maxW: 960, maxLines: 2, color: P.paper, reveal: 'scatter', rdur: 0.9, lineH: 1.3, spans: [{ match: '「', color: P.gold }, { match: '」', color: P.gold }], shrinkFirst: 1, zh: { dy: 62 } });
  } else if (li === 77) {
    lyric(S, 77, { x: X, y: Y, size: 72, weight: 400, maxW: 920, color: P.paper, reveal: 'charfade', rdur: 1.6, glow: { color: rgba(P.orangeL, 0.5), blur: 20 * embrace }, zh: { dy: 58, delay: 0.6 } });
  }
  return { scan: 0.04, vignette: 0.85, warmVignette: 1.15 * embrace, warmVignetteColour: '#120804' };
};

/* ------------------------------------------------------------- final_a */
SCENES.final_a = (S) => {
  const c = S.ctx, t = S.t, w = S.w;
  fill(c, '#2A170C');
  fx.glow(c, 960, 420, 900, P.orangeD, 0.45, 'screen');
  fx.glow(c, 960, 380, 480, P.orange, 0.2, 'screen');
  hexGrid(c, 0.09, 1, { x: 960, y: 420, r0: 260, r1: 1000, colour: '#1E1009', a: 0.9 });
  rings(S, 960, 410, { r: 320, a: 1, colour: P.gold, colour2: P.orangeL, speed: 3.2, labels: ['SYNC 1.000'] });
  fx.particles(c, t, { kind: 'ember', n: 40, seed: 'faem', rise: 60, life: 6, size: 2, color: P.orangeL, alpha: 0.6, sway: 18, glow: true });
  const ch = { cx: 960, by: 796, h: 736 };
  drawChar(S, Object.assign({ mode: 'mono', cm: 1, a: 1, rim: 0.7, warm: 0.45 }, ch));
  // 84 link visual
  const L84 = LINES[84];
  const lk = lineAlpha(t, L84.t - 0.1, S.sec.end + 0.5, 0.4, 0.3);
  if (lk > 0) {
    const [nx, ny] = charPt(ch, 330, 560);
    const sx = 180, sy = 250, sw = 380, sh = 220;
    c.save(); c.globalAlpha = lk;
    c.fillStyle = rgba('#120A06', 0.6); c.fillRect(sx, sy, sw, sh);
    c.strokeStyle = P.gold; c.lineWidth = 1.5; c.strokeRect(sx, sy, sw, sh);
    fx.glow(c, sx + sw / 2, sy + sh / 2, 200, P.orangeL, 0.25);
    c.restore();
    fx.brackets(c, sx - 10, sy - 10, sw + 20, sh + 20, { len: 18, color: P.paper, alpha: 0.8 * lk });
    fx.label(c, '君 // SCREEN', sx, sy - 22, { size: 15, color: P.paper, alpha: 0.8 * lk, upper: false });
    fx.waveform(c, sx + 20, sx + sw - 20, sy + sh / 2, { t, amp: 40, color: P.orangeL, lw: 1.5, alpha: 0.9 * lk, n: 120 });
    const dp = ease.inOutCubic(inv(L84.t + 0.2, L84.t + 1.2, t));
    const ax = sx + sw, ay = sy + sh / 2;
    c.save(); c.strokeStyle = P.orangeL; c.globalAlpha = lk; c.lineWidth = 2;
    c.beginPath(); c.moveTo(ax, ay); c.lineTo(lerp(ax, nx, dp), lerp(ay, ny, dp)); c.stroke();
    c.fillStyle = P.paper;
    c.beginPath(); c.arc(ax, ay, 6, 0, TAU); c.fill();
    if (dp >= 1) {
      c.beginPath(); c.arc(nx, ny, 7, 0, TAU); c.fill();
      fx.ring(c, nx, ny, { r: 16 + 6 * Math.sin(t * 6), color: P.orangeL, alpha: lk * 0.8, lw: 1.5 });
      for (let k = 0; k < 5; k++) { const u = fx.fract(t * 0.9 + k / 5); c.globalAlpha = lk * Math.sin(Math.PI * u); c.fillRect(lerp(ax, nx, u) - 3, lerp(ay, ny, u) - 3, 6, 6); }
    }
    c.restore();
    fx.label(c, 'LINK ESTABLISHED · PRIVATE', (ax + nx) / 2 - 20, (ay + ny) / 2 - 34, { size: 13, color: P.paper, alpha: lk * smooth(L84.t + 1.1, L84.t + 1.5, t) * 0.8, align: 'center' });
  }
  const li = activeLine(t, [78, 79, 80, 81, 82, 83, 84]);
  if (li === 80) {
    lyric(S, 80, { x: 960, y: 905, align: 'center', size: 104, family: F.cor, fstyle: 'italic', weight: 500, maxW: 1640, maxLines: 1, track: 0.06, color: P.paper, reveal: 'typewriter', rdur: 0.7, cursor: { color: P.orangeL, blink: true, alpha: 0.9, w: 14 }, zh: false });
  } else if (li >= 0) {
    const spans = li === 84 ? [{ match: 'リンク', color: P.orange }] : undefined;
    lyric(S, li, { x: 960, y: 900, align: 'center', size: 88, family: F.smb, weight: 800, maxW: 1640, maxLines: 1, color: P.paper, reveal: 'slice', rdur: 0.42, spans, zh: { dy: 56 }, shrinkFirst: 0.7 });
  }
  return { scan: 0.04, vignette: 0.75 };
};

/* ------------------------------------------------------------- final_b */
function ringAngle(t) { // rings decelerate and stop at ~370
  const t0 = 366.0, t1 = 370.0;
  if (t < t0) return t * 3.2;
  const T = Math.min(t, t1) - t0, D = t1 - t0;
  return t0 * 3.2 + 3.2 * (T - (T * T) / (2 * D));
}
const FB_CHAR = { cx: 1420, by: 1035, h: 960 };
/** final_b / outro shared background: orange field around her, darkened text side; dim → 0..1 toward embers */
function fbBase(c, dim = 0) {
  const sunC = charPt(FB_CHAR, 540, 600);
  const g = c.createRadialGradient(sunC[0], sunC[1], 60, sunC[0], sunC[1], 1500);
  g.addColorStop(0, rgba(mix(P.orangeL, '#5A2A12', dim * 0.7))); g.addColorStop(0.35, rgba(mix(P.orange, '#3A1C0C', dim * 0.7)));
  g.addColorStop(0.75, rgba(mix(P.orangeD, '#24110A', dim * 0.8))); g.addColorStop(1, rgba(mix('#4A1E0A', '#1A0B05', dim)));
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  const lg = c.createLinearGradient(0, 0, 1300, 0);
  lg.addColorStop(0, rgba('#2A1206', 0.72 * (1 - dim))); lg.addColorStop(1, rgba('#2A1206', 0));
  c.fillStyle = lg; c.fillRect(0, 0, 1300, H);
  return sunC;
}
/** 89–92: the poem accumulating top→bottom */
function drawPoem(S, X, outA) {
  const c = S.ctx, t = S.t;
  const ys = [270, 420, 570, 760];
  const shadow = { color: 'rgba(30,10,2,0.55)', blur: 18 };
  [89, 90, 91, 92].forEach((i, k) => {
    const ln = LINES[i];
    if (t < ln.t) return;
    const size = i === 92 ? 108 : 76;
    const B = lay({ text: ln.ja, family: F.smb, weight: 800, size, maxW: 940, maxLines: 1, track: 0.02, lineH: 1.2, shrinkFirst: 0.6 });
    const rt = t - ln.t;
    const dimK = i === 92 ? 1 : lerp(1, 0.42, smooth(LINES[i + 1].t, LINES[i + 1].t + 0.6, t));
    fx.drawBlock(c, B, X, ys[k], { color: P.paper, alpha: dimK * outA, reveal: { style: 'slice', rt, dur: 0.42, seed: i }, glow: shadow, sliceAmp: 60 });
    if (S.cfg.showZh) {
      const ZB = lay({ text: ln.zh, family: F.zh, weight: 400, size: i === 92 ? 34 : 28, maxW: 940, maxLines: 1, track: 0.05, lineH: 1.3 });
      fx.drawBlock(c, ZB, X + 2, ys[k] + (i === 92 ? 64 : 48), { color: P.paper, alpha: 0.62 * dimK * outA * smooth(0.15, 0.6, rt) });
    }
  });
}
SCENES.final_b = (S) => {
  const c = S.ctx, t = S.t;
  const hold = t >= LINES[92].t;
  const hudOut = (k) => 1 - smooth(367.6 + k * 0.9, 368.4 + k * 0.9, t);
  const CB = FB_CHAR;
  const sunC = fbBase(c, 0);
  const burst = smooth(LINES[85].t, LINES[85].t + 0.8, t);
  c.save(); c.translate(sunC[0], sunC[1]); c.rotate(t * 0.04);
  for (let i = 0; i < 64; i++) {
    c.rotate(TAU / 64);
    const len = 600 + (i % 4 === 0 ? 900 : i % 2 === 0 ? 600 : 350) * burst;
    c.globalAlpha = (i % 4 === 0 ? 0.32 : 0.16) * burst * hudOut(2);
    c.fillStyle = P.gold;
    c.beginPath(); c.moveTo(80, -1.5); c.lineTo(len, -(i % 4 === 0 ? 7 : 3)); c.lineTo(len, i % 4 === 0 ? 7 : 3); c.lineTo(80, 1.5); c.closePath(); c.fill();
  }
  c.restore();
  rings(S, sunC[0], sunC[1] - 120, { r: 300, a: hudOut(0), colour: P.gold, colour2: P.paper, rot: ringAngle(t), labels: ['VOICE 100%', '君の音'] });
  hexGrid(c, 0.06 * hudOut(1), 1);
  fx.particles(c, t, { kind: 'dust', n: 60, seed: 'fbd', rise: 26, life: 7, size: 2, color: P.paper, alpha: 0.55, sway: 24, glow: true });
  // 86 — 無価値 words return, wiped by an orange sweep
  const L86 = LINES[86];
  const sweep = ease.inOutCubic(inv(L86.t + 1.0, L86.t + 1.9, t));
  const wA = lineAlpha(t, L86.t, L86.end + 0.5, 0.4, 0.3);
  if (wA > 0) {
    const sx = lerp(-200, W + 200, sweep);
    for (let i = 0; i < 18; i++) {
      const r = rng('muk2', i);
      const x = 120 + r() * 1680, y = 140 + r() * 760;
      if (x < sx) continue;
      fx.label(c, '無価値', x, y, { size: 18 + Math.floor(r() * 3) * 6, family: F.dot, color: P.ink, alpha: wA * (0.25 + r() * 0.3), upper: false });
    }
    if (sweep > 0 && sweep < 1) {
      const sg = c.createLinearGradient(sx - 220, 0, sx + 20, 0);
      sg.addColorStop(0, rgba(P.orange, 0)); sg.addColorStop(0.85, rgba(P.orangeL, 0.75)); sg.addColorStop(1, rgba(P.paper, 0.9));
      c.fillStyle = sg; c.fillRect(sx - 220, 0, 240, H);
    }
  }
  drawChar(S, Object.assign({ mode: 'mono', cm: 1, a: 1, rim: 0.5, warm: 0.4, paperGlow: 0.2 }, CB));
  // lyrics (left zone)
  const X = 150;
  const li = activeLine(t, [85, 86, 87, 88]);
  const shadow = { color: 'rgba(30,10,2,0.55)', blur: 18 };
  if (li === 88) {
    lyric(S, 88, { x: X, y: 560, size: 136, family: F.smb, weight: 800, maxW: 940, maxLines: 1, color: P.paper, reveal: 'slice', rdur: 0.45, spans: [{ match: '一番', color: '#FFD27A' }], glow: shadow, shrinkFirst: 0.7, zh: { dy: 74, size: 34 } });
  } else if (li >= 0) {
    lyric(S, li, { x: X, y: 520, size: 88, family: F.smb, weight: 800, maxW: 940, maxLines: 2, color: P.paper, reveal: 'slice', rdur: 0.42, glow: shadow, zh: { dy: 60 } });
  }
  // 89–92 poem accumulates top→bottom
  if (t >= LINES[89].t) {
    drawPoem(S, X, 1);
    fx.label(c, '— 守ってあげられるのに —', X, 930, { size: 13, color: P.paper, alpha: 0.4 * smooth(LINES[92].t + 1, LINES[92].t + 2, t) * hudOut(1), upper: false });
  }
  return { scan: 0.035, vignette: 0.6, tcAlpha: hudOut(3), bugAlpha: 1 };
};

/* --------------------------------------------------------------- outro */
SCENES.outro = (S) => {
  const c = S.ctx, t = S.t;
  // final_b look continues underneath during the first seconds (HUD already gone)
  const CB = FB_CHAR;
  const toPaper = ease.inOutCubic(inv(384.3, 385.7, t));
  const crt = t >= 397.6;
  if (toPaper < 1) {
    fbBase(c, smooth(372, 380, t));
    const dustA = 1 - smooth(372.5, 378, t);
    if (dustA > 0) fx.particles(c, t, { kind: 'dust', n: 60, seed: 'fbd', rise: 26, life: 7, size: 2, color: P.paper, alpha: 0.55 * dustA, sway: 24, glow: true });
    // the poem fades out
    const la = 1 - smooth(372.0, 373.4, t);
    if (la > 0) drawPoem(S, 150, la);
    // dissolve into rising particles (373–381), leaving the book
    const dp = clamp((t - 373.0) / 8.0);
    const k = CB.h / 1000, cw = A.w * k, x0 = CB.cx - cw / 2, y0 = CB.by - CB.h;
    // book travels to centre & closes (381–385)
    const bookMove = ease.inOutCubic(inv(381.0, 383.0, t));
    if (dp <= 0) {
      drawChar(S, Object.assign({ mode: 'mono', cm: 1, a: 1, rim: 0.5, warm: 0.4 }, CB));
    } else if (dp < 1) {
      // erosion via threshold map
      const id = K.dissolveData, src = A.colData.data, d = id.data, thr = A.thr;
      const p = dp * 1.05;
      for (let i = 0, n = thr.length; i < n; i++) {
        const j = i * 4;
        const th = thr[i];
        if (th > p) { d[j] = src[j]; d[j + 1] = src[j + 1]; d[j + 2] = src[j + 2]; d[j + 3] = src[j + 3]; }
        else if (th > p - 0.03) { d[j] = 255; d[j + 1] = 200; d[j + 2] = 130; d[j + 3] = src[j + 3]; }
        else d[j + 3] = 0;
      }
      K.dissolve.getContext('2d').putImageData(id, 0, 0);
      blit(c, A.warmGlow, x0 - 180 * k, y0 - 180 * k, A.warmGlow.width * k, A.warmGlow.height * k, 0.4 * (1 - dp), 'screen');
      blit(c, K.dissolve, x0, y0, cw, CB.h, 1);
    }
    // particles rising from eroded points
    if (dp > 0) {
      c.save();
      for (const pt of A.pts) {
        const th = A.thr[(pt.y | 0) * A.w + (pt.x | 0)];
        if (th > 1.5) continue;
        const born = 373.0 + th / 1.05 * 8.0;
        const age = t - born;
        if (age < 0 || age > 3.2) continue;
        const u = age / 3.2;
        const px = x0 + pt.x * k + Math.sin(age * 1.5 + pt.r * 9) * 22 * u + (pt.r - 0.5) * 60 * u;
        const py = y0 + pt.y * k - age * (60 + pt.r * 90) - age * age * 8;
        c.globalAlpha = (1 - u) * 0.9;
        c.fillStyle = `rgb(${Math.min(255, pt.c[0] + 60)},${Math.min(255, pt.c[1] + 40)},${pt.c[2]})`;
        const s = 1.2 + pt.r * 2.2;
        c.fillRect(px, py, s, s);
      }
      c.restore();
    }
    if (dp >= 1) {
      // only the book remains: it drifts to the centre, a paper cover closes over it,
      // and the closed paper card grows to become the page
      const bk = A.bookOnlyRect, kf = CB.h / A.full.height;
      const bx = x0 + bk.x * kf, by = y0 + bk.y * kf, bw = bk.w * kf, bh = bk.h * kf;
      const sc = lerp(1, 2.4, bookMove);
      const cx = lerp(bx + bw / 2, 960, bookMove), cy = lerp(by + bh / 2, 540, bookMove);
      const dw = bw * sc, dh = bh * sc;
      fx.glow(c, cx, cy, 160 * sc, P.orangeL, 0.3 * (1 - toPaper), 'screen');
      c.save(); c.translate(cx, cy); c.rotate(0.22 * bookMove);
      c.drawImage(A.bookOnly, -dw / 2, -dh / 2, dw, dh);
      c.restore();
      const close = ease.inOutCubic(inv(383.0, 384.2, t));
      if (close > 0) {
        // the cover swings shut: a paper panel hinged on the left edge, with a shading edge
        const pw = (dw + 12) * close;
        c.save();
        c.shadowColor = 'rgba(20,8,2,0.55)'; c.shadowBlur = 24; c.shadowOffsetX = 6;
        c.fillStyle = P.paper; c.fillRect(cx - dw / 2 - 6, cy - dh / 2 - 6, pw, dh + 12);
        c.restore();
        c.save(); c.globalAlpha = 0.5 * (1 - close); c.fillStyle = P.paper2;
        c.fillRect(cx - dw / 2 - 6 + pw - 10, cy - dh / 2 - 6, 10, dh + 12); c.restore();
        // gold hairline frame on the closed card
        c.save(); c.globalAlpha = smooth(0.7, 1, close) * (1 - toPaper); c.strokeStyle = P.goldD; c.lineWidth = 1;
        c.strokeRect(cx - dw / 2 + 8, cy - dh / 2 + 8, dw - 16, dh - 16); c.restore();
      }
      if (toPaper > 0) {
        const L = lerp(cx - dw / 2 - 6, 0, toPaper), T = lerp(cy - dh / 2 - 6, 0, toPaper);
        const R = lerp(cx + dw / 2 + 6, W, toPaper), B = lerp(cy + dh / 2 + 6, H, toPaper);
        c.save(); c.shadowColor = 'rgba(20,8,2,0.5)'; c.shadowBlur = 40 * (1 - toPaper);
        c.fillStyle = P.paper; c.fillRect(L, T, R - L, B - T); c.restore();
      }
    }
  }
  if (toPaper >= 1) {
    // cream paper with ink credits
    fill(c, P.paper);
    fx.glow(c, 960, 520, 900, '#FFF8EC', 0.5);
    const credits = [
      ['機械の声 — The Voice of AI', 38],
      ['原曲：香椎モイミ（V.I.P #3 / 音楽的同位体）', 30],
      ['原MV：まるいち（演出）・strobo（タイポグラフィ）・りたお（イラスト）', 30],
      ['本作角色：智械', 30],
      ['Fan-made MV · HTML Canvas', 28],
    ];
    const y0 = 380;
    const ruleK = ease.inOutCubic(inv(385.9, 387.0, t));
    c.save(); c.fillStyle = P.goldD; c.globalAlpha = 0.8;
    c.fillRect(960 - 260 * ruleK, y0 - 70, 520 * ruleK, 1);
    c.fillRect(960 - 260 * ruleK, y0 + 4 * 66 + 50, 520 * ruleK, 1);
    c.translate(960, y0 - 70); c.rotate(Math.PI / 4); c.globalAlpha = ruleK; c.fillRect(-4, -4, 8, 8);
    c.restore();
    credits.forEach(([s, sz], i) => {
      const T = 386.2 + i * 0.75;
      const B = lay({ text: s, family: F.zom, weight: i === 0 ? 700 : 400, size: sz, maxW: 1500, maxLines: 1, track: 0.04, lineH: 1.2 });
      fx.drawBlock(c, B, 960, y0 + i * 66, { align: 'center', color: P.ink, alpha: 1 - smooth(396.6, 397.5, t), reveal: { style: 'fadeup', rt: t - T, dur: 0.8 } });
    });
    // [智械] + blinking _
    const ta = smooth(391.0, 391.6, t);
    if (ta > 0) {
      const w0 = fx.label(c, '[智械] ', 960 - 50, y0 + 4 * 66 + 130, { size: 24, color: P.ink, alpha: ta, track: 0.2 });
      if (Math.floor(t * 2.4) % 2 === 0) { c.save(); c.globalAlpha = ta; c.fillStyle = P.orangeD; c.fillRect(960 - 50 + w0, y0 + 4 * 66 + 128, 16, 3); c.restore(); }
    }
  }
  // CRT-off collapse (reverse of boot)
  if (crt) {
    const snap = fx.snapshot(c);
    fill(c, '#000');
    const v = ease.inCubic(inv(397.6, 398.25, t));
    const hcol = ease.inCubic(inv(398.25, 398.75, t));
    const hh = Math.max(2, H * (1 - v));
    const ww = Math.max(4, W * (1 - hcol));
    const fade = 1 - smooth(398.8, 399.4, t);
    c.save(); c.globalAlpha = fade;
    if (v < 1) c.drawImage(snap, 0, 0, W, H, 0, H / 2 - hh / 2, W, hh);
    else { c.fillStyle = P.paper; c.fillRect(W / 2 - ww / 2, H / 2 - 1, ww, 2); fx.glow(c, W / 2, H / 2, 60 * (1 - hcol) + 20, P.paper, 0.6); }
    c.restore();
  }
  const paper = toPaper >= 1 && !crt;
  return { tone: paper ? 'light' : 'dark', vignette: paper ? 0.22 : crt ? 0 : 0.7, scan: crt ? 0.02 : 0.04, bugAlpha: 1 - smooth(384.0, 385.0, t), hideTC: crt, grain: crt ? 0.02 : 0.05 };
};
