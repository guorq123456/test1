// 第 7 章「方向与变换」：二维向量与 2×2 矩阵。
//
// 单卡类型：
//   向量 'vec'  {t: 'vec', xs: [a, b]}        列向量 (a, b)，a、b 是有理数
//              key  "v:a,b"       fmt  "(1, 2)"
//   矩阵 'mat'  {t: 'mat', m: [[a, b], [c, d]]}  2×2 矩阵，行优先
//              key  "m:a,b,c,d"   fmt  "[a b; c d]"（分号隔开两行，写在一行里）
//
// 运算：
//   向量 ± 向量、数 × 向量、向量 × 数、向量 ÷ 数
//   向量 × 向量 = 点积（得到一个数）
//   向量 | 向量 = 以两个向量为列的矩阵（拼接）
//   矩阵 ± 矩阵、数 × 矩阵、矩阵 × 数、矩阵 ÷ 数
//   矩阵 × 矩阵、矩阵 × 向量
//   矩阵 ^ 整数（负数用逆矩阵）、矩阵 ÷ 矩阵 = A × B⁻¹、数 ÷ 矩阵 = 数 × B⁻¹
//   其他组合都没有定义，会给玩家一句解释
//
// 具名算子：TR 转置（自己是自己的逆）、DET 行列式、TRACE 迹。

import { R, isR, isInt, eq, add, sub, mul, neg, inv, rkey, fmtR, height, cmp, parseQKey, OVER } from '../math.js';
import { registerType, BIN } from '../values.js';
import { registerNamed, namedU } from '../unary.js';

// ───────────────────────── 构造与判断 ─────────────────────────

export const isVec = v => v !== null && typeof v === 'object' && v.t === 'vec' && Array.isArray(v.xs);
export const isMat = v => v !== null && typeof v === 'object' && v.t === 'mat' && Array.isArray(v.m);

// 分量里只要有一个算溢出了，整个结果就是 OVER
const allR = xs => xs.every(isR);

export function vec(a, b) {
  if (!allR([a, b])) return OVER;
  return { t: 'vec', xs: [a, b] };
}

export function mat(a, b, c, d) {
  if (!allR([a, b, c, d])) return OVER;
  return { t: 'mat', m: [[a, b], [c, d]] };
}

// 用整数或 "n/d" 字符串快速写：V(1, 0)、Mx(0, -1, 1, 0)、V('1/2', 1)
const q = a => (typeof a === 'string' ? parseQKey(a) : R(a));
export const V = (a, b) => vec(q(a), q(b));
export const Mx = (a, b, c, d) => mat(q(a), q(b), q(c), q(d));

export const I2 = Mx(1, 0, 0, 1);

const flat = m => [m.m[0][0], m.m[0][1], m.m[1][0], m.m[1][1]];

export const keyV = v => `v:${rkey(v.xs[0])},${rkey(v.xs[1])}`;
export const keyM = v => `m:${flat(v).map(rkey).join(',')}`;
export const fmtVec = v => `(${fmtR(v.xs[0])}, ${fmtR(v.xs[1])})`;
export const fmtMat = v => `[${fmtR(v.m[0][0])} ${fmtR(v.m[0][1])}; ${fmtR(v.m[1][0])} ${fmtR(v.m[1][1])}]`;

const Q_RE = '-?\\d+(?:/\\d+)?';
const VEC_RE = new RegExp(`^v:(${Q_RE}),(${Q_RE})$`);
const MAT_RE = new RegExp(`^m:(${Q_RE}),(${Q_RE}),(${Q_RE}),(${Q_RE})$`);

export function parseVecKey(s) {
  const m = typeof s === 'string' ? VEC_RE.exec(s) : null;
  if (!m) return null;
  const v = vec(parseQKey(m[1]), parseQKey(m[2]));
  return isVec(v) ? v : null;
}

export function parseMatKey(s) {
  const m = typeof s === 'string' ? MAT_RE.exec(s) : null;
  if (!m) return null;
  const v = mat(parseQKey(m[1]), parseQKey(m[2]), parseQKey(m[3]), parseQKey(m[4]));
  return isMat(v) ? v : null;
}

// 大小：所有分量 height 的最大值。
// 矩阵里绝对值不小于 2 的整数分量多算 1（2 算 3，1/2 仍算 2）：这样在 SIZE_CAP = 2 以内，
// 矩阵的分量只能取 {−1, −1/2, 0, 1/2, 1}，一共 625 个矩阵。要是把 ±2 也放进来就有 2401 个，
// 「M₂ 在 + 下封闭」这类操作会把引擎的运算预算用满，要等上一秒。
const sizeOf = xs => Math.max(1, ...xs.map(height));
const entryM = a => (a.d === 1 && Math.abs(a.n) >= 2 ? Math.abs(a.n) + 1 : height(a));
export const sizeVec = v => sizeOf(v.xs);
export const sizeMat = v => Math.max(1, ...flat(v).map(entryM));

// 排序：先按大小，再按分量逐个比
function cmpParts(xs, ys) {
  const sx = sizeOf(xs);
  const sy = sizeOf(ys);
  if (sx !== sy) return sx - sy;
  for (let i = 0; i < xs.length; i++) {
    const c = cmp(xs[i], ys[i]);
    if (c !== 0) return c;
  }
  return 0;
}

// ───────────────────────── 向量运算 ─────────────────────────

export const addV = (x, y) => vec(add(x.xs[0], y.xs[0]), add(x.xs[1], y.xs[1]));
export const subV = (x, y) => vec(sub(x.xs[0], y.xs[0]), sub(x.xs[1], y.xs[1]));
export const scaleV = (k, x) => vec(mul(k, x.xs[0]), mul(k, x.xs[1]));

// 点积：结果是一个数
export function dot(x, y) {
  const a = mul(x.xs[0], y.xs[0]);
  const b = mul(x.xs[1], y.xs[1]);
  if (!allR([a, b])) return OVER;
  return add(a, b);
}

// 拼接：两个列向量并排，左边的是第一列
export const cat = (x, y) => mat(x.xs[0], y.xs[0], x.xs[1], y.xs[1]);

// ───────────────────────── 矩阵运算 ─────────────────────────

export const addM = (x, y) => mat(...flat(x).map((a, i) => add(a, flat(y)[i])));
export const subM = (x, y) => mat(...flat(x).map((a, i) => sub(a, flat(y)[i])));
export const scaleM = (k, x) => mat(...flat(x).map(a => mul(k, a)));
export const transpose = x => mat(x.m[0][0], x.m[1][0], x.m[0][1], x.m[1][1]);

// 两个数相乘再相加，中途溢出就返回 OVER
function mulAdd(a, b, c, d) {
  const p = mul(a, b);
  const r = mul(c, d);
  if (!allR([p, r])) return OVER;
  return add(p, r);
}

export function det(x) {
  const [a, b, c, d] = flat(x);
  const p = mul(a, d);
  const r = mul(b, c);
  if (!allR([p, r])) return OVER;
  return sub(p, r);
}

export function trace(x) {
  return add(x.m[0][0], x.m[1][1]);
}

export function mulM(x, y) {
  const [a, b, c, d] = flat(x);
  const [e, f, g, h] = flat(y);
  return mat(mulAdd(a, e, b, g), mulAdd(a, f, b, h), mulAdd(c, e, d, g), mulAdd(c, f, d, h));
}

export function mulMV(x, v) {
  const [a, b, c, d] = flat(x);
  const [p, r] = v.xs;
  return vec(mulAdd(a, p, b, r), mulAdd(c, p, d, r));
}

// 逆矩阵。行列式是 0 时返回 null；数字太大返回 OVER
export function invM(x) {
  const dt = det(x);
  if (!isR(dt)) return dt;
  if (dt.n === 0) return null;
  const [a, b, c, d] = flat(x);
  const k = inv(dt);
  return mat(mul(d, k), mul(neg(b), k), mul(neg(c), k), mul(a, k));
}

export function powM(x, k) {
  if (k === 0) return I2;
  if (k < 0) {
    const y = invM(x);
    return isMat(y) ? powM(y, -k) : y;
  }
  // 反复平方
  let base = x;
  let out = I2;
  while (k > 0) {
    if (k & 1) {
      out = mulM(out, base);
      if (!isMat(out)) return out;
    }
    k = Math.floor(k / 2);
    if (k > 0) {
      base = mulM(base, base);
      if (!isMat(base)) return base;
    }
  }
  return out;
}

// ───────────────────────── 二元运算的分派 ─────────────────────────

const kindOf = v => (isR(v) ? 'q' : isVec(v) ? 'vec' : isMat(v) ? 'mat' : null);
const fmtAny = v => (isR(v) ? fmtR(v) : isVec(v) ? fmtVec(v) : fmtMat(v));
const nameOf = { q: '数', vec: '向量', mat: '矩阵' };

const MSG_SINGULAR = m => `${fmtMat(m)} 的行列式是 0，没有逆矩阵。`;
const MSG_VEC_MAT = '列向量不能放在矩阵左边。要变换一个向量，请把矩阵放左边：矩阵 × 向量。';

// 出错时返回 { err, reason }，reason 的三类见 docs/v03-step1.md 第 2 节
function linBin(op, x, y) {
  const kx = kindOf(x);
  const ky = kindOf(y);
  // 另一边是别的领域的类型：交给它们处理
  if (kx === null || ky === null) return undefined;
  const k = `${kx}|${ky}`;
  const noOp = why => ({ err: `${nameOf[kx]}和${nameOf[ky]}之间没有「${BIN[op].name}」：${why}`, reason: 'type' });

  switch (op) {
    case 'add':
    case 'sub': {
      if (k === 'vec|vec') return op === 'add' ? addV(x, y) : subV(x, y);
      if (k === 'mat|mat') return op === 'add' ? addM(x, y) : subM(x, y);
      if (kx === 'q' || ky === 'q') {
        const other = kx === 'q' ? ky : kx;
        return noOp(
          other === 'vec'
            ? '向量有两个分量，数只有一个，对不上。想把每个分量都加上同一个数，先造一个向量再加。'
            : '矩阵有四个分量，数只有一个，对不上。想加上 2，先造出标量矩阵 2 × I 再加。',
        );
      }
      return noOp('一个是两个分量的向量，一个是四个分量的矩阵，对不上。');
    }
    case 'mul': {
      if (k === 'q|vec') return scaleV(x, y);
      if (k === 'vec|q') return scaleV(y, x);
      if (k === 'vec|vec') return dot(x, y);
      if (k === 'q|mat') return scaleM(x, y);
      if (k === 'mat|q') return scaleM(y, x);
      if (k === 'mat|mat') return mulM(x, y);
      if (k === 'mat|vec') return mulMV(x, y);
      return { err: MSG_VEC_MAT, reason: 'type' };
    }
    case 'div': {
      if (ky === 'q') {
        if (y.n === 0) return { err: '不能除以 0。', reason: 'undefined' };
        return kx === 'vec' ? scaleV(inv(y), x) : scaleM(inv(y), x);
      }
      if (ky === 'mat') {
        if (kx === 'vec') return { err: '向量不能除以矩阵。想"撤销"一个变换，用它的逆矩阵去乘：M⁻¹ × 向量。', reason: 'type' };
        const yi = invM(y);
        if (yi === null) return { err: MSG_SINGULAR(y), reason: 'undefined' };
        if (!isMat(yi)) return yi;
        return kx === 'q' ? scaleM(x, yi) : mulM(x, yi);
      }
      // ky === 'vec'
      if (kx === 'vec') return noOp('两个向量相除说不清是什么。想比较它们，可以用点积（×）。');
      return noOp('向量没有"倒数"，不能当除数。');
    }
    case 'pow': {
      if (k === 'mat|q') {
        // 分数次方（矩阵开方）在更大的世界里可能有结果，只是这里写不出来
        if (!isInt(y)) return { err: `矩阵只能做整数次方，${fmtR(y)} 次方算不了。`, reason: 'unrepresentable' };
        if (Math.abs(y.n) > 1e6) return OVER;
        const r = powM(x, y.n);
        if (r === null) return { err: `${MSG_SINGULAR(x)}所以它的负数次方也没有。`, reason: 'undefined' };
        return r;
      }
      if (kx === 'vec') return noOp('向量乘向量是点积，得到的是数，再往下就乘不动了。');
      if (ky !== 'q') return noOp('指数得是一个整数。');
      return noOp('数的向量次方、矩阵次方都没有定义。');
    }
    case 'mod':
      return noOp('取余只对整数做。');
    case 'cat': {
      if (k === 'vec|vec') return cat(x, y);
      return noOp('拼接只能把两个列向量并排拼成一个 2×2 矩阵。');
    }
  }
  return undefined;
}

// 绑定值的公式："x × (1, 0)"、"[0 −1; 1 0] × x"。向量、矩阵自带括号，不用再套一层
function fmtBind(op, side, c, s) {
  const sym = BIN[op].sym;
  const xs = /\s/.test(s) ? `(${s})` : s;
  const cs = fmtAny(c);
  return side === 'r' ? `${xs} ${sym} ${cs}` : `${cs} ${sym} ${xs}`;
}

// ───────────────────────── 视野与探针 ─────────────────────────

const S7 = ['-2', '-1', '-1/2', '0', '1/2', '1', '2'].map(parseQKey);
const S5 = ['-1', '-1/2', '0', '1/2', '1'].map(parseQKey);
const S3 = ['-1', '0', '1'].map(parseQKey);

// 向量的视野：分量取自 {−2, −1, −1/2, 0, 1/2, 1, 2}，共 49 个
export const WINDOW_V = S7.flatMap(a => S7.map(b => vec(a, b)));
// 小探针：两两运算、封闭常常能覆盖到的那些
export const PROBES_SMALL_V = [
  ...S5.flatMap(a => S5.map(b => vec(a, b))),
  ...['v:2,0', 'v:-2,0', 'v:0,2', 'v:0,-2'].map(parseVecKey),
];
export const PROBES_V = [
  ...WINDOW_V,
  ...['v:3,0', 'v:-3,0', 'v:0,3', 'v:0,-3', 'v:1/3,0', 'v:0,1/3', 'v:3,3', 'v:2,3', 'v:3,-2', 'v:1/2,1/3', 'v:5,0', 'v:0,-5', 'v:20,20', 'v:1/20,0', 'v:7,1/7', 'v:-4,4'].map(
    parseVecKey,
  ),
];

// 矩阵的视野：分量取自 {−1, 0, 1} 的 81 个，再加上几个带 1/2、2 的
const BASIC_M = S3.flatMap(a => S3.flatMap(b => S3.flatMap(c => S3.map(d => mat(a, b, c, d)))));
const SHAPES = ['m:1,0,0,1', 'm:1,0,0,0', 'm:0,0,0,1', 'm:0,1,0,0', 'm:0,0,1,0'].map(parseMatKey);
const HALF_M = SHAPES.map(x => scaleM(R(1, 2), x));
const DOUBLE_M = SHAPES.map(x => scaleM(R(2), x));
export const WINDOW_M = [...BASIC_M, ...HALF_M, ...DOUBLE_M];
// 小探针：带 1/2 的那几个能把 ℤ·I 和 ℚ·I、ℤ² | ℤ² 和 M₂ 区分开；带 2 的超出了 SIZE_CAP，两两运算算不出，不放进来
export const PROBES_SMALL_M = [...BASIC_M, ...HALF_M];
export const PROBES_M = [
  ...WINDOW_M,
  ...[
    'm:3,0,0,3', 'm:1/3,0,0,1/3', 'm:-2,0,0,-2', 'm:-1/2,0,0,-1/2', 'm:3,0,0,0', 'm:1,0,0,2', 'm:2,0,0,1', 'm:1/2,0,0,1', 'm:0,3,0,0', 'm:0,0,3,0', 'm:0,3,2,0', 'm:0,-1/2,2,0',
    'm:1,2,3,4', 'm:1,2,2,4', 'm:2,1,1,1', 'm:1/2,1/3,0,1', 'm:1,1/2,1/2,1', 'm:1,1,1,1', 'm:2,2,2,2', 'm:0,2,0,0', 'm:20,0,0,20', 'm:1,20,0,1', 'm:3,1,2,1', 'm:5,-3,-3,2',
  ].map(parseMatKey),
];

// 两两运算、封闭的结果大小超过它就丢掉：向量分量限制在 {−2, −1, −1/2, 0, 1/2, 1, 2}，矩阵分量限制在 {−1, −1/2, 0, 1/2, 1}
export const SIZE_CAP = 2;

// ───────────────────────── 类型注册 ─────────────────────────

registerType({
  t: 'vec',
  name: '向量',
  label: () => '向量',
  key: keyV,
  parseKey: parseVecKey,
  fmt: fmtVec,
  size: sizeVec,
  cmp: (a, b) => cmpParts(a.xs, b.xs),
  window: WINDOW_V,
  probes: PROBES_V,
  probesSmall: PROBES_SMALL_V,
  sizeCap: SIZE_CAP,
  bin: linBin,
  fmtBind,
});

registerType({
  t: 'mat',
  name: '矩阵',
  label: () => '矩阵',
  key: keyM,
  parseKey: parseMatKey,
  fmt: fmtMat,
  size: sizeMat,
  cmp: (a, b) => cmpParts(flat(a), flat(b)),
  window: WINDOW_M,
  probes: PROBES_M,
  probesSmall: PROBES_SMALL_M,
  sizeCap: SIZE_CAP,
  bin: linBin,
  fmtBind,
});

// ───────────────────────── 具名算子 ─────────────────────────

const onlyMat = (what, f, whyNotVec) => x => {
  if (isMat(x)) return f(x);
  if (isVec(x)) return { err: `${what}只对矩阵有定义。${whyNotVec}`, reason: 'type' };
  if (isR(x)) return { err: `${what}只对矩阵有定义，数没有${what}。`, reason: 'type' };
  return { err: `${what}只对矩阵有定义。`, reason: 'type' };
};

registerNamed({
  id: 'TR',
  name: '转置',
  fmt: s => (/\s/.test(s) ? `(${s})ᵀ` : `${s}ᵀ`),
  apply: onlyMat('转置', transpose, '列向量转过来是行向量，这个游戏里只有列向量。'),
  inverse: 'TR',
  desc: '把矩阵沿对角线翻过来：行变成列，列变成行。翻两次就回到原样，所以它是自己的逆。',
});

registerNamed({
  id: 'DET',
  name: '行列式',
  fmt: s => `det(${s})`,
  apply: onlyMat('行列式', det, '向量只有一列，算不出面积的倍数。'),
  desc: '[a b; c d] 的行列式是 ad − bc。它的绝对值是矩阵把面积放大的倍数；是负数说明平面被翻了个面（比如反射，行列式是 −1）；等于 0 的矩阵把平面压扁了，没有逆。',
});

registerNamed({
  id: 'TRACE',
  name: '迹',
  fmt: s => `tr(${s})`,
  apply: onlyMat('迹', trace, '向量没有对角线。'),
  desc: '对角线上两个数的和：[a b; c d] 的迹是 a + d。',
});

// ───────────────────────── 章节内容 ─────────────────────────

export const CHAPTER = {
  id: 7,
  title: '方向与变换',
  desc: '把两个数排成一列，就有了方向。',
  intro:
    '一个数只能说"多少"，两个数排成一列就能说"往哪边、走多远"，这就是向量。把两个向量并排放，就得到一个 2×2 矩阵；矩阵乘向量，是把整个平面旋转、翻转、拉伸。这一章的卡组有的是平面上的一条线、一张网，有的是一小群变换，转四次就回到原地。',
  unlock: {
    when: 'd:Q',
    gives: ['c:v:1,0', 'c:v:0,1', 'b:cat', 'u:TR', 'u:DET', 'u:TRACE'],
    note: '集齐有理数 ℚ 之后，你拿到了两个方向 e₁ = (1, 0)、e₂ = (0, 1)，以及「拼接」、转置、行列式和迹。试试 e₁ | e₂。',
  },
};

export const NAMED_UN = [
  { id: 'TR', name: '转置', f: namedU('TR') },
  { id: 'DET', name: '行列式', f: namedU('DET') },
  { id: 'TRACE', name: '迹', f: namedU('TRACE') },
];

export const BIN_INFO = {
  cat: { desc: '把两个列向量并排放在一起，拼成一个 2×2 矩阵：左边的是第一列，右边的是第二列。(1, 0) | (0, 1) 就是单位矩阵 I。' },
};

const isZeroR = a => a.n === 0;

export const CATALOG = [
  {
    id: 'Xaxis',
    short: 'ℚe₁',
    name: 'x 轴',
    ch: 7,
    type: 'vec',
    preview: '{(a, 0)}：(1, 0)、(−1, 0)、(1/2, 0)、…',
    struct: '群',
    groupOp: '+',
    note: '(x 轴, +) 是群：第二个分量一直是 0，(0, 0) 是单位元，(a, 0) 的逆元是 (−a, 0)。它和 (ℚ, +) 长得一模一样。',
    desc: '所有第二个分量是 0 的向量，也就是 e₁ 的全部倍数。',
    hint: '让 ℚ 里的每个数都乘以 e₁ = (1, 0)。',
    has: v => isVec(v) && isZeroR(v.xs[1]),
    recipes: [
      ['d:Q', 'b:mul', 'c:v:1,0'],
      ['c:m:1,0,0,0', 'b:mul', 'd:Plane'],
      ['c:m:0,-1,1,0', 'b:mul', 'd:Yaxis'],
    ],
  },
  {
    id: 'Yaxis',
    short: 'ℚe₂',
    name: 'y 轴',
    ch: 7,
    type: 'vec',
    preview: '{(0, b)}：(0, 1)、(0, −1)、(0, 1/2)、…',
    struct: '群',
    groupOp: '+',
    note: '(y 轴, +) 是群，和 x 轴一样。把 x 轴整个转 90°，就是 y 轴。',
    desc: '所有第一个分量是 0 的向量，也就是 e₂ 的全部倍数。',
    hint: '让 ℚ 里的每个数都乘以 e₂ = (0, 1)；或者用旋转矩阵 [0 −1; 1 0] 把 x 轴转过来。',
    has: v => isVec(v) && isZeroR(v.xs[0]),
    recipes: [
      ['d:Q', 'b:mul', 'c:v:0,1'],
      ['c:m:0,0,0,1', 'b:mul', 'd:Plane'],
      ['c:m:0,-1,1,0', 'b:mul', 'd:Xaxis'],
    ],
  },
  {
    id: 'Cross',
    short: '四方向',
    name: '四个方向',
    ch: 7,
    type: 'vec',
    preview: '{(1, 0), (0, 1), (−1, 0), (0, −1)}',
    list: ['v:1,0', 'v:0,1', 'v:-1,0', 'v:0,-1'],
    struct: '集合',
    note: '对 + 不封闭：(1, 0) + (1, 0) = (2, 0) 跑出去了。它是 e₁ 被旋转群转出来的四个位置。',
    desc: '东南西北：e₁ 每次转 90°，转四次回到原地。',
    hint: '让旋转群 C₄ 里的每个矩阵都去乘 e₁。',
    has: v => isVec(v) && v.xs.some(isZeroR) && v.xs.some(a => Math.abs(a.n) === 1 && a.d === 1),
    recipes: [
      ['d:Rot4', 'b:mul', 'c:v:1,0'],
      ['d:Dih4', 'b:mul', 'c:v:1,0'],
      ['d:Refl', 'b:mul', 'c:v:1,0'],
      ['d:Rot4', 'b:mul', 'c:v:0,1'],
    ],
  },
  {
    id: 'Lattice',
    short: 'ℤ²',
    name: '整点格',
    ch: 7,
    type: 'vec',
    preview: '{(a, b)：a、b 都是整数}',
    struct: '群',
    groupOp: '+',
    note: '(ℤ², +) 是群：整数向量相加还是整数向量，(0, 0) 是单位元，(a, b) 的逆元是 (−a, −b)。像一张方格纸上的所有格点。',
    desc: '两个分量都是整数的向量。',
    hint: '从四个方向出发，用加法反复组合。',
    has: v => isVec(v) && v.xs.every(isInt),
    recipes: [
      ['d:Cross', 'm:closure', 'b:add'],
      ['d:Cross', 'm:closure', 'b:sub'],
    ],
  },
  {
    id: 'Plane',
    short: 'ℚ²',
    name: '平面',
    ch: 7,
    type: 'vec',
    preview: '{(a, b)：a、b 是有理数}',
    struct: '群',
    groupOp: '+',
    note: '(ℚ², +) 是群：向量相加还是向量，(0, 0) 是单位元，(a, b) 的逆元是 (−a, −b)。乘法（点积）得到的是数，不在里面，所以它对 × 谈不上是群。',
    desc: '全部二维向量。x 轴上取一个，y 轴上取一个，加起来就能到达平面上任何一点。',
    hint: 'x 轴和 y 轴两两相加；或者把整点格的每张卡都乘以有理数。',
    has: v => isVec(v),
    recipes: [
      ['d:Xaxis', 'b:add', 'd:Yaxis'],
      ['d:Lattice', 'b:mul', 'd:Q'],
      ['d:Q', 'b:mul', 'd:Lattice'],
      ['d:Lattice', 'b:div', 'd:Np'],
    ],
  },
  {
    id: 'Rot4',
    short: 'C₄',
    name: '旋转群',
    ch: 7,
    type: 'mat',
    preview: '{I, R, R², R³}，R = [0 −1; 1 0]',
    list: ['m:1,0,0,1', 'm:0,-1,1,0', 'm:-1,0,0,-1', 'm:0,1,-1,0'],
    struct: '群',
    groupOp: '×',
    note: '(C₄, ×) 是群：转 90° 的矩阵 R 自己乘自己，R² 转 180°，R³ 转 270°，R⁴ = I 回到原地。I 是单位元，R 的逆元是 R³。对 + 不封闭：I + I = 2I 跑出去了。',
    desc: '把平面转 0°、90°、180°、270° 的四个矩阵。',
    hint: '先造出 R = e₂ | (−e₁)，再用乘法封闭。',
    has: v => isMat(v) && ['m:1,0,0,1', 'm:0,-1,1,0', 'm:-1,0,0,-1', 'm:0,1,-1,0'].includes(keyM(v)),
    recipes: [
      ['c:m:0,-1,1,0', 'm:closure', 'b:mul'],
      ['c:m:0,-1,1,0', 'b:pow', 'd:Z'],
      ['d:Refl', 'b:mul', 'd:Refl'],
      ['c:m:0,-1,1,0', 'b:pow', 'd:N'],
    ],
  },
  {
    id: 'Refl',
    short: '反射',
    name: '四个反射',
    ch: 7,
    type: 'mat',
    preview: '{[1 0; 0 −1], [−1 0; 0 1], [0 1; 1 0], [0 −1; −1 0]}',
    list: ['m:1,0,0,-1', 'm:-1,0,0,1', 'm:0,1,1,0', 'm:0,-1,-1,0'],
    struct: '集合',
    note: '对 × 不封闭：两个反射乘起来是旋转，比如 [1 0; 0 −1] × [0 1; 1 0] = [0 1; −1 0] = R³。所以它不是群，但它和 C₄ 合起来就是群。',
    desc: '沿 x 轴、y 轴、对角线 y = x、y = −x 翻转平面的四个矩阵。每个自己乘自己都是 I。',
    hint: '让旋转群 C₄ 里的每个矩阵都乘以翻转 F = e₁ | (−e₂) = [1 0; 0 −1]。',
    has: v => isMat(v) && ['m:1,0,0,-1', 'm:-1,0,0,1', 'm:0,1,1,0', 'm:0,-1,-1,0'].includes(keyM(v)),
    recipes: [
      ['d:Rot4', 'b:mul', 'c:m:1,0,0,-1'],
      ['c:m:1,0,0,-1', 'b:mul', 'd:Rot4'],
      ['d:Rot4', 'b:mul', 'c:m:0,1,1,0'],
    ],
  },
  {
    id: 'Dih4',
    short: 'D₄',
    name: '二面体群',
    ch: 7,
    type: 'mat',
    preview: '{I, R, R², R³, F, FR, FR², FR³}',
    list: ['m:1,0,0,1', 'm:0,-1,1,0', 'm:-1,0,0,-1', 'm:0,1,-1,0', 'm:1,0,0,-1', 'm:-1,0,0,1', 'm:0,1,1,0', 'm:0,-1,-1,0'],
    struct: '群',
    groupOp: '×',
    note: '(D₄, ×) 是群：四个旋转加四个反射，一共 8 张卡，正方形所有的对称。它不是交换的：R × F 和 F × R 不一样。这是你遇到的第一个不交换的群。',
    desc: '把一个正方形变回它自己的全部 8 种方式。',
    hint: '旋转群和四个反射取「并」；或者从四个反射出发用乘法封闭。',
    has: v =>
      isMat(v) &&
      ['m:1,0,0,1', 'm:0,-1,1,0', 'm:-1,0,0,-1', 'm:0,1,-1,0', 'm:1,0,0,-1', 'm:-1,0,0,1', 'm:0,1,1,0', 'm:0,-1,-1,0'].includes(keyM(v)),
    recipes: [
      ['d:Rot4', 'm:union', 'd:Refl'],
      ['d:Refl', 'm:closure', 'b:mul'],
      ['d:Refl', 'm:union', 'd:Rot4'],
    ],
  },
  {
    id: 'Diag',
    short: '对角',
    name: '对角矩阵',
    ch: 7,
    type: 'mat',
    preview: '{[a 0; 0 b]}',
    struct: '群',
    groupOp: '+',
    note: '(对角矩阵, +) 是群：角上的 0 加起来还是 0，零矩阵是单位元。对 × 也封闭，但 [1 0; 0 0] 没有逆，所以对 × 不是群。',
    desc: '只有对角线上有数的矩阵。它把 x 方向拉伸 a 倍、y 方向拉伸 b 倍。',
    hint: 'x 轴上取一个向量、y 轴上取一个向量，拼接起来。',
    has: v => isMat(v) && isZeroR(v.m[0][1]) && isZeroR(v.m[1][0]),
    recipes: [
      ['d:Xaxis', 'b:cat', 'd:Yaxis'],
      ['d:Anti', 'b:mul', 'c:m:0,-1,1,0'],
      ['c:m:0,-1,1,0', 'b:mul', 'd:Anti'],
    ],
  },
  {
    id: 'Anti',
    short: '反对角',
    name: '反对角矩阵',
    ch: 7,
    type: 'mat',
    preview: '{[0 a; b 0]}',
    struct: '群',
    groupOp: '+',
    note: '(反对角矩阵, +) 是群，和对角矩阵一样。对 × 不封闭：两个反对角矩阵乘起来变成对角矩阵。',
    desc: '只有另一条对角线上有数的矩阵。它把 x 和 y 对调，再各自拉伸。',
    hint: 'y 轴上取一个向量、x 轴上取一个向量，拼接起来；或者把对角矩阵乘以旋转 R，两列就换了位置。',
    has: v => isMat(v) && isZeroR(v.m[0][0]) && isZeroR(v.m[1][1]),
    recipes: [
      ['d:Yaxis', 'b:cat', 'd:Xaxis'],
      ['d:Diag', 'b:mul', 'c:m:0,-1,1,0'],
      ['c:m:0,-1,1,0', 'b:mul', 'd:Diag'],
    ],
  },
  {
    id: 'Scalar',
    short: 'ℚ·I',
    name: '标量矩阵',
    ch: 7,
    type: 'mat',
    preview: '{a·I}：I、−I、2I、I/2、…',
    struct: '群',
    groupOp: '+',
    note: '(ℚ·I, +) 是群：aI + bI = (a + b)I。它就是把 ℚ 装进矩阵里：aI 乘任何矩阵都只是放大 a 倍。',
    desc: '单位矩阵的全部倍数。',
    hint: '让 ℚ 里的每个数都乘以 I = e₁ | e₂。',
    has: v => isMat(v) && isZeroR(v.m[0][1]) && isZeroR(v.m[1][0]) && eq(v.m[0][0], v.m[1][1]),
    recipes: [
      ['d:Q', 'b:mul', 'c:m:1,0,0,1'],
      ['c:m:1,0,0,1', 'b:mul', 'd:Q'],
      ['d:Q', 'b:mul', 'c:m:-1,0,0,-1'],
    ],
  },
  {
    id: 'Mat2',
    short: 'M₂',
    name: '全体矩阵',
    ch: 7,
    type: 'mat',
    preview: '{[a b; c d]：a、b、c、d 是有理数}',
    struct: '群',
    groupOp: '+',
    note: '(M₂, +) 是群：零矩阵是单位元，每个矩阵取反就是逆元。对 × 不是群：[1 0; 0 0] 没有逆矩阵。',
    desc: '所有 2×2 矩阵。平面上任取两个向量并排，就是一个矩阵。',
    hint: '平面 ℚ² 和它自己两两拼接。',
    has: v => isMat(v),
    recipes: [
      ['d:Plane', 'b:cat', 'd:Plane'],
      ['d:Diag', 'b:add', 'd:Anti'],
      ['d:Anti', 'b:add', 'd:Diag'],
    ],
  },
  {
    id: 'GL2',
    short: 'GL₂',
    name: '可逆矩阵',
    ch: 7,
    type: 'mat',
    preview: '{行列式不是 0 的矩阵}',
    struct: '群',
    groupOp: '×',
    note: '(GL₂, ×) 是群：可逆乘可逆还是可逆，I 是单位元，每个矩阵的逆元就是它的逆矩阵。对 + 不封闭：I + (−I) = 0 不可逆。',
    desc: '有逆矩阵的矩阵，也就是行列式不为 0 的矩阵。它们做的变换都能撤销。',
    hint: '让 M₂ 里的每个矩阵都做 1/x。没有逆矩阵的会被跳过。',
    has: v => isMat(v) && !isZeroR(det(v)),
    recipes: [
      ['d:Mat2', 'u:recip', null],
      ['d:Mat2', 'b:pow', 'c:-1'],
      ['c:m:1,0,0,1', 'b:div', 'd:Mat2'],
    ],
  },
];

export const QUESTS = [
  {
    id: 'lin1',
    ch: 7,
    title: '拼出单位矩阵',
    text: '左边放 e₁ = (1, 0)，中间放「拼接」，右边放 e₂ = (0, 1)。两个向量并排，就是单位矩阵 I。',
    done: has => has('c:m:1,0,0,1'),
  },
  {
    id: 'lin2',
    ch: 7,
    title: '转一圈',
    text: '先用 −1 × e₁ 造出 (−1, 0)，拼成 R = e₂ | (−e₁) = [0 −1; 1 0]。让 R 在 × 下封闭，看看转几次回到原地。',
    done: has => has('d:Rot4'),
  },
  {
    id: 'lin3',
    ch: 7,
    title: '集齐方向与变换',
    text: '打开图鉴看第 7 章。向量的卡组是平面上的线和网，矩阵的卡组是一群群变换。试试 M₂ 经 1/x，没有逆的矩阵会被跳过。',
    done: has => CATALOG.every(c => has(`d:${c.id}`)),
  },
];

// 从"集齐初等篇 + 本章赠卡（e₁、e₂、拼接、转置、行列式、迹）"出发，集齐本章全部卡组
export const WALKTHROUGH = [
  ['c:v:1,0', 'b:cat', 'c:v:0,1', 'c:m:1,0,0,1'],
  ['c:-1', 'b:mul', 'c:v:1,0', 'c:v:-1,0'],
  ['c:-1', 'b:mul', 'c:v:0,1', 'c:v:0,-1'],
  ['c:v:0,1', 'b:cat', 'c:v:-1,0', 'c:m:0,-1,1,0'],
  ['c:v:1,0', 'b:cat', 'c:v:0,-1', 'c:m:1,0,0,-1'],
  ['c:m:0,-1,1,0', 'm:closure', 'b:mul', 'd:Rot4'],
  ['d:Rot4', 'b:mul', 'c:v:1,0', 'd:Cross'],
  ['d:Cross', 'm:closure', 'b:add', 'd:Lattice'],
  ['d:Q', 'b:mul', 'c:v:1,0', 'd:Xaxis'],
  ['d:Q', 'b:mul', 'c:v:0,1', 'd:Yaxis'],
  ['d:Xaxis', 'b:add', 'd:Yaxis', 'd:Plane'],
  ['d:Rot4', 'b:mul', 'c:m:1,0,0,-1', 'd:Refl'],
  ['d:Rot4', 'm:union', 'd:Refl', 'd:Dih4'],
  ['d:Xaxis', 'b:cat', 'd:Yaxis', 'd:Diag'],
  ['d:Yaxis', 'b:cat', 'd:Xaxis', 'd:Anti'],
  ['d:Q', 'b:mul', 'c:m:1,0,0,1', 'd:Scalar'],
  ['d:Plane', 'b:cat', 'd:Plane', 'd:Mat2'],
  ['d:Mat2', 'u:pow(-1)', null, 'd:GL2'],
];
