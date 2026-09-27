// 第 8 章「以身为尺」：带量纲的量。
//
// 单卡类型 'qty'：{ t: 'qty', v, dim }，v 是有理数，dim = [L, T, M] 是三个有理数指数
//   （长度、时间、质量），允许分数（√面积 = 长度）。
// 基本单位是身体尺度：步（长度）、息（一次呼吸，时间）、捧（双手一捧，质量）。
// 无量纲的量不存在：运算结果三个指数全是 0 时直接返回有理数，所以 步 ÷ 步 = 1 回到初等篇的数。
//
//   key  "q:3|1,-1,0"     fmt  "3 步/息"     label  "速度"
//
// 运算：
//   + −   只在量纲相同时才行，否则 {err}
//   × ÷   量纲指数相加减；数 × 量、量 ÷ 数、数 ÷ 量都行
//   ^     量 ^ 有理数：指数乘上去，值用 rpow；开不出有理数就 {err}
//   量 + 数、量 ^ 量、取余：{err}

import { R, isR, ZERO, ONE, eq, add, sub, mul, div, cmp, rkey, fmtR, height, rpow, parseQKey, isInt, sup } from '../math.js';
import { registerType } from '../values.js';

// ───────────────────────── 值 ─────────────────────────

export const isQty = v => v !== null && typeof v === 'object' && v.t === 'qty';

// 写量纲：dim(1, -1, 0) 或 dim('1/2', 0, 0)
export const dim = (...xs) => xs.map(x => (typeof x === 'string' ? parseQKey(x) : R(x)));
export const dimKey = d => `${rkey(d[0])},${rkey(d[1])},${rkey(d[2])}`;
const isZeroDim = d => d[0].n === 0 && d[1].n === 0 && d[2].n === 0;
const sameDim = (a, b) => eq(a[0], b[0]) && eq(a[1], b[1]) && eq(a[2], b[2]);
const ZERO_DIM = [ZERO, ZERO, ZERO];

// 整理成值：v 不是有理数（OVER、null）就原样返回；无量纲就返回有理数本身
export function qty(v, d) {
  if (!isR(v)) return v;
  if (isZeroDim(d)) return v;
  return { t: 'qty', v, dim: d };
}

// 小整数指数用现成的对象，封闭时省掉反复分配
const INTS = Array.from({ length: 65 }, (_, i) => R(i - 32));
const RI = n => (n >= -32 && n <= 32 ? INTS[n + 32] : R(n));

// 两个量纲逐项相加（sign = 1）或相减（sign = −1）。指数溢出时返回 null（不会发生，只是稳妥）
function dimOp(sign, a, b) {
  const d = new Array(3);
  for (let i = 0; i < 3; i++) {
    const x = a[i];
    const y = b[i];
    const e = x.d === 1 && y.d === 1 ? RI(x.n + sign * y.n) : sign > 0 ? add(x, y) : sub(x, y);
    if (!isR(e)) return null;
    d[i] = e;
  }
  return d;
}

// 常用写法：Q(3, 1, -1, 0) = 3 步/息
export const Q = (v, l, t, m) => qty(typeof v === 'string' ? parseQKey(v) : R(v), dim(l, t, m));

// ───────────────────────── 量纲的名字 ─────────────────────────

// 图鉴里的量纲类，按这个顺序排序、显示
export const DIMS = [
  { id: 'Len', name: '长度', d: dim(1, 0, 0) },
  { id: 'Time', name: '时间', d: dim(0, 1, 0) },
  { id: 'Mass', name: '质量', d: dim(0, 0, 1) },
  { id: 'Area', name: '面积', d: dim(2, 0, 0) },
  { id: 'Vol', name: '体积', d: dim(3, 0, 0) },
  { id: 'Vel', name: '速度', d: dim(1, -1, 0) },
  { id: 'Acc', name: '加速度', d: dim(1, -2, 0) },
  { id: 'Freq', name: '频率', d: dim(0, -1, 0) },
  { id: 'Force', name: '力', d: dim(1, -2, 1) },
  { id: 'Energy', name: '能量', d: dim(2, -2, 1) },
  { id: 'Power', name: '功率', d: dim(2, -3, 1) },
];

// 认得出名字、但图鉴里没有的量纲
const MORE_NAMES = [
  ['动量', dim(1, -1, 1)],
  ['密度', dim(-3, 0, 1)],
  ['压强', dim(-1, -2, 1)],
];

const DIM_NAMES = new Map([...DIMS.map(x => [dimKey(x.d), x.name]), ...MORE_NAMES.map(([n, d]) => [dimKey(d), n])]);
const DIM_ORDER = new Map(DIMS.map((x, i) => [dimKey(x.d), i]));

// 量纲的名字：长度、速度、力……认不出的写 "量"
export const dimName = v => DIM_NAMES.get(dimKey(v.dim)) ?? '量';

// 固定值单卡：用身体量出来的老单位
export const NAMED_VALUES = [
  { name: '拃', key: 'q:1/5|1,0,0', text: '张开手掌，拇指尖到中指尖的距离，五拃是一步' },
  { name: '庹', key: 'q:2|1,0,0', text: '两臂平伸的长度，两步' },
  { name: '里', key: 'q:300|1,0,0', text: '三百步' },
  { name: '刻', key: 'q:200|0,1,0', text: '两百次呼吸' },
  { name: '日', key: 'q:20000|0,1,0', text: '一百刻，两万次呼吸' },
  { name: '石', key: 'q:120|0,0,1', text: '一百二十捧' },
];
const NAMED_BY_KEY = new Map(NAMED_VALUES.map(x => [x.key, x.name]));

// ───────────────────────── 显示 ─────────────────────────

const UNIT_ORDER = [
  [2, '捧'],
  [0, '步'],
  [1, '息'],
];

const expStr = e => (eq(e, ONE) ? '' : isInt(e) ? sup(e.n) : `^(${fmtR(e)})`);

// 单位的写法："步"、"步²"、"捧·步/息²"、"1/息"、"步^(1/2)"
export function fmtUnit(d) {
  const num = [];
  const den = [];
  for (const [i, name] of UNIT_ORDER) {
    const e = d[i];
    if (e.n === 0) continue;
    const a = e.n < 0 ? R(-e.n, e.d) : e;
    (e.n > 0 ? num : den).push(`${name}${expStr(a)}`);
  }
  let s = num.join('·');
  if (den.length) s = `${s || '1'}/${den.length > 1 ? `(${den.join('·')})` : den[0]}`;
  return s;
}

export function fmtQty(v) {
  const u = fmtUnit(v.dim);
  if (u.startsWith('1/')) {
    const body = u.slice(2);
    return isInt(v.v) ? `${fmtR(v.v)}/${body}` : `(${fmtR(v.v)})/${body}`;
  }
  return `${fmtR(v.v)} ${u}`;
}

// 说明一个量是什么："长度"，或者认不出名字时 "单位是 步·息 的量"
const describe = v => {
  const n = dimName(v);
  return n === '量' ? `单位是 ${fmtUnit(v.dim)} 的量` : n;
};

export const keyQty = v => `q:${rkey(v.v)}|${dimKey(v.dim)}`;

const KEY_RE = /^q:(-?\d+(?:\/\d+)?)\|(-?\d+(?:\/\d+)?),(-?\d+(?:\/\d+)?),(-?\d+(?:\/\d+)?)$/;

export function parseQtyKey(s) {
  const m = typeof s === 'string' ? KEY_RE.exec(s) : null;
  if (!m) return null;
  const v = parseQKey(m[1]);
  const d = [m[2], m[3], m[4]].map(parseQKey);
  if (!v || d.some(e => e === null) || isZeroDim(d)) return null;
  return { t: 'qty', v, dim: d };
}

// ───────────────────────── 运算 ─────────────────────────

const VERB = { add: '相加', sub: '相减' };

function qtyBin(op, x, y) {
  const qx = isQty(x);
  const qy = isQty(y);
  if (!qx && !qy) return undefined;
  // 另一边既不是数也不是量：交给别的类型处理
  if (!(qx || isR(x)) || !(qy || isR(y))) return undefined;
  switch (op) {
    case 'add':
    case 'sub': {
      if (!qx || !qy) {
        const [q, r] = qx ? [x, y] : [y, x];
        return { err: `${fmtQty(q)} 是${describe(q)}，${fmtR(r)} 只是一个数，没有单位，两者不能${VERB[op]}。` };
      }
      if (!sameDim(x.dim, y.dim)) {
        return { err: `${describe(x)}和${describe(y)}不能${VERB[op]}：${fmtQty(x)} 和 ${fmtQty(y)} 的单位不一样，合不到一起。` };
      }
      return qty((op === 'add' ? add : sub)(x.v, y.v), x.dim);
    }
    case 'mul': {
      // 数 × 量、量 × 数：量纲照抄
      if (!qx) return qty(mul(x, y.v), y.dim);
      if (!qy) return qty(mul(x.v, y), x.dim);
      const d = dimOp(1, x.dim, y.dim);
      return d ? qty(mul(x.v, y.v), d) : null;
    }
    case 'div': {
      const vy = qy ? y.v : y;
      if (vy.n === 0) return { err: '不能除以 0。' };
      if (!qy) return qty(div(x.v, y), x.dim);
      const d = dimOp(-1, qx ? x.dim : ZERO_DIM, y.dim);
      return d ? qty(div(qx ? x.v : x, vy), d) : null;
    }
    case 'pow': {
      if (qy) return { err: `指数不能带单位：${fmtQty(y)} 次方没有意义。指数得是一个数。` };
      const e = y;
      if (e.d > 12) return { err: '指数的分母太大了。' };
      const v = rpow(x.v, e);
      if (v === null) {
        if (x.v.n === 0) return { err: '0 的 0 次方、0 的负数次方都没有定义。' };
        return { err: `${fmtQty(x)} 的 ${fmtR(e)} 次方开不出来：${fmtR(x.v)} 的 ${e.d} 次方根不是有理数。` };
      }
      return qty(v, x.dim.map(d => mul(d, e)));
    }
    case 'mod':
      return { err: `取余只对整数做，${fmtQty(qx ? x : y)} 带着单位，做不了。` };
  }
  return undefined;
}

// ───────────────────────── 视野与探针 ─────────────────────────

// 每个量纲类在视野里的值。1～12 和 1/2～1/6 都有，这样 长度 ÷ 长度 能凑出 ℚ⁺ 的每一个小探针
const VALS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '1/2', '1/3', '1/4', '1/5', '1/6'].map(parseQKey);
// 图鉴外的量纲只放几个值，让自造的卡组也能预览
const VALS_SMALL = ['1', '2', '3', '1/2'].map(parseQKey);
const EXTRA_DIMS = [
  dim(1, -1, 1), // 动量
  dim(-3, 0, 1), // 密度
  dim(-1, -2, 1), // 压强
  dim(0, 2, 0), // 时间²
  dim(2, -2, 0), // 速度²
  dim(-1, 0, 0), // 1/长度
  dim(0, 0, -1), // 1/质量
  dim(0, -2, 0), // 频率²
  dim(2, -1, 0), // 面积/时间
  dim('1/2', 0, 0), // √长度
];

export const WINDOW_Q = [
  ...DIMS.flatMap(x => VALS.map(v => qty(v, x.d))),
  ...EXTRA_DIMS.flatMap(d => VALS_SMALL.map(v => qty(v, d))),
];

// 探针：每个量纲类三个值。面积用平方数、体积用立方数，这样 长度 经 x²、长度 经 x³ 也认得出来
const PROBE_VALS = { Area: ['1', '4', '1/4'], Vol: ['1', '8', '1/8'] };
export const PROBES_SMALL_Q = DIMS.flatMap(x => (PROBE_VALS[x.id] ?? ['1', '2', '1/2']).map(s => qty(parseQKey(s), x.d)));

// 大探针：精确卡组再多比对几个视野外的值。面积只放平方数、体积只放立方数；
// 长度的值立方之后也不能超过一千万，不然 体积 经 ∛x 这种做法会在探针上溢出
const PROBE_MORE = {
  Len: ['100', '1/5', '1/12', '210'],
  Time: ['200', '2000', '1/200'],
  Mass: ['120', '1/120'],
  Area: ['9', '1/9', '100', '2500'],
  Vol: ['27', '1/27', '1000'],
  Vel: ['300', '1/200'],
  Acc: ['3', '1/4'],
  Freq: ['1/200', '1/20000'],
  Force: ['4', '1/4'],
  Energy: ['3', '9'],
  Power: ['3', '1/3'],
};
export const PROBES_Q = [...PROBES_SMALL_Q, ...DIMS.flatMap(x => (PROBE_MORE[x.id] ?? []).map(s => qty(parseQKey(s), x.d)))];

// 大小 = 值的高度 + 2 × 指数绝对值之和。指数也算进去，封闭时量纲才不会一直长。
// 上限 14：8 步³（体积的探针）是 8 + 6，2 捧·步²/息³（功率的探针）是 2 + 12，刚好都留得下；
// 再大，"长度 在 ÷ 下封闭" 这种会算出几千张卡，慢
const absExp = e => (e.d === 1 ? (e.n < 0 ? -e.n : e.n) : Math.abs(e.n / e.d));
const totalExp = d => absExp(d[0]) + absExp(d[1]) + absExp(d[2]);
export const sizeQty = v => height(v.v) + 2 * totalExp(v.dim);
export const SIZE_CAP = 14;

function cmpQty(a, b) {
  const ia = DIM_ORDER.get(dimKey(a.dim)) ?? DIMS.length;
  const ib = DIM_ORDER.get(dimKey(b.dim)) ?? DIMS.length;
  if (ia !== ib) return ia - ib;
  for (let i = 0; i < 3; i++) {
    const c = cmp(a.dim[i], b.dim[i]);
    if (c !== 0) return c;
  }
  return cmp(a.v, b.v);
}

registerType({
  t: 'qty',
  name: '量',
  label(v) {
    const n = dimName(v);
    const named = NAMED_BY_KEY.get(keyQty(v));
    return named ? `${n}（1 ${named}）` : n;
  },
  key: keyQty,
  parseKey: parseQtyKey,
  fmt: fmtQty,
  size: sizeQty,
  cmp: cmpQty,
  window: WINDOW_Q,
  probes: PROBES_Q,
  probesSmall: PROBES_SMALL_Q,
  sizeCap: SIZE_CAP,
  bin: qtyBin,
});

// ───────────────────────── 章节内容 ─────────────────────────

const c = key => `c:${key}`;
const STEP = 'q:1|1,0,0';
const BREATH = 'q:1|0,1,0';
const HANDFUL = 'q:1|0,0,1';

export const CHAPTER = {
  id: 8,
  title: '以身为尺',
  desc: '用步子、呼吸和双手丈量世界。',
  intro:
    '还没有尺子的时候，人就用自己量世界。走多远，数步子；等多久，数呼吸；有多少，看双手能捧几回。步、息、捧，是从身体里长出来的单位。' +
    '后来有人把一块田的长和宽都走了一遍，把两个步数乘起来，发现得到的东西不再是步数：它是田的大小。步数除以呼吸数，是快慢。' +
    '长度乘长度，是另一种东西。人们给这"另一种东西"记账，就有了量纲。' +
    '这一章的卡都带着单位。加减只能在同类之间做，乘除却会变出新的种类。有一个彩蛋：步 ÷ 步 回到没有单位的数，长度 ÷ 长度 就是 ℚ⁺。',
  unlock: {
    when: 'd:Qp',
    gives: [c(STEP), c(BREATH), c(HANDFUL), ...NAMED_VALUES.map(x => c(x.key))],
    note:
      '有了正有理数，就能给数配上单位。赠卡里除了 1 步、1 息、1 捧，还有几个老单位：1/5 步是拃（张开手掌的宽），2 步是庹（两臂平伸），300 步是里；200 息是刻，20000 息是日（一日百刻）；120 捧是石。数值是这个游戏里定的，古人各地各有各的算法。',
  },
};

export const NAMED_UN = [];

export const BIN_INFO = {};

// 一个量纲类的图鉴条目
function entry(id, extra) {
  const x = DIMS.find(d => d.id === id);
  const key = dimKey(x.d);
  const few = ['1/2', '1', '2', '3'].map(s => fmtQty(qty(parseQKey(s), x.d)));
  return {
    id,
    short: x.name,
    name: x.name,
    ch: 8,
    type: 'qty',
    preview: `{…, ${few.join(', ')}, …}`,
    struct: '群',
    groupOp: '+',
    // 引擎有时会把别的类型的值（比如 步 ÷ 步 得到的数）送进来，先挡掉
    has: v => isQty(v) && dimKey(v.dim) === key,
    ...extra,
  };
}

export const CATALOG = [
  entry('Len', {
    note: '(长度, +) 是群：步数加步数还是步数，0 步是单位元，3 步的逆元是往回走的 −3 步。对 × 不封闭：步 × 步 = 步²，跑到面积去了。',
    desc: '所有能用步子量出来的量：3 步、1/2 步、300 步。',
    hint: '把正有理数 ℚ⁺ 里的每个数都乘上 1 步。',
    recipes: [
      ['d:Qp', 'b:mul', c(STEP)],
      ['d:Vel', 'b:mul', 'd:Time'],
      ['d:Area', 'u:sqrt', null],
      ['d:Vol', 'b:div', 'd:Area'],
    ],
  }),
  entry('Time', {
    note: '(时间, +) 是群：等了 3 息再等 2 息就是 5 息，0 息是单位元。时间 × 时间 是 息²，那不是时间。',
    desc: '用呼吸数出来的量：1 息、200 息（一刻）、20000 息（一日）。',
    hint: '把 ℚ⁺ 乘上 1 息；或者把频率倒过来。',
    recipes: [
      ['d:Qp', 'b:mul', c(BREATH)],
      ['d:Len', 'b:div', 'd:Vel'],
      ['d:Freq', 'u:recip', null],
      ['d:Qp', 'b:div', 'd:Freq'],
    ],
  }),
  entry('Mass', {
    note: '(质量, +) 是群：两捧加一捧是三捧，0 捧是单位元。质量 × 质量 是 捧²，没人见过那种东西。',
    desc: '用双手捧出来的量：1 捧、120 捧（一石）。',
    hint: '把 ℚ⁺ 乘上 1 捧；或者用力 ÷ 加速度。',
    recipes: [
      ['d:Qp', 'b:mul', c(HANDFUL)],
      ['d:Force', 'b:div', 'd:Acc'],
      [c(HANDFUL), 'b:mul', 'd:Qp'],
    ],
  }),
  entry('Area', {
    note: '(面积, +) 是群：两块田拼在一起还是田，0 步² 是单位元。它是长度 × 长度，单位是 步²。',
    desc: '一块田有多大：长的步数乘宽的步数。',
    hint: '长度 × 长度，或者让长度里每张卡都做平方。',
    recipes: [
      ['d:Len', 'b:mul', 'd:Len'],
      ['d:Len', 'u:sq', null],
      ['d:Vol', 'b:div', 'd:Len'],
    ],
  }),
  entry('Vol', {
    note: '(体积, +) 是群，单位是 步³。面积再乘一个长度就到了这里。',
    desc: '一个坑有多深多大：面积再乘高。',
    hint: '面积 × 长度，或者让长度里每张卡都做立方。',
    recipes: [
      ['d:Area', 'b:mul', 'd:Len'],
      ['d:Len', 'u:cube', null],
      ['d:Len', 'b:mul', 'd:Area'],
    ],
  }),
  entry('Vel', {
    note: '(速度, +) 是群，单位是 步/息。它是长度 ÷ 时间：一息走几步。',
    desc: '走得多快：一次呼吸走了几步。',
    hint: '长度 ÷ 时间。',
    recipes: [
      ['d:Len', 'b:div', 'd:Time'],
      ['d:Acc', 'b:mul', 'd:Time'],
      ['d:Len', 'b:mul', 'd:Freq'],
    ],
  }),
  entry('Acc', {
    note: '(加速度, +) 是群，单位是 步/息²。速度再除一次时间：每一息快了多少。',
    desc: '越走越快时，快的那一部分。',
    hint: '速度 ÷ 时间。',
    recipes: [
      ['d:Vel', 'b:div', 'd:Time'],
      ['d:Force', 'b:div', 'd:Mass'],
      ['d:Vel', 'b:mul', 'd:Freq'],
    ],
  }),
  entry('Freq', {
    note: '(频率, +) 是群，单位是 1/息。时间倒过来就是它：一息里发生几次。',
    desc: '心跳一息几下：每次呼吸里发生的次数。',
    hint: '让时间里每张卡都做 1/x。',
    recipes: [
      ['d:Time', 'u:recip', null],
      ['d:Qp', 'b:div', 'd:Time'],
      ['d:Vel', 'b:div', 'd:Len'],
    ],
  }),
  entry('Force', {
    note: '(力, +) 是群，单位是 捧·步/息²。质量 × 加速度：推一捧东西让它越走越快，要用多大的劲。',
    desc: '推东西要用的劲。',
    hint: '质量 × 加速度。',
    recipes: [
      ['d:Mass', 'b:mul', 'd:Acc'],
      ['d:Energy', 'b:div', 'd:Len'],
    ],
  }),
  entry('Energy', {
    note: '(能量, +) 是群，单位是 捧·步²/息²。力 × 长度：用这么大的劲推了这么远。',
    desc: '用了多少劲、推了多远，两样乘起来。',
    hint: '力 × 长度。',
    recipes: [
      ['d:Force', 'b:mul', 'd:Len'],
      ['d:Power', 'b:mul', 'd:Time'],
    ],
  }),
  entry('Power', {
    note: '(功率, +) 是群，单位是 捧·步²/息³。能量 ÷ 时间：一息之内花掉多少能量。',
    desc: '干活有多快：一息之内做了多少。',
    hint: '能量 ÷ 时间，或者力 × 速度。',
    recipes: [
      ['d:Energy', 'b:div', 'd:Time'],
      ['d:Force', 'b:mul', 'd:Vel'],
    ],
  }),
];

export const QUESTS = [
  {
    id: 'qty1',
    title: '一里有几步',
    text: '赠卡里有 300 步（一里）和 1 步。左边放 300 步，中间放「除法」，右边放 1 步：单位约掉，只剩一个数。',
    done: has => has('c:300'),
  },
  {
    id: 'qty2',
    title: '长度乘长度',
    text: '先把 ℚ⁺ 乘上 1 步，得到「长度」。再让长度 × 长度，看看得到的是什么。',
    done: has => has('d:Area'),
  },
  {
    id: 'qty3',
    title: '集齐量纲',
    text: '打开图鉴，把第八章的卡组都造出来。每一种都是别的量纲乘或除出来的。',
    done: has => CATALOG.every(c => has(`d:${c.id}`)),
  },
];

// 从"集齐初等篇 + 本章赠卡（步、息、捧和几个老单位）"出发，集齐本章全部卡组
export const WALKTHROUGH = [
  [c('q:300|1,0,0'), 'b:div', c(STEP), 'c:300'],
  [c(STEP), 'b:mul', c(STEP), c('q:1|2,0,0')],
  ['d:Qp', 'b:mul', c(STEP), 'd:Len'],
  ['d:Qp', 'b:mul', c(BREATH), 'd:Time'],
  ['d:Qp', 'b:mul', c(HANDFUL), 'd:Mass'],
  ['d:Len', 'b:mul', 'd:Len', 'd:Area'],
  ['d:Area', 'b:mul', 'd:Len', 'd:Vol'],
  ['d:Len', 'b:div', 'd:Time', 'd:Vel'],
  ['d:Vel', 'b:div', 'd:Time', 'd:Acc'],
  ['d:Time', 'u:pow(-1)', null, 'd:Freq'],
  ['d:Mass', 'b:mul', 'd:Acc', 'd:Force'],
  ['d:Force', 'b:mul', 'd:Len', 'd:Energy'],
  ['d:Energy', 'b:div', 'd:Time', 'd:Power'],
];
