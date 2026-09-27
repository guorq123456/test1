// 一元算子：一个输入、一个输出的变换。
//
//   aff    a·x + b            有理数系数
//   pow    xⁿ                 n 是有理数
//   exp    cˣ
//   log    log_c x
//   bind   x ∘ c 或 c ∘ x     二元算子绑定一个任意类型的值（比如 x mod 12、x × e₁）
//   named  领域注册的算子      比如 求导 D、转置 ᵀ、行列式 det
//   fn     把一张单卡当函数用  比如多项式 p(x)
//   chain  依次做若干个

import {
  R,
  isR,
  ZERO,
  ONE,
  NEG1,
  eq,
  eqR,
  isInt,
  inv,
  mul,
  add,
  sub,
  neg,
  div,
  rkey,
  gcd,
  fmtR,
  rpow,
  rlog,
  ipow,
  toNum,
  uniqR,
  OVER,
  sup,
  subscript,
} from './math.js';
import { BIN, binV, isV, vkey, fmtV, parseVKey, TYPES, defOf, eqV, typeOf, powQ, logQ } from './values.js';

// 乘法可交换的类型（矩阵不在里面）
const COMMUTATIVE = new Set(['q', 'mod', 'poly', 'qty']);

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

export const bindU = (op, side, c) => ({ t: 'bind', op, side, c });
export const namedU = id => ({ t: 'named', id });
export const fnU = v => ({ t: 'fn', v });

// 领域注册的具名算子：{ id, name, fmt(s), apply(x), inverse?, desc? }
export const NAMED = new Map();
export function registerNamed(def) {
  if (!def.id || !def.name || !def.fmt || !def.apply) throw new Error(`算子 ${def.id} 的定义不完整`);
  NAMED.set(def.id, def);
}

const Q_KINDS = new Set(['aff', 'pow', 'exp', 'log']);
export const isQStructural = f => Q_KINDS.has(f.t) || (f.t === 'chain' && f.fs.every(isQStructural));

// 返回：值 | OVER | null（没有定义）| {err}
export function applyU(f, x) {
  if (!isV(x)) return null;
  switch (f.t) {
    case 'aff': {
      if (isId(f)) return x;
      // 常数捷径只对数成立：余数、长度、向量乘 0 要得到带类型的零（[0]₁₂、0 步、(0, 0)），走下面的 binV
      if (isConst(f) && isR(x)) return f.b;
      if (isR(x)) {
        const ax = mul(f.a, x);
        return isR(ax) ? add(ax, f.b) : ax;
      }
      const ax = eq(f.a, ONE) ? x : binV('mul', f.a, x);
      if (!isV(ax)) return ax;
      return f.b.n === 0 ? ax : binV('add', ax, f.b);
    }
    case 'pow':
      // 负整数次方写成 1/x、1/x²，0 代进去是除以 0，不说成"0 的负数次方"
      if (isR(x) && x.n === 0 && isInt(f.n) && f.n.n < 0) return { err: '不能除以 0。', reason: 'undefined' };
      return isR(x) ? powQ(x, f.n) : binV('pow', x, f.n);
    case 'exp':
      return isR(x) ? powQ(f.c, x) : { err: `${fmtV(x)} 不是数，不能当指数。`, reason: 'type' };
    case 'log':
      return isR(x) ? logQ(f.c, x) : { err: `${fmtV(x)} 不是数，不能取对数。`, reason: 'type' };
    case 'bind':
      return f.side === 'r' ? binV(f.op, x, f.c) : binV(f.op, f.c, x);
    case 'named': {
      const d = NAMED.get(f.id);
      return d ? d.apply(x) : null;
    }
    case 'fn': {
      const d = defOf(f.v);
      return d.call ? d.call(f.v, x) : null;
    }
    case 'chain': {
      let v = x;
      for (const g of f.fs) {
        v = applyU(g, v);
        if (!isV(v)) return v;
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
    case 'bind':
      return `bind(${f.op},${f.side},${vkey(f.c)})`;
    case 'named':
      return `named(${f.id})`;
    case 'fn':
      return `fn(${vkey(f.v)})`;
    case 'chain':
      return `chain(${f.fs.map(ukey).join(';')})`;
  }
  return '?';
}

// d 的素因子都整除 m（反复约掉公因数，约不动时看剩下的是不是 1）
function primesDivide(d, m) {
  for (let g = gcd(d, m); g > 1; g = gcd(d, m)) d /= g;
  return d === 1;
}

// 尝试把"先 f 后 g"化简成一个算子；化简不了返回 undefined。
// 只在化简后的算子"凡是 f∘g 算不出的地方它也算不出"时才化简：
// 比如 log₂x 接 2ˣ 不能化成 x，因为 3 代入 log₂x 就算不出，化成 x 就把 3 放过去了。
function merge(f, g) {
  if (isId(f)) return g;
  if (isId(g)) return f;
  // 整系数的 a·x + b 对任何数都有定义，所以只有 f 是它时，接一个常数才能直接变成常数。
  // 分数系数不行：x/2 在 ℤ₁₂ 上没有定义（2 没有逆元），x/2 接 5 不能化成 5
  if (isConst(g)) return f.t === 'aff' && isInt(f.a) && isInt(f.b) ? g : undefined;
  if (isConst(f)) {
    const v = applyU(g, f.b);
    return isR(v) ? aff(ZERO, v) : undefined;
  }
  if (f.t === 'aff' && g.t === 'aff') {
    const a = mul(g.a, f.a);
    const ab = mul(g.a, f.b);
    if (!isR(a) || !isR(ab)) return undefined;
    const b = add(ab, g.b);
    if (!isR(b)) return undefined;
    // 在 ℤₙ 上 a·x + b 有定义 ⇔ n 的素因子都不整除 a、b 的分母。合并后分母的素因子只会变少，
    // 所以要原来四个系数分母的素因子都还在，化简才不会把没有定义的地方放过去：
    // x/2 接 2x 不能化成 x（[1]₁₂ 一步步做在 x/2 就没有定义），x/2 接 x/3 可以化成 x/6
    const D = a.d * b.d;
    if (![f.a, f.b, g.a, g.b].every(c => primesDivide(c.d, D))) return undefined;
    return aff(a, b);
  }
  if (f.t === 'pow' && g.t === 'pow' && isInt(f.n) && isInt(g.n)) {
    // 两个负指数相接会得到正指数，把 0 放过去；不化简
    if (f.n.n < 0 && g.n.n < 0) return undefined;
    const n = mul(f.n, g.n);
    return isR(n) ? powU(n) : undefined;
  }
  if (f.t === 'named' && g.t === 'named') {
    const d = NAMED.get(f.id);
    if (d && d.inverse === g.id) return ID;
  }
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
    case 'bind': {
      const { op, side, c } = f;
      if (op === 'add') return bindU('sub', 'r', c);
      if (op === 'sub') return side === 'r' ? bindU('add', 'r', c) : f;
      const ci = op === 'mul' || op === 'div' ? binV('pow', c, NEG1) : null;
      if (op === 'mul') {
        // c 没有倒数（[2]₁₂、奇异矩阵）时，乘以 c 不是一一对应，没有逆
        if (!isV(ci)) return null;
        return side === 'r' ? bindU('div', 'r', c) : bindU('mul', 'l', ci);
      }
      if (op === 'div') {
        if (side === 'r') return bindU('mul', 'r', c);
        // c ÷ x：乘法可交换时它是自己的逆；矩阵不可交换，逆是 y ↦ y⁻¹ · c
        if (!isV(ci)) return null;
        return COMMUTATIVE.has(typeOf(c)) ? f : compose(powU(NEG1), bindU('mul', 'r', c));
      }
      return null;
    }
    case 'named': {
      const d = NAMED.get(f.id);
      return d?.inverse ? namedU(d.inverse) : null;
    }
    case 'fn': {
      const d = defOf(f.v);
      return d.invertFn ? d.invertFn(f.v) : null;
    }
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

// 有理数一元算子的原像：{ list } 表示有限个；{ pred } 表示无穷多个，用谓词描述。
// 如果倒推时数字超出了上限，结果里会带 unknown: true（原像可能存在，只是游戏里表示不了）。
// 只对 isQStructural 的算子有意义。
export function preU(f, y) {
  const verify = xs => {
    const list = uniqR(xs).filter(x => eqR(applyU(f, x), y));
    return { list, unknown: !list.length && xs.some(x => x === OVER) };
  };
  if (!isR(y)) return { list: [] };
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
      // (−1)ˣ 只会得到 ±1：别的 y 一定没有原像，±1 的原像有无穷多个
      if (eq(f.c, NEG1)) return y.d === 1 && Math.abs(y.n) === 1 ? { pred: x => eqR(applyU(f, x), y) } : { list: [] };
      if (f.c.n < 0) {
        // |c| ≠ 1，所以 |c|^e = |y| 的有理数 e 唯一；符号和定义域交给 verify 检查
        if (y.n === 0) return { list: [] };
        const e = rlog(neg(f.c), y.n < 0 ? neg(y) : y);
        return verify(e ? [e] : []);
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

// 不用加括号的输入写法：变量 x，或者一个非负整数（√2、10⁹）
const isAtom = s => s === 'x' || /^\d+$/.test(s);
const isTight = s => !/\s/.test(s);
// 只留最外层（括号里的内容去掉），用来判断 / 和空格是不是在最外层
function outer(s) {
  let depth = 0;
  let o = '';
  for (const ch of s) {
    if (ch === '(' || ch === '[') depth++;
    else if (ch === ')' || ch === ']') depth--;
    else if (depth === 0) o += ch;
  }
  return o;
}
// 系数乘式子（2x、2·3、2√x、2(x/2)）：放在分数线前面要加括号，写成 (2x)/2，免得和 2(x/2) 分不清
const isProduct = s => /^\d+[^\d⁰¹²³⁴⁵⁶⁷⁸⁹ˣ^]/.test(s);
// 1/t，t 是一整项（1/x、1/x²、1/(x + 1)、1/0），不是 1/x + 1 这种
const isRecip = s => s.startsWith('1/') && !/[\s/]/.test(outer(s.slice(2)));
// 放在分数线前面时需要括号的情况
const tightDiv = s => (!isTight(s) || s.includes('/') || s.startsWith('−') || isProduct(s) ? `(${s})` : s);
// 负号开头的也要括号：−(−3)、(−3) mod 12，不写 −−3
const wrap = s => (isTight(s) && !s.startsWith('−') ? s : `(${s})`);

// 系数 k（字符串）乘以式子 s
function scale(k, s) {
  if (isRecip(s)) return `${k}/${s.slice(2)}`;
  if (s.startsWith('−')) return `${k}·(${s})`;
  if (!isTight(s)) return `${k}(${s})`;
  // 最外层有分数线：2(x/2)，不写 2x/2（和 (2x)/2 分不清）
  if (outer(s).includes('/')) return /^[0-9]/.test(s) ? `${k}·(${s})` : `${k}(${s})`;
  if (/^[0-9(]/.test(s)) return `${k}·${s}`;
  return `${k}${s}`;
}

function fmtAff(a, b, s) {
  if (a.n === 0) return fmtR(b);
  if (eq(a, NEG1)) {
    const t = wrap(s);
    return b.n === 0 ? `−${t}` : `${fmtR(b)} − ${t}`;
  }
  let lead;
  if (eq(a, ONE)) lead = s;
  else if (a.d === 1) lead = scale(fmtR(a), s);
  else if (isRecip(s)) {
    // (k/d)·(1/t) 写成 k/(d·t)：2/(3x)、1/(2·0)，不写 2/x/3
    const t = s.slice(2);
    lead = `${fmtR(R(a.n))}/(${a.d}${/^[0-9−]/.test(t) ? '·' : ''}${t})`;
  } else {
    const top = a.n === 1 ? tightDiv(s) : a.n === -1 ? `−${tightDiv(s)}` : scale(fmtR(R(a.n)), s);
    lead = `${top}/${a.d}`;
  }
  if (b.n === 0) return lead;
  return b.n > 0 ? `${lead} + ${fmtR(b)}` : `${lead} − ${fmtR(neg(b))}`;
}

function fmtPow(n, s) {
  const base = isAtom(s) ? s : `(${s})`;
  if (isInt(n)) {
    if (n.n === 0) return `${base}⁰`;
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
  if (s === 'x') return `${base}ˣ`;
  if (/^\d+$/.test(s)) return `${base}${sup(s)}`;
  return `${base}^(${s})`;
}

function fmtLog(c, s) {
  const base = c.d === 1 ? `log${subscript(c.n)}` : `log_(${fmtR(c)})`;
  return isAtom(s) ? `${base}${s}` : `${base}(${s})`;
}

function fmtBind(f, s) {
  const d = defOf(f.c);
  if (d.fmtBind) {
    const r = d.fmtBind(f.op, f.side, f.c, s);
    if (r) return r;
  }
  // x ^ c 的 c 是数时和 x^(1/5) 一样写：x^(1/13)，不写 x ^ 1/13（会读成 x¹/13）
  if (f.op === 'pow' && f.side === 'r' && isR(f.c)) return fmtPow(f.c, s);
  const sym = BIN[f.op].sym;
  const cs = fmtV(f.c);
  // 分数、负数常数加括号；带单位的量（3/息）只看空格，不看 /
  const ct = /\s/.test(cs) || (isR(f.c) && (f.c.d !== 1 || f.c.n < 0)) ? `(${cs})` : cs;
  return f.side === 'r' ? `${wrap(s)} ${sym} ${ct}` : `${ct} ${sym} ${wrap(s)}`;
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
    case 'bind':
      return fmtBind(f, s);
    case 'named':
      return NAMED.get(f.id)?.fmt(s) ?? `${f.id}(${s})`;
    case 'fn': {
      const d = defOf(f.v);
      return d.fmtCall ? d.fmtCall(f.v, s) : `(${fmtV(f.v)})(${s})`;
    }
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
    case 'bind':
      return { t: 'bind', op: f.op, side: f.side, c: vkey(f.c) };
    case 'named':
      return { t: 'named', id: f.id };
    case 'fn':
      return { t: 'fn', v: vkey(f.v) };
    case 'chain':
      return { t: 'chain', fs: f.fs.map(serU) };
  }
  return null;
}

export function parseU(o) {
  if (!o) return null;
  const k = s => {
    const x = parseVKey(s);
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
    case 'bind': {
      const c = parseVKey(o.c);
      return c && BIN[o.op] && (o.side === 'l' || o.side === 'r') ? bindU(o.op, o.side, c) : null;
    }
    case 'named':
      return NAMED.has(o.id) ? namedU(o.id) : null;
    case 'fn': {
      const v = parseVKey(o.v);
      return v && defOf(v).call ? fnU(v) : null;
    }
    case 'chain': {
      const fs = (o.fs || []).map(parseU);
      return fs.length >= 2 && fs.every(Boolean) ? { t: 'chain', fs } : null;
    }
  }
  return null;
}

// ───────────────────────── 二元算子绑定一个值 ─────────────────────────

const Q_OPS = new Set(['add', 'sub', 'mul', 'div', 'pow']);

// 检查绑定出来的算子至少对某些输入算得出来；都算不出时带上第一条解释
function genericBind(b, side, c) {
  const f = bindU(b.id, side, c);
  const trial = [c, ...[...TYPES.values()].flatMap(t => t.window.slice(0, 8))];
  let why = null;
  for (const x of trial) {
    const r = applyU(f, x);
    if (isV(r)) return { f };
    if (!why && r && typeof r === 'object' && r.err) why = r.err;
  }
  const s = fmtU(f);
  return { err: why ? `${s} 对任何输入都算不出结果：${why}` : `${s} 对任何输入都算不出结果。` };
}

// 右边绑定一个值：x ∘ c
export function bindRight(b, c) {
  if (!isR(c) || !Q_OPS.has(b.id)) return genericBind(b, 'r', c);
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
      // x ^ 0 不是常数 1：0 ^ 0 没有定义，矩阵、量的 0 次方也不是数 1，逐值算
      if (c.n === 0) return { f: bindU('pow', 'r', c) };
      return c.d > 12 ? { err: '指数的分母太大了。' } : { f: powU(c) };
  }
  return { err: '这个算子不能绑定数字。' };
}

// 左边绑定一个值：c ∘ x
export function bindLeft(c, b) {
  if (!isR(c) || !Q_OPS.has(b.id)) return genericBind(b, 'l', c);
  switch (b.id) {
    case 'add':
      return { f: aff(ONE, c) };
    case 'sub':
      return { f: aff(NEG1, c) };
    case 'mul':
      return { f: aff(c, ZERO) };
    case 'div':
      // 0 ÷ x 不是常数 0：x = 0 时没有定义，所以走逐值计算的通用绑定
      return { f: c.n === 0 ? bindU('div', 'l', c) : compose(powU(NEG1), aff(c, ZERO)) };
    case 'pow':
      return c.n === 0 ? { err: '0ˣ 在初等篇里先不讨论，换一个底数吧。' } : { f: expU(c) };
  }
  return { err: '这个算子不能绑定数字。' };
}

export { eqV, ipow };
