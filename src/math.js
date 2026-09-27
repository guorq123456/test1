// 算子工坊的数学核心：有理数、算子、卡组。
// 这里只有纯计算，不碰页面，方便用 node --test 直接测试。

// ───────────────────────── 有理数 ─────────────────────────

// 分子、分母的上限。超过它的数算作"太大"，游戏里造不出来。
// 两个不超过 1e7 的数相乘最多 1e14，仍在 JS 能精确表示的整数范围内。
export const LIMIT = 1e7;

// 计算溢出时返回的标记（区别于"没有定义"时返回的 null）
export const OVER = Object.freeze({ over: true });

export function gcd(a, b) {
  a = Math.abs(a);
  b = Math.abs(b);
  while (b) {
    const t = a % b;
    a = b;
    b = t;
  }
  return a;
}

export function R(n, d = 1) {
  if (d === 0 || !Number.isFinite(n) || !Number.isFinite(d)) return null;
  if (d < 0) {
    n = -n;
    d = -d;
  }
  const g = gcd(n, d);
  if (g > 1) {
    n /= g;
    d /= g;
  }
  if (Math.abs(n) > LIMIT || d > LIMIT) return OVER;
  return n === 0 ? { n: 0, d: 1 } : { n, d };
}

export const isR = v => v !== null && typeof v === 'object' && typeof v.n === 'number';
export const ZERO = R(0);
export const ONE = R(1);
export const NEG1 = R(-1);
export const TWO = R(2);

export const eq = (x, y) => x.n === y.n && x.d === y.d;
export const eqR = (x, y) => isR(x) && isR(y) && eq(x, y);
export const cmp = (x, y) => x.n * y.d - y.n * x.d;
export const isInt = x => x.d === 1;
export const height = x => Math.max(Math.abs(x.n), x.d);
export const toNum = x => x.n / x.d;
export const rkey = x => (x.d === 1 ? `${x.n}` : `${x.n}/${x.d}`);

export function parseKey(s) {
  const [a, b] = String(s).split('/');
  return R(Number(a), b === undefined ? 1 : Number(b));
}

export function fmtR(x) {
  const body = x.d === 1 ? `${Math.abs(x.n)}` : `${Math.abs(x.n)}/${x.d}`;
  return x.n < 0 ? `−${body}` : body;
}

export const add = (x, y) => R(x.n * y.d + y.n * x.d, x.d * y.d);
export const sub = (x, y) => R(x.n * y.d - y.n * x.d, x.d * y.d);
export const mul = (x, y) => R(x.n * y.n, x.d * y.d);
export const div = (x, y) => (y.n === 0 ? null : R(x.n * y.d, x.d * y.n));
export const neg = x => R(-x.n, x.d);
export const inv = x => (x.n === 0 ? null : R(x.d, x.n));

// 整数次幂。0⁰ 和 0 的负数次方没有定义。
export function ipow(x, k) {
  if (x.n === 0) return k > 0 ? ZERO : null;
  if (k === 0) return ONE;
  if (k < 0) return ipow(inv(x), -k);
  if (height(x) === 1) return x.n < 0 && k % 2 === 1 ? NEG1 : ONE;
  if (k * Math.log10(height(x)) > 7.5) return OVER;
  let r = ONE;
  for (let i = 0; i < k; i++) {
    r = mul(r, x);
    if (!isR(r)) return r;
  }
  return r;
}

// 整数 n 的 q 次方根（必须恰好是整数，否则返回 null）
function iroot(n, q) {
  if (n < 0) {
    if (q % 2 === 0) return null;
    const r = iroot(-n, q);
    return r === null ? null : -r;
  }
  const r = Math.round(n ** (1 / q));
  for (const c of [r - 1, r, r + 1]) if (c >= 0 && c ** q === n) return c;
  return null;
}

// x 的 e 次方，e 可以是分数。结果不是有理数（比如 √2）时返回 null。
export function rpow(x, e) {
  if (!isR(x) || !isR(e)) return null;
  if (e.d === 1) return ipow(x, e.n);
  if (e.d > 12) return null;
  const rn = iroot(x.n, e.d);
  const rd = iroot(x.d, e.d);
  if (rn === null || rd === null) return null;
  return ipow(R(rn, rd), e.n);
}

// 以 c 为底 y 的对数（结果必须是分母不超过 12 的有理数）
export function rlog(c, y) {
  if (c.n <= 0 || eq(c, ONE) || y.n <= 0) return null;
  const est = Math.log(toNum(y)) / Math.log(toNum(c));
  if (!Number.isFinite(est) || Math.abs(est) > 64) return null;
  for (let q = 1; q <= 12; q++) {
    const e = R(Math.round(est * q), q);
    if (!isR(e)) continue;
    const v = rpow(c, e);
    if (eqR(v, y)) return e;
  }
  return null;
}

function uniqR(xs) {
  const m = new Map();
  for (const x of xs) if (isR(x)) m.set(rkey(x), x);
  return [...m.values()];
}

// ───────────────────────── 一元算子 ─────────────────────────
// aff: a·x + b    pow: xⁿ    exp: cˣ    log: log_c x    chain: 依次做若干个

export const aff = (a, b) => ({ t: 'aff', a, b });
export const ID = aff(ONE, ZERO);
export const isConst = f => f.t === 'aff' && f.a.n === 0;
export const isId = f => f.t === 'aff' && eq(f.a, ONE) && f.b.n === 0;

export function powU(n) {
  if (n.n === 0) return aff(ZERO, ONE);
  if (eq(n, ONE)) return ID;
  return { t: 'pow', n };
}

export function expU(c) {
  if (c.n === 0) return null;
  if (eq(c, ONE)) return aff(ZERO, ONE);
  return { t: 'exp', c };
}

export function logU(c) {
  if (c.n <= 0 || eq(c, ONE)) return null;
  return { t: 'log', c };
}

export function applyU(f, x) {
  if (!isR(x)) return null;
  switch (f.t) {
    case 'aff': {
      const ax = mul(f.a, x);
      return isR(ax) ? add(ax, f.b) : ax;
    }
    case 'pow':
      return rpow(x, f.n);
    case 'exp':
      return rpow(f.c, x);
    case 'log':
      return rlog(f.c, x);
    case 'chain': {
      let v = x;
      for (const g of f.fs) {
        v = applyU(g, v);
        if (!isR(v)) return v;
      }
      return v;
    }
  }
  return null;
}

export function ukey(f) {
  switch (f.t) {
    case 'aff':
      return `aff(${rkey(f.a)},${rkey(f.b)})`;
    case 'pow':
      return `pow(${rkey(f.n)})`;
    case 'exp':
      return `exp(${rkey(f.c)})`;
    case 'log':
      return `log(${rkey(f.c)})`;
    case 'chain':
      return `chain(${f.fs.map(ukey).join(';')})`;
  }
  return '?';
}

// 尝试把"先 f 后 g"化简成一个算子；化简不了返回 undefined
function merge(f, g) {
  if (isId(f)) return g;
  if (isId(g)) return f;
  if (isConst(g)) return g;
  if (isConst(f)) {
    const v = applyU(g, f.b);
    return isR(v) ? aff(ZERO, v) : undefined;
  }
  if (f.t === 'aff' && g.t === 'aff') {
    const a = mul(g.a, f.a);
    const ab = mul(g.a, f.b);
    if (!isR(a) || !isR(ab)) return undefined;
    const b = add(ab, g.b);
    return isR(b) ? aff(a, b) : undefined;
  }
  if (f.t === 'pow' && g.t === 'pow' && isInt(f.n) && isInt(g.n)) {
    const n = mul(f.n, g.n);
    return isR(n) ? powU(n) : undefined;
  }
  if (f.t === 'exp' && g.t === 'log' && eq(f.c, g.c)) return ID;
  if (f.t === 'log' && g.t === 'exp' && eq(f.c, g.c)) return ID;
  return undefined;
}

// 复合：先做 f，再做 g
export function compose(f, g) {
  const parts = [...(f.t === 'chain' ? f.fs : [f]), ...(g.t === 'chain' ? g.fs : [g])];
  const out = [];
  for (const h of parts) {
    out.push(h);
    while (out.length >= 2) {
      const m = merge(out[out.length - 2], out[out.length - 1]);
      if (m === undefined) break;
      out.splice(-2, 2, m);
    }
  }
  const fs = out.filter(h => !isId(h));
  if (fs.length === 0) return ID;
  return fs.length === 1 ? fs[0] : { t: 'chain', fs };
}

// 逆算子；没有逆时返回 null
export function invertU(f) {
  switch (f.t) {
    case 'aff': {
      if (f.a.n === 0) return null;
      const ia = inv(f.a);
      const ib = mul(neg(f.b), ia);
      return isR(ia) && isR(ib) ? aff(ia, ib) : null;
    }
    case 'pow': {
      const m = inv(f.n);
      return isR(m) && m.d <= 12 ? powU(m) : null;
    }
    case 'exp':
      return f.c.n > 0 ? logU(f.c) : null;
    case 'log':
      return expU(f.c);
    case 'chain': {
      let r = ID;
      for (let i = f.fs.length - 1; i >= 0; i--) {
        const g = invertU(f.fs[i]);
        if (!g) return null;
        r = compose(r, g);
      }
      return r;
    }
  }
  return null;
}

// y 的原像：{ list } 表示有限个；{ pred } 表示无穷多个，用谓词描述。
// 如果倒推时数字超出了上限，结果里会带 unknown: true（原像可能存在，只是游戏里表示不了）。
export function preU(f, y) {
  const verify = xs => {
    const list = uniqR(xs).filter(x => eqR(applyU(f, x), y));
    return { list, unknown: !list.length && xs.some(x => x === OVER) };
  };
  switch (f.t) {
    case 'aff': {
      if (f.a.n === 0) return eq(f.b, y) ? { pred: () => true } : { list: [] };
      const t = sub(y, f.b);
      return verify(isR(t) ? [div(t, f.a)] : [t]);
    }
    case 'pow': {
      const r = rpow(y, inv(f.n));
      return verify(isR(r) ? [r, neg(r)] : [r]);
    }
    case 'exp': {
      if (eq(f.c, NEG1)) return { pred: x => eqR(applyU(f, x), y) };
      if (f.c.n < 0) {
        if (y.n === 0) return { list: [] };
        const k = Math.round(Math.log(Math.abs(toNum(y))) / Math.log(Math.abs(toNum(f.c))));
        return verify(Number.isFinite(k) ? [R(k)] : []);
      }
      const e = rlog(f.c, y);
      return verify(e ? [e] : []);
    }
    case 'log':
      return verify([rpow(f.c, y)]);
    case 'chain': {
      let ys = [y];
      let unknown = false;
      for (let i = f.fs.length - 1; i >= 0; i--) {
        const next = [];
        for (const v of ys) {
          const p = preU(f.fs[i], v);
          if (p.pred) return { pred: x => eqR(applyU(f, x), y) };
          if (p.unknown) unknown = true;
          next.push(...p.list);
        }
        ys = uniqR(next);
        if (!ys.length) return { list: [], unknown };
      }
      const r = verify(ys);
      return { list: r.list, unknown: unknown && !r.list.length };
    }
  }
  return { list: [] };
}

// ───────────────────────── 公式显示 ─────────────────────────

const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹', '-': '⁻' };
const SUB = { 0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄', 5: '₅', 6: '₆', 7: '₇', 8: '₈', 9: '₉', '-': '₋' };
const sup = n => [...String(n)].map(ch => SUP[ch] ?? ch).join('');
const subscript = n => [...String(n)].map(ch => SUB[ch] ?? ch).join('');

const isAtom = s => s === 'x';
const isTight = s => !/\s/.test(s);
// 放在分数线前面时需要括号的情况
const tightDiv = s => (!isTight(s) || s.includes('/') ? `(${s})` : s);

// 系数 k（字符串）乘以式子 s
function scale(k, s) {
  if (s.startsWith('1/')) return `${k}/${s.slice(2)}`;
  if (!isTight(s)) return `${k}(${s})`;
  if (/^[0-9(−]/.test(s)) return `${k}·${s}`;
  return `${k}${s}`;
}

function fmtAff(a, b, s) {
  if (a.n === 0) return fmtR(b);
  if (eq(a, NEG1)) {
    const t = isTight(s) ? s : `(${s})`;
    return b.n === 0 ? `−${t}` : `${fmtR(b)} − ${t}`;
  }
  let lead;
  if (eq(a, ONE)) lead = s;
  else if (a.d === 1) lead = scale(fmtR(a), s);
  else {
    const top = a.n === 1 ? tightDiv(s) : a.n === -1 ? `−${tightDiv(s)}` : scale(fmtR(R(a.n)), s);
    lead = `${top}/${a.d}`;
  }
  if (b.n === 0) return lead;
  return b.n > 0 ? `${lead} + ${fmtR(b)}` : `${lead} − ${fmtR(neg(b))}`;
}

function fmtPow(n, s) {
  const base = isAtom(s) ? s : `(${s})`;
  if (isInt(n)) {
    if (n.n > 0) return `${base}${sup(n.n)}`;
    if (n.n === -1) return `1/${tightDiv(s)}`;
    return `1/${base}${sup(-n.n)}`;
  }
  const roots = { 2: '√', 3: '∛', 4: '∜' };
  if (Math.abs(n.n) === 1 && roots[n.d]) {
    const r = `${roots[n.d]}${base}`;
    return n.n > 0 ? r : `1/${r}`;
  }
  return `${base}^(${fmtR(n)})`;
}

function fmtExp(c, s) {
  const base = c.n > 0 && c.d === 1 ? fmtR(c) : `(${fmtR(c)})`;
  return isAtom(s) ? `${base}ˣ` : `${base}^(${s})`;
}

function fmtLog(c, s) {
  const base = c.d === 1 ? `log${subscript(c.n)}` : `log_(${fmtR(c)})`;
  return isAtom(s) ? `${base}x` : `${base}(${s})`;
}

// 一元算子的公式，比如 "x + 1"、"(x + 1)²"、"3/x"
export function fmtU(f, s = 'x') {
  switch (f.t) {
    case 'aff':
      return fmtAff(f.a, f.b, s);
    case 'pow':
      return fmtPow(f.n, s);
    case 'exp':
      return fmtExp(f.c, s);
    case 'log':
      return fmtLog(f.c, s);
    case 'chain':
      return f.fs.reduce((acc, g) => fmtU(g, acc), s);
  }
  return '?';
}

export function serU(f) {
  switch (f.t) {
    case 'aff':
      return { t: 'aff', a: rkey(f.a), b: rkey(f.b) };
    case 'pow':
      return { t: 'pow', n: rkey(f.n) };
    case 'exp':
      return { t: 'exp', c: rkey(f.c) };
    case 'log':
      return { t: 'log', c: rkey(f.c) };
    case 'chain':
      return { t: 'chain', fs: f.fs.map(serU) };
  }
  return null;
}

export function parseU(o) {
  if (!o) return null;
  const k = s => {
    const x = parseKey(s);
    return isR(x) ? x : null;
  };
  switch (o.t) {
    case 'aff': {
      const a = k(o.a);
      const b = k(o.b);
      return a && b ? aff(a, b) : null;
    }
    case 'pow': {
      const n = k(o.n);
      return n ? powU(n) : null;
    }
    case 'exp': {
      const c = k(o.c);
      return c ? expU(c) : null;
    }
    case 'log': {
      const c = k(o.c);
      return c ? logU(c) : null;
    }
    case 'chain': {
      const fs = (o.fs || []).map(parseU);
      return fs.length >= 2 && fs.every(Boolean) ? { t: 'chain', fs } : null;
    }
  }
  return null;
}

// ───────────────────────── 二元算子 ─────────────────────────

export const BIN = {
  add: { id: 'add', name: '加法', sym: '+', comm: true, fn: add },
  sub: { id: 'sub', name: '减法', sym: '−', comm: false, fn: sub },
  mul: { id: 'mul', name: '乘法', sym: '×', comm: true, fn: mul },
  div: { id: 'div', name: '除法', sym: '÷', comm: false, fn: div },
  pow: { id: 'pow', name: '乘方', sym: '^', comm: false, fn: rpow },
};

export const MSG_OVER = '数字太大了（分子或分母超过了一千万），换小一点的数试试。';

// 两张单卡做二元运算
export function binCard(b, x, y) {
  const v = b.fn(x, y);
  if (isR(v)) return { v };
  if (v === OVER) return { err: MSG_OVER };
  if (b.id === 'div') return { err: '不能除以 0。' };
  if (b.id === 'pow') {
    if (x.n === 0) return { err: '0 的 0 次方、0 的负数次方都没有定义。' };
    return { err: `${fmtR(x)} 的 ${fmtR(y)} 次方不是有理数，初等篇里还造不出来。` };
  }
  return { err: '这一步算不出结果。' };
}

// 右边绑定一个数：x ∘ c
export function bindRight(b, c) {
  switch (b.id) {
    case 'add':
      return { f: aff(ONE, c) };
    case 'sub':
      return { f: aff(ONE, neg(c)) };
    case 'mul':
      return { f: aff(c, ZERO) };
    case 'div':
      return c.n === 0 ? { err: '不能除以 0，所以 x ÷ 0 没有意义。' } : { f: aff(inv(c), ZERO) };
    case 'pow':
      return c.d > 12 ? { err: '指数的分母太大了。' } : { f: powU(c) };
  }
  return { err: '这个算子不能绑定数字。' };
}

// 左边绑定一个数：c ∘ x
export function bindLeft(c, b) {
  switch (b.id) {
    case 'add':
      return { f: aff(ONE, c) };
    case 'sub':
      return { f: aff(NEG1, c) };
    case 'mul':
      return { f: aff(c, ZERO) };
    case 'div':
      return { f: c.n === 0 ? aff(ZERO, ZERO) : compose(powU(NEG1), aff(c, ZERO)) };
    case 'pow':
      return c.n === 0 ? { err: '0ˣ 在初等篇里先不讨论，换一个底数吧。' } : { f: expU(c) };
  }
  return { err: '这个算子不能绑定数字。' };
}

// ───────────────────────── 卡组 ─────────────────────────
// 卡组用"成员判断"来表示：has(x) 告诉你 x 在不在里面。
// 像"封闭"这种没法精确推算的操作，会在一个小窗口里真的算一遍，再和图鉴里的卡组比对。

export const WIN_H = 20; // 窗口：分子、分母都不超过 20 的有理数

function rationalsUpTo(h, maxD = h) {
  const out = [];
  for (let d = 1; d <= maxD; d++) for (let n = -h; n <= h; n++) if (gcd(n, d) === 1) out.push(R(n, d));
  return out.sort((x, y) => height(x) - height(y) || cmp(x, y));
}

export const WINDOW = rationalsUpTo(WIN_H);

// 探针：用来判断两个卡组是否一样
export const PROBE_SMALL = rationalsUpTo(12, 6);
export const PROBE_LARGE = [
  '13', '16', '17', '24', '25', '27', '31', '32', '36', '49', '63', '64', '81', '97', '100', '127', '128',
  '243', '255', '256', '1000', '1024', '4096', '65536', '-13', '-16', '-25', '-32', '-64', '-97', '-100',
  '-128', '-1000', '-1024', '1/7', '1/8', '1/9', '1/10', '1/12', '1/16', '1/25', '1/32', '1/64', '1/97',
  '1/100', '1/128', '1/1024', '-1/7', '-1/8', '-1/16', '-1/97', '97/2', '13/7', '2/97', '3/64', '5/12',
  '7/8', '25/4', '1024/3', '-7/8', '-97/2', '9/16', '49/100',
].map(parseKey);
export const PROBES = [...PROBE_SMALL, ...PROBE_LARGE];

// 展示卡组内容时从这里挑"最简单"的几个数
const DISPLAY_POOL = (() => {
  const xs = [...WINDOW];
  for (let n = -400; n <= 400; n++) xs.push(R(n));
  for (let k = 0; k <= 16; k++) xs.push(R(2 ** k), R(1, 2 ** k));
  return uniqR(xs).sort((x, y) => height(x) - height(y) || cmp(x, y));
})();

// has(x) 返回 true / false，或者 null（表示"超出游戏的数字范围，判断不了"）
export function mkDeck(kind, has, extra = {}) {
  const cache = new Map();
  return {
    kind,
    approx: false,
    ...extra,
    has(x) {
      if (!isR(x)) return false;
      const k = rkey(x);
      if (cache.has(k)) return cache.get(k);
      const r = has(x);
      const v = r === null ? null : !!r;
      cache.set(k, v);
      return v;
    },
  };
}

// 三值逻辑的"或"和"且"：null 表示不知道
const or3 = (a, b) => (a === true || b === true ? true : a === null || b === null ? null : false);
const and3 = (a, b) => (a === false || b === false ? false : a === null || b === null ? null : true);

export function finiteDeck(xs, name) {
  const list = uniqR(xs).sort(cmp);
  const keys = new Set(list.map(rkey));
  return mkDeck('finite', x => keys.has(rkey(x)), { list, name });
}

function approxDeck(map, name) {
  return mkDeck('approx', x => map.has(rkey(x)), { name, approx: true, elems: [...map.values()] });
}

// 对卡组里的每张卡做一元算子 f
export function imageDeck(D, f, name) {
  if (D.list) return finiteDeck(D.list.map(x => applyU(f, x)), name);
  return mkDeck(
    'image',
    y => {
      const p = preU(f, y);
      if (p.pred) return WINDOW.some(x => p.pred(x) && D.has(x) === true);
      const hits = p.list.map(x => D.has(x));
      if (hits.includes(true)) return true;
      return p.unknown || hits.includes(null) ? null : false;
    },
    { name, approx: D.approx },
  );
}

export function unionDeck(A, B, name) {
  if (A.list && B.list) return finiteDeck([...A.list, ...B.list], name);
  return mkDeck('union', x => or3(A.has(x), B.has(x)), { name, approx: A.approx || B.approx });
}

export function interDeck(A, B, name) {
  if (A.list) return finiteDeck(A.list.filter(x => B.has(x) === true), name);
  if (B.list) return finiteDeck(B.list.filter(x => A.has(x) === true), name);
  return mkDeck('inter', x => and3(A.has(x), B.has(x)), { name, approx: A.approx || B.approx });
}

// a·x + b 的轨道 {c, f(c), f(f(c)), …} 的精确成员判断
function affOrbitHas(c, f, y) {
  const { a, b } = f;
  if (eq(a, ONE)) {
    const t = sub(y, c);
    if (!isR(t)) return false;
    const k = div(t, b);
    return isR(k) && isInt(k) && k.n >= 0;
  }
  // 不动点 p = b / (1 − a)，于是 y − p = aᵏ · (c − p)
  const oneMinusA = sub(ONE, a);
  if (!isR(oneMinusA)) return false;
  const p = div(b, oneMinusA);
  if (!isR(p)) return false;
  const u = sub(y, p);
  const w = sub(c, p);
  if (!isR(u) || !isR(w) || w.n === 0) return false;
  const r = div(u, w);
  if (!isR(r)) return false;
  if (eq(r, ONE)) return true;
  const la = Math.log(Math.abs(toNum(a)));
  if (la === 0 || r.n === 0) return false;
  const k = Math.round(Math.log(Math.abs(toNum(r))) / la);
  if (!(k >= 0) || k > 200) return false;
  return eqR(ipow(a, k), r);
}

const ORBIT_STEPS = 400;

// 延展：从 c 出发反复做 f
export function orbitDeck(c, f, name) {
  const seq = [c];
  const seen = new Set([rkey(c)]);
  let x = c;
  let open = true;
  let overflow = false;
  for (let i = 0; i < ORBIT_STEPS; i++) {
    const y = applyU(f, x);
    if (!isR(y)) {
      open = false;
      overflow = y === OVER;
      break;
    }
    const k = rkey(y);
    if (seen.has(k)) {
      open = false;
      break;
    }
    seen.add(k);
    seq.push(y);
    x = y;
  }
  // 走进了循环，或者走到没有定义的地方停下：有限卡组
  if (!open && !overflow) return finiteDeck(seq, name);
  const extra = { name, seq: seq.slice(0, 6) };
  if (f.t === 'aff') return mkDeck('orbit', y => affOrbitHas(c, f, y), extra);
  // 其他算子：记下走过的每一步。走满步数还没停就标成近似。
  return mkDeck('orbit', y => seen.has(rkey(y)), { ...extra, approx: open });
}

const OP_BUDGET = 1_500_000;

// 封闭：从 D 出发，用 b 反复组合（在窗口里算）
export function closureDeck(D, b, name) {
  const fin = !!D.list;
  const seeds = fin ? D.list : WINDOW.filter(x => D.has(x));
  const hmax = fin ? Math.min(2000, Math.max(WIN_H, 2 * Math.max(1, ...seeds.map(height)))) : WIN_H;
  const all = new Map(seeds.map(x => [rkey(x), x]));
  let frontier = [...all.values()];
  let dropped = false;
  let ops = 0;
  let rounds = 0;
  let stop = false;
  while (frontier.length && rounds < 12 && !stop) {
    rounds++;
    const cur = [...all.values()];
    const fresh = [];
    const tryAdd = z => {
      if (!isR(z)) {
        if (z === OVER) dropped = true;
        return;
      }
      if (height(z) > hmax) {
        dropped = true;
        return;
      }
      const k = rkey(z);
      if (!all.has(k)) {
        all.set(k, z);
        fresh.push(z);
      }
    };
    for (const x of frontier) {
      for (const y of cur) {
        tryAdd(b.fn(x, y));
        if (!b.comm) tryAdd(b.fn(y, x));
      }
      ops += cur.length * 2;
      if (ops > OP_BUDGET || all.size > 4000) {
        dropped = true;
        stop = true;
        break;
      }
    }
    frontier = fresh;
  }
  if (frontier.length) dropped = true;
  if (fin && !dropped) return finiteDeck([...all.values()], name);
  return approxDeck(all, name);
}

// 两个卡组两两运算：{a ∘ b | a ∈ A, b ∈ B}
export function pairwiseDeck(A, b, B, name) {
  const fin = !!(A.list && B.list);
  const sa = A.list ?? WINDOW.filter(x => A.has(x));
  const sb = B.list ?? WINDOW.filter(x => B.has(x));
  const out = new Map();
  for (const x of sa) {
    for (const y of sb) {
      const z = b.fn(x, y);
      if (!isR(z)) continue;
      if (!fin && height(z) > WIN_H) continue;
      out.set(rkey(z), z);
    }
  }
  if (fin) return finiteDeck([...out.values()], name);
  return approxDeck(out, name);
}

export function sigOf(D, probes = PROBES) {
  return probes.map(x => ({ true: '1', false: '0', null: '?' })[D.has(x)]).join('');
}

// 卡组内容预览，比如 "{0, 2, 4, 6, 8, …}"
export function previewDeck(D, max = 6) {
  if (D.list) {
    const xs = D.list;
    if (!xs.length) return '{ }';
    if (xs.length <= max + 1) return `{${xs.map(fmtR).join(', ')}}`;
    return `{${xs.slice(0, max).map(fmtR).join(', ')}, …}`;
  }
  if (D.seq && D.seq.length >= 2) return `{${D.seq.slice(0, 5).map(fmtR).join(', ')}, …}`;
  const members = [];
  for (const x of DISPLAY_POOL) {
    if (D.has(x)) {
      members.push(x);
      if (members.length >= max) break;
    }
  }
  if (!members.length) return D.approx ? '{ …（范围外） }' : '{ }';
  members.sort(cmp);
  const lo = members[0];
  const hi = members[members.length - 1];
  const moreLo = DISPLAY_POOL.some(x => cmp(x, lo) < 0 && D.has(x));
  const moreHi = DISPLAY_POOL.some(x => cmp(x, hi) > 0 && D.has(x));
  return `{${moreLo ? '…, ' : ''}${members.map(fmtR).join(', ')}${moreHi ? ', …' : ''}}`;
}

// 简单的字符串哈希，用来给未命名卡组起编号
export function hash(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}
