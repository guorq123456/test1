// 第 6 章「未知数」：有理系数一元多项式，以及求导、积分。
//
// 值：{ t: 'poly', c: [a0, a1, a2, …] }，c[i] 是 xⁱ 的系数（有理数），最高次系数非零。
// 常数多项式不存在：任何运算结果只要是常数，就直接返回有理数。所以 x − x = 0 得到的
// 就是初等篇的单卡 0，多项式和有理数天然互通；反过来，有理数也可以当常数多项式参与运算。
//
// key："p:" + 系数从高次到低次用逗号连接：x² + 2x + 1 → "p:1,2,1"，x/2 − 1 → "p:1/2,-1"。

import { R, isR, ZERO, ONE, eq, isInt, add, mul, div, inv, neg, rkey, fmtR, height, cmp, parseQKey, OVER, sup, iroot } from '../math.js';
import { registerType, fmtV, PROBE_SMALL, BIN } from '../values.js';
import { registerNamed, namedU, bindU, aff } from '../unary.js';

// 次数上限。超过它的结果算作"太大"（返回 OVER），和数字溢出一样处理。
export const MAX_DEG = 12;

export const isP = v => v !== null && typeof v === 'object' && v.t === 'poly' && Array.isArray(v.c);
const coef = v => (isR(v) ? [v] : v.c);
export const degOf = v => (isR(v) ? 0 : v.c.length - 1);

// 把系数表整理成值：去掉高位的 0；常数就返回有理数；系数溢出返回 OVER
export function poly(c) {
  for (const a of c) if (!isR(a)) return a === OVER ? OVER : null;
  let n = c.length;
  while (n > 0 && c[n - 1].n === 0) n--;
  if (n === 0) return ZERO;
  if (n === 1) return c[0];
  if (n - 1 > MAX_DEG) return OVER;
  return { t: 'poly', c: c.slice(0, n) };
}

// 用整数或 "n/d" 字符串快速写多项式，系数从高次到低次：P(1, 2, 1) = x² + 2x + 1
export const P = (...hi) => poly(hi.map(a => (typeof a === 'string' ? parseQKey(a) : R(a))).reverse());
export const X = P(1, 0);

function addC(a, b) {
  const n = Math.max(a.length, b.length);
  const out = [];
  for (let i = 0; i < n; i++) {
    const s = add(a[i] ?? ZERO, b[i] ?? ZERO);
    if (!isR(s)) return s;
    out.push(s);
  }
  return out;
}

export function addP(x, y) {
  const c = addC(coef(x), coef(y));
  return Array.isArray(c) ? poly(c) : c;
}

export function subP(x, y) {
  const c = addC(coef(x), coef(y).map(neg));
  return Array.isArray(c) ? poly(c) : c;
}

export function mulP(x, y) {
  const a = coef(x);
  const b = coef(y);
  if (a.length - 1 + (b.length - 1) > MAX_DEG) return OVER;
  const out = Array.from({ length: a.length + b.length - 1 }, () => ZERO);
  for (let i = 0; i < a.length; i++) {
    if (a[i].n === 0) continue;
    for (let j = 0; j < b.length; j++) {
      const t = mul(a[i], b[j]);
      if (!isR(t)) return t;
      const s = add(out[i + j], t);
      if (!isR(s)) return s;
      out[i + j] = s;
    }
  }
  return poly(out);
}

export function powP(x, k) {
  if (k === 0) return ONE;
  if (degOf(x) * k > MAX_DEG) return OVER;
  let r = ONE;
  for (let i = 0; i < k; i++) {
    r = mulP(r, x);
    if (!isR(r) && !isP(r)) return r;
  }
  return r;
}

export const scaleP = (x, r) => poly(coef(x).map(a => mul(a, r)));

// ───────────────────────── 显示 ─────────────────────────

const CN = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'];

// 一项：系数 a（正数）乘以 xs 的 i 次方
function term(a, i, xs) {
  if (i === 0) return fmtR(a);
  const p = i === 1 ? xs : `${xs}${sup(i)}`;
  if (a.d === 1) return a.n === 1 ? p : `${a.n}${p}`;
  return a.n === 1 ? `${p}/${a.d}` : `${a.n}${p}/${a.d}`;
}

// 多项式的公式，xs 是变量的写法（'x'，或者代入别的式子时的 '(x + 1)'）
export function fmtPoly(c, xs = 'x') {
  let s = '';
  for (let i = c.length - 1; i >= 0; i--) {
    const a = c[i];
    if (a.n === 0) continue;
    const t = term(a.n < 0 ? neg(a) : a, i, xs);
    if (s === '') s = a.n < 0 ? `−${t}` : t;
    else s += a.n < 0 ? ` − ${t}` : ` + ${t}`;
  }
  return s === '' ? '0' : s;
}

// 算子公式里的输入。平时输入写成 x（"x + 1"、"x²"、"x′"）。可多项式的变量也叫 x：算子里一旦出现了
// 多项式的 x（绑定的常量是多项式，比如「乘以 x」；积分的上限 x），输入再写成 x 就会和它混在一起，
// 乘以 x 会写成 "x × x"，看起来像平方。这时输入统一写成填空的方格 □：□ × x、x^□、∫₀ˣ □ dt。
// （不用 "(·)"：游戏里 · 是乘号，"捧·步"、"a·x"。）
//
// 多项式当函数用（fmtCall）不用改：代入会把多项式里的每个 x 都换成输入，公式里剩下的 x 全是输入，
// 而且把 x 代入 p 得到的就是 p 自己，所以 "x²" 这样写不会误导。
export const SLOT = '□';
const LATIN_X = /(?<![A-Za-z])x(?![A-Za-z])/g;
// s 是输入的写法。已经含 □ 的，说明前面的步骤里已经出现过多项式的 x、输入早就改写成了 □，
// 这时 s 里的 x 都是多项式的变量，原样保留；否则 s 里的 x 都是输入，换成 □
export const slotted = s => (s.includes(SLOT) ? s : s.replace(LATIN_X, SLOT));
const wrapS = s => (/\s/.test(s) ? `(${s})` : s);

const KEY_RE = /^p:(-?\d+(\/\d+)?)(,-?\d+(\/\d+)?)+$/;

export function parsePolyKey(s) {
  if (typeof s !== 'string' || !KEY_RE.test(s)) return null;
  const hi = s.slice(2).split(',').map(parseQKey);
  if (hi.some(a => a === null) || hi[0].n === 0 || hi.length - 1 > MAX_DEG) return null;
  return { t: 'poly', c: hi.reverse() };
}

// ───────────────────────── 视野与探针 ─────────────────────────

const q = s => parseQKey(s);
// 视野里最常见的系数
const C = ['-2', '-1', '-1/2', '1/2', '1', '2'].map(q);
// 只有一项时系数可以多一些
const C1 = [...C, ...['-4', '-3', '-3/2', '-2/3', '-1/3', '-1/4', '1/4', '1/3', '2/3', '3/2', '3', '4'].map(q)];
const C0 = [ZERO, ...C];

function buildWindow() {
  const out = [];
  // ax：系数取遍有理数的小探针（去掉 0）。这样"正比例式求导"能算出 ℚ∖{0} 在小探针里的每一个数，
  // 引擎才认得出来（求导没有逆，它的像只能在视野里近似地算）
  for (const a of PROBE_SMALL) if (a.n !== 0) out.push(poly([ZERO, a]));
  for (const a of C) for (const b of C) out.push(poly([b, a])); // ax + b
  for (const a of C1) out.push(poly([ZERO, ZERO, a])); // ax²
  for (const a of C) for (const b of C) out.push(poly([ZERO, b, a])); // ax² + bx
  for (const a of C) for (const c of C) out.push(poly([c, ZERO, a])); // ax² + c
  for (const a of [ONE, neg(ONE)]) for (const b of ['-2', '-1', '1', '2'].map(q)) for (const c of [ONE, neg(ONE)]) out.push(poly([c, b, a])); // ±x² + bx ± 1
  for (let n = 3; n <= 5; n++) out.push(poly([...Array(n).fill(ZERO), ONE])); // x³ x⁴ x⁵
  return out;
}

export const WINDOW_P = buildWindow();

// 两两运算、封闭的结果大小超过它就丢掉。设得小是为了让封闭在 200ms 内算完
export const SIZE_CAP = 4;

// 小探针：近似卡组只比对这些。每一张都要是视野里两两运算、像常常能算出来的，
// 所以大小都不超过 SIZE_CAP
export const PROBES_SMALL_P = [
  // 单项式
  'p:1,0', 'p:1,0,0', 'p:1,0,0,0',
  // 正比例
  'p:-1,0', 'p:2,0', 'p:-2,0', 'p:1/2,0', 'p:-1/2,0', 'p:3,0', 'p:2/3,0',
  // 一次式
  'p:1,1', 'p:1,-1', 'p:-1,1', 'p:2,1', 'p:2,-2', 'p:-2,1/2', 'p:1,2', 'p:1,1/2', 'p:-1,-1',
  // 平方项
  'p:-1,0,0', 'p:2,0,0', 'p:1/2,0,0', 'p:-1/2,0,0',
  // 过原点的二次式
  'p:1,1,0', 'p:1,-1,0', 'p:2,1,0', 'p:1/2,-1,0', 'p:-1,2,0', 'p:1,-2,0',
  // 完全平方式
  'p:1,2,1', 'p:1,-2,1',
  // 其他二次式
  'p:1,1,1', 'p:1,0,-1', 'p:1,0,1', 'p:2,1,-1', 'p:-1,0,2', 'p:1/2,-1,1', 'p:1,-1,-2',
].map(parsePolyKey);

// 大探针：精确卡组逐一比对；再加上一些视野外的
export const PROBES_P = [
  ...PROBES_SMALL_P,
  ...[
    'p:1,0,0,0,0', 'p:1,0,0,0,0,0', 'p:1,0,0,0,0,0,0,0,0,0,0,0,0', 'p:3,0,0', 'p:4,0,0', 'p:1/4,0,0', 'p:1,1,1/4', 'p:7,0', 'p:1/7,0', 'p:-100,0', 'p:5,-3', 'p:1/3,7', 'p:100,1',
    'p:3,2,-7', 'p:1,0,100', 'p:-5,0,0', 'p:9,0,0', 'p:1/9,0,0', 'p:9,6,1', 'p:9,-12,4', 'p:4,4,1', 'p:1/9,2/3,1',
    'p:1,3,0', 'p:7,-1,0', 'p:1,1,0,0', 'p:1,0,-1,0', 'p:1,0,0,1', 'p:2,0,0,0', 'p:1,2,1,0', 'p:1,0,0,0,1', 'p:1,0,1,0,1',
  ].map(parsePolyKey),
];

// ───────────────────────── 类型注册 ─────────────────────────

function cmpP(a, b) {
  const da = degOf(a);
  const db = degOf(b);
  if (da !== db) return da - db;
  const sa = sizeP(a);
  const sb = sizeP(b);
  if (sa !== sb) return sa - sb;
  const ta = a.c.filter(x => x.n !== 0).length;
  const tb = b.c.filter(x => x.n !== 0).length;
  if (ta !== tb) return ta - tb;
  for (let i = da; i >= 0; i--) {
    const x = a.c[i];
    const y = b.c[i];
    const ax = { n: Math.abs(x.n), d: x.d };
    const ay = { n: Math.abs(y.n), d: y.d };
    const c = cmp(ax, ay);
    if (c !== 0) return c;
    if (x.n !== y.n) return x.n > y.n ? -1 : 1; // 正的排前面
  }
  return 0;
}

// 大小 = 次数 + 系数的最大 height。封闭、两两运算靠它限制增长
export function sizeP(v) {
  let h = 1;
  for (const a of v.c) {
    const t = height(a);
    if (t > h) h = t;
  }
  return v.c.length - 1 + h;
}

export function keyP(v) {
  let s = 'p:';
  for (let i = v.c.length - 1; i >= 0; i--) s += (i === v.c.length - 1 ? '' : ',') + rkey(v.c[i]);
  return s;
}

const MSG_DIV = '除以多项式会得到分式（比如 1/x）。分式不是多项式，这个游戏里还没有它。只能除以一个不为 0 的数。';

registerType({
  t: 'poly',
  name: '多项式',
  label: v => `${CN[degOf(v)] ?? degOf(v)}次多项式`,
  key: keyP,
  parseKey: parsePolyKey,
  fmt: v => fmtPoly(v.c),
  size: sizeP,
  cmp: cmpP,
  window: WINDOW_P,
  probes: PROBES_P,
  probesSmall: PROBES_SMALL_P,
  sizeCap: SIZE_CAP,
  bin(op, x, y) {
    const px = isP(x);
    const py = isP(y);
    if (!px && !py) return undefined;
    // 另一边既不是数也不是多项式：交给别的类型处理
    if (!(px || isR(x)) || !(py || isR(y))) return undefined;
    switch (op) {
      case 'add':
        return addP(x, y);
      case 'sub':
        return subP(x, y);
      case 'mul':
        return mulP(x, y);
      case 'div':
        if (py) return { err: MSG_DIV };
        if (y.n === 0) return { err: '不能除以 0。' };
        return scaleP(x, inv(y));
      case 'pow':
        if (py) return { err: `指数得是一个数。像 ${fmtV(x)} 的 ${fmtV(y)} 次方这样把 x 放在指数上，得到的不是多项式。` };
        if (!isInt(y)) return { err: `多项式只能做整数次方：${fmtV(x)} 的 ${fmtR(y)} 次方一般开不出来。` };
        if (y.n < 0) return { err: '多项式的负数次方会得到分式（比如 1/x），不是多项式。' };
        return powP(x, y.n);
      case 'mod':
        return { err: '多项式的带余除法这个游戏里先不做。' };
    }
    return undefined;
  },
  // 把多项式当函数用：x 是数就代入求值，x 是多项式就复合 p(q(x))
  call(v, x) {
    if (isR(x)) {
      let r = ZERO;
      for (let i = v.c.length - 1; i >= 0; i--) {
        r = mul(r, x);
        if (!isR(r)) return r;
        r = add(r, v.c[i]);
        if (!isR(r)) return r;
      }
      return r;
    }
    if (isP(x)) {
      if (degOf(v) * degOf(x) > MAX_DEG) return OVER;
      let r = ZERO;
      for (let i = v.c.length - 1; i >= 0; i--) {
        r = mulP(r, x);
        if (!isR(r) && !isP(r)) return r;
        r = addP(r, v.c[i]);
        if (!isR(r) && !isP(r)) return r;
      }
      return r;
    }
    return { err: '只能把数或多项式代入多项式。' };
  },
  // s 里的 x 全是输入（或者输入已经写成 □），代进去不会和多项式的 x 混淆，见上面 SLOT 的说明
  fmtCall: (v, s) => (s === 'x' ? fmtPoly(v.c) : fmtPoly(v.c, `(${s})`)),
  // 一次式 ax + b 当函数用时可以倒推：x = (y − b)/a
  invertFn(v) {
    if (degOf(v) !== 1) return null;
    const [b, a] = v.c;
    return aff(inv(a), neg(div(b, a)));
  },
  // 绑定的常量 c 是多项式，里面有多项式的 x，所以输入写成 □：乘以 x 是 "□ × x"，不是 "x × x"
  fmtBind(op, side, c, s) {
    const t = slotted(s);
    const ct = wrapS(fmtV(c));
    if (op === 'pow' && side === 'l') return t === SLOT ? `${ct}^${SLOT}` : `${ct}^(${t})`;
    const sym = BIN[op].sym;
    return side === 'r' ? `${wrapS(t)} ${sym} ${ct}` : `${ct} ${sym} ${wrapS(t)}`;
  },
});

// ───────────────────────── 求导与积分 ─────────────────────────

export function derive(x) {
  if (isR(x)) return ZERO;
  if (!isP(x)) return { err: '只有数和多项式能求导。' };
  return poly(x.c.slice(1).map((a, i) => mul(a, R(i + 1))));
}

export function integrate(x) {
  if (isR(x)) return poly([ZERO, x]);
  if (!isP(x)) return { err: '只有数和多项式能积分。' };
  if (degOf(x) + 1 > MAX_DEG) return OVER;
  return poly([ZERO, ...x.c.map((a, i) => mul(a, R(1, i + 1)))]);
}

registerNamed({
  id: 'D',
  name: '求导',
  fmt: s => (s === 'x' ? 'x′' : `(${s})′`),
  apply: derive,
  // 注意：这里故意不写 inverse。求导会丢掉常数项（x + 1 和 x 求导都是 1），所以它没有逆；
  // 只有积分有逆（先积分再求导一定回到原样）。
  desc: '每一项 a·xⁿ 变成 n·a·xⁿ⁻¹，常数项消失。数求导得到 0。',
});

registerNamed({
  id: 'INT',
  name: '积分',
  // 上限 x 是多项式的变量，所以输入写成 □，积分变量写成 t：∫₀ˣ □ dt（数 3 填进去是 ∫₀ˣ 3 dt = 3x）。
  // 前面的步骤里已经出现了多项式的 x 时（输入已经是 □），积分号里的 x 要改名成积分变量 t：
  // 先乘以 x 再积分是 ∫₀ˣ (□ × t) dt
  fmt: s => {
    const body = s.includes(SLOT) ? s.replace(LATIN_X, 't') : slotted(s);
    return `∫₀ˣ ${body === SLOT ? SLOT : `(${body})`} dt`;
  },
  apply: integrate,
  inverse: 'D',
  desc: '求导倒过来做：每一项 a·xⁿ 变成 a·xⁿ⁺¹/(n + 1)，常数项取 0（也就是从 0 积到 x）。数 c 积分得到 c·x。',
});

// ───────────────────────── 内容 ─────────────────────────

export const CHAPTER = {
  id: 6,
  title: '未知数',
  desc: '把一个还不知道的数写成 x。',
  intro:
    '到现在为止，每张卡都是一个确定的数。这一章多了一张特别的卡：x，一个还不知道是多少的数。把 x 和数加减乘起来，就得到多项式。多项式可以求导、可以积分，也可以把别的卡代进去算。',
  unlock: {
    when: 'd:Q',
    gives: ['c:p:1,0', 'u:D', 'u:INT'],
    note: '集齐有理数 ℚ 之后，你拿到了未知数 x、求导和积分。多项式也能当算子用，试试把 x 放在中间：先点合成台中间的空格，再点 x。',
  },
};

export const NAMED_UN = [
  { id: 'D', name: '求导', f: namedU('D') },
  { id: 'INT', name: '积分', f: namedU('INT') },
  { id: 'mulx', name: '乘以 x', f: bindU('mul', 'r', X) },
];

export const BIN_INFO = {};

const isSquareR = a => a.n > 0 && iroot(a.n, 2) !== null && iroot(a.d, 2) !== null;

export const CATALOG = [
  {
    id: 'Mono',
    short: 'xⁿ',
    name: '单项式',
    ch: 6,
    type: 'poly',
    preview: '{x, x², x³, x⁴, …}',
    struct: '集合',
    note: '对 × 封闭：x² × x³ = x⁵。但 x + x = 2x 不在里面，对 + 不封闭。',
    desc: 'x 自己乘自己，乘出来的一串。',
    hint: '从 x 出发，每一步都乘以 x。',
    has: v => isP(v) && eq(v.c[v.c.length - 1], ONE) && v.c.slice(0, -1).every(a => a.n === 0),
    recipes: [
      ['c:p:1,0', 'm:extend', 'u:mulx'],
      ['c:p:1,0', 'm:closure', 'b:mul'],
      ['c:p:1,0', 'b:pow', 'd:Np'],
    ],
  },
  {
    id: 'Prop',
    short: 'ax',
    name: '正比例式',
    ch: 6,
    type: 'poly',
    preview: '{x, −x, 2x, x/2, …}',
    struct: '集合',
    note: '对 + 不封闭：x + (−x) = 0 是一个数，不是多项式。所以不是群。',
    desc: '一个不为 0 的数乘以 x。',
    hint: '把非零有理数积分，每个数 a 都变成 ax。',
    has: v => isP(v) && degOf(v) === 1 && v.c[0].n === 0,
    recipes: [
      ['d:Qnz', 'u:INT', null],
      ['d:Qnz', 'b:mul', 'c:p:1,0'],
      ['c:p:1,0', 'b:mul', 'd:Qnz'],
      ['d:Sq2', 'u:D', null],
    ],
  },
  {
    id: 'Qnz',
    short: 'ℚ∖{0}',
    name: '非零有理数',
    ch: 6,
    type: 'q',
    preview: '{…, −1, −1/2, 1/2, 1, 2, …}',
    struct: '群',
    groupOp: '×',
    note: '(ℚ∖{0}, ×) 是群：非零数相乘还是非零数，1 是单位元，a/b 的逆元是 b/a。把 0 去掉正是为了让每个数都有倒数。',
    desc: '有理数去掉 0。它是正比例式求导的结果：ax 求导得到 a。',
    hint: '把正比例式里的每一张都求导；或者让 ℚ 里的每个数都取倒数。',
    has: x => isR(x) && x.n !== 0,
    recipes: [
      ['d:Prop', 'u:D', null],
      ['d:Q', 'u:recip', null],
      ['d:Qp', 'b:mul', 'd:Sign'],
      ['d:L1', 'u:D', null],
    ],
  },
  {
    id: 'L1',
    short: 'ax + b',
    name: '一次式',
    ch: 6,
    type: 'poly',
    preview: '{x, x + 1, 2x − 1, x/2 + 3, …}',
    struct: '集合',
    note: '一次式相加可能变成数：(x + 1) + (1 − x) = 2。把所有的数也算进来，(ℚ[x]₁, +) 才是群。',
    desc: 'ax + b，其中 a 不是 0。画出来是一条不水平的直线。',
    hint: '正比例式加上任何一个数。',
    has: v => isP(v) && degOf(v) === 1,
    recipes: [
      ['d:Prop', 'b:add', 'd:Q'],
      ['d:Q', 'b:add', 'd:Prop'],
      ['d:Prop', 'b:sub', 'd:Q'],
      ['d:Root0Q', 'u:D', null],
    ],
  },
  {
    id: 'Sq2',
    short: 'ax²',
    name: '平方项',
    ch: 6,
    type: 'poly',
    preview: '{x², −x², 2x², x²/2, …}',
    struct: '集合',
    note: '对 × 不封闭：x² × x² = x⁴。对 + 也不封闭：x² + (−x²) = 0。',
    desc: '一个不为 0 的数乘以 x²。',
    hint: '两个正比例式相乘；或者把正比例式积分。',
    has: v => isP(v) && degOf(v) === 2 && v.c[0].n === 0 && v.c[1].n === 0,
    recipes: [
      ['d:Prop', 'u:INT', null],
      ['d:Prop', 'b:mul', 'd:Prop'],
      ['d:Prop', 'b:mul', 'c:p:1,0'],
      ['d:Qnz', 'b:mul', 'c:p:1,0,0'],
    ],
  },
  {
    id: 'Root0Q',
    short: 'ax² + bx',
    name: '过原点的二次式',
    ch: 6,
    type: 'poly',
    preview: '{x², x² + x, 2x² − x, …}',
    struct: '集合',
    note: '常数项是 0，所以代入 x = 0 一定得到 0：这条抛物线经过原点。相加可能变成一次式，不是群。',
    desc: '没有常数项的二次式。它是一次式的积分。',
    hint: '把每个一次式都积分；或者让每个一次式都乘以 x。',
    has: v => isP(v) && degOf(v) === 2 && v.c[0].n === 0,
    recipes: [
      ['d:L1', 'u:INT', null],
      ['c:p:1,0', 'b:mul', 'd:L1'],
      ['d:L1', 'b:mul', 'c:p:1,0'],
      ['d:L1', 'b:mul', 'd:Prop'],
    ],
  },
  {
    id: 'PerfSq',
    short: '(ax + b)²',
    name: '完全平方式',
    ch: 6,
    type: 'poly',
    preview: '{x², x² + 2x + 1, 4x² − 4x + 1, …}',
    struct: '集合',
    note: '两个完全平方式相加一般不是完全平方式：x² + (x + 1)² = 2x² + 2x + 1。不是群。',
    desc: '一次式的平方。展开后 x² 的系数是一个数的平方，而且 b² = 4ac。',
    hint: '让每个一次式都做「平方」。多项式也能当算子用，试试把 x² 放在中间：先点合成台中间的空格，再点 x²。',
    has: v => {
      if (!isP(v) || degOf(v) !== 2) return false;
      const [c, b, a] = v.c;
      if (!isSquareR(a)) return false;
      // b² = 4ac。系数很大时 b²、4ac 会超出有理数的上限（mul 返回 OVER，再交给 eq 就崩溃），
      // 所以交叉相乘后用 BigInt 精确比较：b.n²·a.d·c.d = 4·a.n·c.n·b.d²。不会溢出，总能判断
      const B = BigInt;
      return B(b.n) * B(b.n) * B(a.d) * B(c.d) === 4n * B(a.n) * B(c.n) * B(b.d) * B(b.d);
    },
    recipes: [
      ['d:L1', 'u:sq', null],
      ['d:L1', 'c:p:1,0,0', null],
      ['d:L1', 'b:pow', 'c:2'],
    ],
  },
  {
    id: 'Q2',
    short: 'ax² + bx + c',
    name: '二次式',
    ch: 6,
    type: 'poly',
    preview: '{x², x² + 1, x² + x + 1, 2x² − x, …}',
    struct: '集合',
    note: '二次式相加可能变成一次式甚至数：x² + (1 − x²) = 1。把次数更低的都算进来，(ℚ[x]₂, +) 才是群。',
    desc: 'ax² + bx + c，其中 a 不是 0。画出来是一条抛物线。',
    hint: '过原点的二次式加上任何一个数，抛物线就上下平移了。',
    has: v => isP(v) && degOf(v) === 2,
    recipes: [
      ['d:Root0Q', 'b:add', 'd:Q'],
      ['d:Q', 'b:add', 'd:Root0Q'],
      ['d:Root0Q', 'b:sub', 'd:Q'],
    ],
  },
];

export const QUESTS = [
  {
    id: 'p1',
    ch: 6,
    title: '未知数登场',
    text: '左边放 x，中间放加法，右边放 1，合成 x + 1。',
    done: has => has('c:p:1,1'),
  },
  {
    id: 'p2',
    ch: 6,
    title: '多项式当算子',
    text: '多项式可以当算子用：先点合成台中间的空格，再点 x + 1，把它放在中间；再点一次 x + 1，放在旁边当输入，合成。把 x + 1 代入 x + 1，得到 x + 2。再试试中间放 x：把任何多项式代入 x，得到的还是它自己。',
    // 只认 x + 2：它是照着任务做出来的。x² 用乘法就能做出来，不能说明会把多项式当算子用
    done: has => has('c:p:1,2'),
  },
  {
    id: 'p3',
    ch: 6,
    title: '集齐未知数篇',
    text: '打开「图鉴」看第 6 章。先把 x 反复乘以 x，再想想求导和积分把哪些卡组连在一起。',
    done: has => CATALOG.every(c => has(`d:${c.id}`)),
  },
];

// 从"集齐初等篇 + 本章赠卡（x、求导、积分）"出发，集齐本章所有卡组
export const WALKTHROUGH = [
  [null, 'b:mul', 'c:p:1,0', 'u:bind(mul,r,p:1,0)'],
  ['c:p:1,0', 'm:extend', 'u:bind(mul,r,p:1,0)', 'd:Mono'],
  ['d:Q', 'u:pow(-1)', null, 'd:Qnz'],
  ['d:Qnz', 'u:named(INT)', null, 'd:Prop'],
  ['d:Prop', 'b:add', 'd:Q', 'd:L1'],
  ['d:Prop', 'u:named(INT)', null, 'd:Sq2'],
  ['d:L1', 'u:named(INT)', null, 'd:Root0Q'],
  ['d:L1', 'u:pow(2)', null, 'd:PerfSq'],
  ['d:Root0Q', 'b:add', 'd:Q', 'd:Q2'],
  ['d:Prop', 'u:named(D)', null, 'd:Qnz'],
];
