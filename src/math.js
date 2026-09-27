// 有理数核心。没有任何依赖，其他模块都建立在它之上。

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

export const isR = v => v !== null && typeof v === 'object' && typeof v.n === 'number' && typeof v.d === 'number';
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

export const Q_KEY_RE = /^-?\d+(\/\d+)?$/;

export function parseQKey(s) {
  if (typeof s !== 'string' || !Q_KEY_RE.test(s)) return null;
  const [a, b] = s.split('/');
  const v = R(Number(a), b === undefined ? 1 : Number(b));
  return isR(v) ? v : null;
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
export function iroot(n, q) {
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

export function uniqR(xs) {
  const m = new Map();
  for (const x of xs) if (isR(x)) m.set(rkey(x), x);
  return [...m.values()];
}

// 上标、下标数字，公式显示用
const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹', '-': '⁻', '/': '⸍' };
const SUB = { 0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄', 5: '₅', 6: '₆', 7: '₇', 8: '₈', 9: '₉', '-': '₋' };
export const sup = n => [...String(n)].map(ch => SUP[ch] ?? ch).join('');
export const subscript = n => [...String(n)].map(ch => SUB[ch] ?? ch).join('');
