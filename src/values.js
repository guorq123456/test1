// 单卡的类型系统。
//
// 一张单卡的值（Value）可以是：
//   有理数            {n, d}                       类型 'q'（内置）
//   其他领域注册的类型 {t: '<类型名>', ...}          由 src/domains/*.js 通过 registerType 注册
//
// 类型定义（TypeDef）的字段：
//   t          类型名，如 'mod' 'poly' 'vec' 'mat' 'qty'
//   name       中文名，如 '余数'
//   label(v)?  这张卡的小字说明，如 '模 12'（默认用 name）
//   key(v)     唯一字符串（也是存档格式）。不能和有理数的写法 "-3" "1/2" 混淆
//   parseKey(s) 把 key 解析回值；不是本类型的 key 时返回 null
//   fmt(v)     显示用的文字，允许用 \n 换行（矩阵）
//   size(v)    "大小"，用来限制封闭、延展时的增长（有理数是分子分母的最大值）
//   cmp(a,b)?  排序（默认按 key）
//   sub(v)?    子类型，用于给卡组分类，如 'mod:12'（默认就是 t）
//   window / windowFor(sub)?   有限的"视野"：这个类型里有代表性的一批值，集合运算在它上面进行
//   probes / probesFor(sub)?   探针：判断两个卡组是否相同时用来比对的值
//   probesSmall?               小探针（近似卡组只比对这些）
//   sizeCap?   两两运算的结果超过这个大小就丢掉（默认 WIN_H）
//   bin(op, x, y)  二元运算。至少一个操作数是本类型时会被调用。
//                  返回：值 | OVER | null（没有定义）| {err: '原因'} | undefined（本类型不处理这种组合）
//   call(v, x)?     把这张卡当作函数用（多项式代入）；fmtCall(v, s)? 它的公式写法
//   fmtBind(op, side, c, s)?  自定义 "x op c" 的公式写法（可选）

import { R, isR, rkey, fmtR, height, cmp, gcd, add, sub, mul, div, rpow, parseQKey, Q_KEY_RE, OVER } from './math.js';

export const MSG_OVER = '数字太大了（分子或分母超过了一千万），换小一点的数试试。';

export const TYPES = new Map();

export function registerType(def) {
  if (!def.t || !def.name || !def.key || !def.fmt) throw new Error(`类型 ${def.t} 的定义不完整`);
  TYPES.set(def.t, {
    size: () => 1,
    window: [],
    probes: [],
    parseKey: () => null,
    bin: () => undefined,
    ...def,
  });
}

export const typeOf = v =>
  isR(v) ? 'q' : v && typeof v === 'object' && typeof v.t === 'string' && TYPES.has(v.t) ? v.t : null;
export const isV = v => typeOf(v) !== null;
export const defOf = v => TYPES.get(typeOf(v));
export const vkey = v => (isR(v) ? rkey(v) : defOf(v).key(v));
export const fmtV = v => (isR(v) ? fmtR(v) : defOf(v).fmt(v));
export const sizeV = v => (isR(v) ? height(v) : defOf(v).size(v));
export const eqV = (a, b) => isV(a) && isV(b) && vkey(a) === vkey(b);
export const serV = vkey;
export const baseType = t => String(t).split(':')[0];

export function subtypeOf(v) {
  const d = defOf(v);
  return d.sub ? d.sub(v) : d.t;
}

export function typeLabel(v) {
  const d = defOf(v);
  return d.label ? d.label(v) : d.name;
}

export function cmpV(a, b) {
  const ta = typeOf(a);
  const tb = typeOf(b);
  if (ta !== tb) return ta < tb ? -1 : 1;
  if (ta === 'q') return cmp(a, b);
  const d = TYPES.get(ta);
  if (d.cmp) return d.cmp(a, b);
  const ka = vkey(a);
  const kb = vkey(b);
  return ka < kb ? -1 : ka > kb ? 1 : 0;
}

export function uniqV(xs) {
  const m = new Map();
  for (const x of xs) if (isV(x)) m.set(vkey(x), x);
  return [...m.values()];
}

export function parseVKey(s) {
  if (typeof s !== 'string') return null;
  if (Q_KEY_RE.test(s)) return parseQKey(s);
  for (const d of TYPES.values()) {
    if (d.t === 'q') continue;
    const v = d.parseKey(s);
    if (v) return v;
  }
  return null;
}

export function windowFor(type) {
  const d = TYPES.get(baseType(type));
  if (!d) return [];
  return d.windowFor ? d.windowFor(type) : d.window;
}

export function probesFor(type) {
  const d = TYPES.get(baseType(type));
  if (!d) return [];
  return d.probesFor ? d.probesFor(type) : d.probes;
}

export function smallProbesFor(type) {
  const d = TYPES.get(baseType(type));
  if (!d) return [];
  return d.probesSmall ?? probesFor(type);
}

export function sizeCapFor(type) {
  const d = TYPES.get(baseType(type));
  return d?.sizeCap ?? WIN_H;
}

// ───────────────────────── 二元运算 ─────────────────────────

export const BIN = {
  add: { id: 'add', name: '加法', sym: '+', comm: true },
  sub: { id: 'sub', name: '减法', sym: '−', comm: false },
  mul: { id: 'mul', name: '乘法', sym: '×', comm: true },
  div: { id: 'div', name: '除法', sym: '÷', comm: false },
  pow: { id: 'pow', name: '乘方', sym: '^', comm: false },
  mod: { id: 'mod', name: '取余', sym: 'mod', comm: false },
  cat: { id: 'cat', name: '拼接', sym: '|', comm: false },
};
for (const b of Object.values(BIN)) b.fn = (x, y) => binV(b.id, x, y);

// 额外的运算处理器：处理类型定义没有接住的组合（比如 整数 mod 整数 → 余数）
const EXTRA = [];
export function registerBin(handler) {
  EXTRA.push(handler);
}

// 返回：值 | OVER | null | {err}
export function binV(op, x, y) {
  if (!isV(x) || !isV(y) || !BIN[op]) return null;
  const tx = typeOf(x);
  const ty = typeOf(y);
  for (const t of tx === ty ? [tx] : [tx, ty]) {
    const r = TYPES.get(t).bin(op, x, y);
    if (r !== undefined) return r;
  }
  for (const h of EXTRA) {
    const r = h(op, x, y);
    if (r !== undefined) return r;
  }
  return { err: `${typeLabel(x)}和${typeLabel(y)}之间没有「${BIN[op].name}」这种运算。` };
}

// ───────────────────────── 有理数类型 ─────────────────────────

export const WIN_H = 20; // 视野：分子、分母都不超过 20 的有理数

function rationalsUpTo(h, maxD = h) {
  const out = [];
  for (let d = 1; d <= maxD; d++) for (let n = -h; n <= h; n++) if (gcd(n, d) === 1) out.push(R(n, d));
  return out.sort((x, y) => height(x) - height(y) || cmp(x, y));
}

export const WINDOW = rationalsUpTo(WIN_H);
export const PROBE_SMALL = rationalsUpTo(12, 6);
export const PROBE_LARGE = [
  '13', '16', '17', '24', '25', '27', '31', '32', '36', '49', '63', '64', '81', '97', '100', '127', '128',
  '243', '255', '256', '1000', '1024', '4096', '65536', '-13', '-16', '-25', '-32', '-64', '-97', '-100',
  '-128', '-1000', '-1024', '1/7', '1/8', '1/9', '1/10', '1/12', '1/16', '1/25', '1/32', '1/64', '1/97',
  '1/100', '1/128', '1/1024', '-1/7', '-1/8', '-1/16', '-1/97', '97/2', '13/7', '2/97', '3/64', '5/12',
  '7/8', '25/4', '1024/3', '-7/8', '-97/2', '9/16', '49/100',
].map(parseQKey);
export const PROBES = [...PROBE_SMALL, ...PROBE_LARGE];

registerType({
  t: 'q',
  name: '数',
  key: rkey,
  fmt: fmtR,
  size: height,
  cmp,
  window: WINDOW,
  probes: PROBES,
  probesSmall: PROBE_SMALL,
  parseKey: parseQKey,
  bin(op, x, y) {
    if (!isR(x) || !isR(y)) return undefined;
    switch (op) {
      case 'add':
        return add(x, y);
      case 'sub':
        return sub(x, y);
      case 'mul':
        return mul(x, y);
      case 'div':
        return y.n === 0 ? { err: '不能除以 0。' } : div(x, y);
      case 'pow': {
        const v = rpow(x, y);
        if (v !== null) return v;
        if (x.n === 0) return { err: '0 的 0 次方、0 的负数次方都没有定义。' };
        return { err: `${fmtR(x)} 的 ${fmtR(y)} 次方不是有理数，初等篇里还造不出来。` };
      }
    }
    return undefined;
  },
});

export { OVER };
