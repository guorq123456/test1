// 第 5 章「时钟与余数」：模运算与有限群。
//
// 单卡类型 'mod'：余数类 {t: 'mod', n, r}，表示"除以 n 余 r"，0 ≤ r < n，n ≥ 2。
//   key  "[3]12"      fmt  "[3]₁₂"      sub  "mod:12"
// 同一个 n 的余数才在同一个钟面上，不同 n 之间不能运算。
//
// 运算：
//   整数 mod 整数  → 余数（registerBin，两边都是有理数时由它接手）
//   余数 ± × 余数  → 余数（同一个 n）
//   余数 ÷ 余数    → 乘以逆元；没有逆元就报错
//   余数 ^ 整数    → 反复相乘；负指数先取逆元
//   余数 和 整数 混合 → 整数先化成同一个 n 的余数
//   余数 和 别的类型（量、向量、多项式……）→ 本类型不处理（返回 undefined），交给别的类型
//   余数 mod m     → 只有 m 整除 n 时才有意义：[r]n → [r mod m]m
//
// 出错时返回 { err, reason }，reason 的三类见 docs/v03-step1.md 第 2 节。

import { isR, isInt, gcd, fmtR, subscript } from '../math.js';
import { registerType, registerBin } from '../values.js';

// ───────────────────────── 余数类 ─────────────────────────

export const M = (n, r) => ({ t: 'mod', n, r: ((r % n) + n) % n });
export const isMod = v => v !== null && typeof v === 'object' && v.t === 'mod';
const eqMod = (a, b) => a.n === b.n && a.r === b.r;

// 视野最多列出这么多个余数（n 再大就只列前面一段）
const WINDOW_MAX = 200;
const residues = n => Array.from({ length: Math.min(n, WINDOW_MAX) }, (_, r) => M(n, r));
const nOfSub = sub => {
  const n = Number(String(sub).split(':')[1]);
  return Number.isInteger(n) && n >= 2 ? n : 12;
};

// 扩展欧几里得：返回 a 在模 n 下的逆元，没有就返回 null
export function modInv(a, n) {
  let [r0, r1] = [n, ((a % n) + n) % n];
  let [s0, s1] = [0, 1];
  while (r1 !== 0) {
    const q = Math.floor(r0 / r1);
    [r0, r1] = [r1, r0 - q * r1];
    [s0, s1] = [s1, s0 - q * s1];
  }
  if (r0 !== 1) return null;
  return ((s0 % n) + n) % n;
}

// 快速幂：a^k mod n，k ≥ 0。r < n ≤ 1e7，r·r < 1e14，不会丢精度
function modPow(a, k, n) {
  let base = a % n;
  let out = 1 % n;
  while (k > 0) {
    if (k & 1) out = (out * base) % n;
    base = (base * base) % n;
    k = Math.floor(k / 2);
  }
  return out;
}

const fmtMod = v => `[${v.r}]${subscript(v.n)}`;

// 把一个操作数（余数或有理数，modBin 已经排除了别的类型）化成模 n 的余数；化不了就返回 {err}。
// 分数化不成余数算"表示不了"：余数和整数之间有这条法，只是分数走不通；更大的世界
// （比如有理数的钟面 ℚ/nℤ）里 [3]₁₂ + 1/2 是有结果的
function toMod(v, n) {
  if (isMod(v)) return v;
  if (!isInt(v)) return { err: `${fmtR(v)} 不是整数，没法化成模 ${n} 的余数。`, reason: 'unrepresentable' };
  return M(n, v.n);
}

// 模数不是不小于 2 的整数：对 0 取余和除以 0 一样没有定义；对 1、负数、分数取余数学上有结果
// （ℤ₁、ℤ/3ℤ、ℚ/½ℤ），只是钟面写不出来
const badModulus = y => (y.n === 0 ? 'undefined' : 'unrepresentable');

const ERR_NO_INV = (b, g) =>
  b.r === 0
    ? `不能除以 ${fmtMod(b)}：它和 0 一样，没有倒数。`
    : `${fmtMod(b)} 没有逆元：${b.r} 和 ${b.n} 的最大公约数是 ${g}，不是 1，所以除不动。`;

function modBin(op, x, y) {
  const xm = isMod(x);
  const ym = isMod(y);
  if (!xm && !ym) return undefined;
  if (op === 'cat') return undefined;
  // 另一边既不是余数也不是有理数（量、向量、多项式……）：交给别的类型处理，
  // 不要把它说成"不是整数"
  if (!(xm || isR(x)) || !(ym || isR(y))) return undefined;

  if (op === 'mod') {
    if (xm && ym) return { err: `${fmtMod(x)} 已经是余数了，不能再对余数取余。`, reason: 'type' };
    if (!xm) return { err: `取余的模数要是普通的整数，${fmtMod(y)} 是余数，不行。`, reason: 'type' };
    if (!isInt(y) || y.n < 2) return { err: `取余的模数要是不小于 2 的整数，${fmtR(y)} 不行。`, reason: badModulus(y) };
    if (x.n % y.n !== 0) {
      return {
        err: `模 ${x.n} 的余数只能再对 ${x.n} 的约数取余：${fmtMod(x)} 说不清是 ${x.r} 还是 ${x.r + x.n}，对 ${y.n} 取余会得到不同的结果。`,
        reason: 'undefined',
      };
    }
    return M(y.n, x.r);
  }

  if (op === 'pow') {
    if (ym) {
      return {
        err: `指数要是普通的整数：${fmtMod(y)} 说不清是 ${y.r} 次、${y.r + y.n} 次还是 ${y.r + 2 * y.n} 次。`,
        reason: 'type',
      };
    }
    if (!isInt(y)) return { err: `余数的指数要是整数，${fmtR(y)} 不行。`, reason: 'unrepresentable' };
    const k = y.n;
    if (k >= 0) return M(x.n, modPow(x.r, k, x.n));
    const inv = modInv(x.r, x.n);
    if (inv === null) return { err: ERR_NO_INV(x, gcd(x.r, x.n)), reason: 'undefined' };
    return M(x.n, modPow(inv, -k, x.n));
  }

  if (xm && ym && x.n !== y.n) {
    return {
      err: `${fmtMod(x)} 和 ${fmtMod(y)} 不在同一个钟面上（一个模 ${x.n}，一个模 ${y.n}），不能一起算。`,
      reason: 'type',
    };
  }
  const n = xm ? x.n : y.n;
  const a = toMod(x, n);
  if (a.err) return a;
  const b = toMod(y, n);
  if (b.err) return b;
  switch (op) {
    case 'add':
      return M(n, a.r + b.r);
    case 'sub':
      return M(n, a.r - b.r);
    case 'mul':
      return M(n, a.r * b.r);
    case 'div': {
      const inv = modInv(b.r, n);
      if (inv === null) return { err: ERR_NO_INV(b, gcd(b.r, n)), reason: 'undefined' };
      return M(n, a.r * inv);
    }
  }
  return undefined;
}

registerType({
  t: 'mod',
  name: '余数',
  label: v => `模 ${v.n}`,
  // 模 n 的余数只有 n 个，视野就是全部：在视野里算出来的结果是精确的
  exhaustive: () => true,
  key: v => `[${v.r}]${v.n}`,
  parseKey(s) {
    const m = /^\[(\d+)\](\d+)$/.exec(s);
    if (!m) return null;
    const r = Number(m[1]);
    const n = Number(m[2]);
    if (!Number.isSafeInteger(n) || n < 2 || r >= n) return null;
    return M(n, r);
  },
  fmt: fmtMod,
  size: () => 1,
  cmp: (a, b) => a.n - b.n || a.r - b.r,
  sub: v => `mod:${v.n}`,
  window: residues(12),
  windowFor: sub => residues(nOfSub(sub)),
  probes: residues(12),
  probesFor: sub => residues(nOfSub(sub)),
  bin: modBin,
});

// 整数 mod 整数 → 余数。两边都是有理数时，'q' 类型不处理 mod，这里接手。
registerBin((op, x, y) => {
  if (op !== 'mod' || !isR(x) || !isR(y)) return undefined;
  if (!isInt(y) || y.n < 2) return { err: `取余的模数要是不小于 2 的整数，${fmtR(y)} 不行。`, reason: badModulus(y) };
  // 分数取余：更大的世界（ℚ/nℤ）里 1/2 mod 5 = 1/2，只是钟面写不出来
  if (!isInt(x)) return { err: `${fmtR(x)} 不是整数，取余只对整数做。`, reason: 'unrepresentable' };
  return M(y.n, x.n);
});

// ───────────────────────── 章节内容 ─────────────────────────

export const CHAPTER = {
  id: 5,
  title: '时钟与余数',
  desc: '数到 12 就回到 0。',
  intro:
    '钟面上 11 点再过 3 小时是 2 点，不是 14 点。把整数按"除以 n 的余数"分成 n 类，就得到一种转圈的算术：卡不多，加减乘照样做，有时连除法也行。这一章的卡组都是有限的，是不是群一眼就能数出来。',
  unlock: {
    when: 'd:Z',
    gives: ['b:mod', 'c:12', 'c:7'],
    note: '有了整数，就可以对它取余了。取余也能由减法「延展」得到：反复减去（负数就反复加上）同一个数，直到落在 0 到它减 1 之间，剩下的就是余数。',
  },
};

export const NAMED_UN = [];

export const BIN_INFO = {
  mod: {
    desc: '反复减去（负数就反复加上）同一个数，直到落在 0 到它减 1 之间，剩下的就是余数：17 mod 5 = 2，−17 mod 5 = 3。整数 mod n 得到"模 n 的余数"，同一个 n 的余数可以互相加减乘。',
  },
};

const keysOf = (n, rs) => rs.map(r => `[${r}]${n}`);
const inSet = (n, rs) => v => v.n === n && rs.includes(v.r);

export const CATALOG = [
  {
    id: 'Z12',
    short: 'ℤ₁₂',
    name: '时钟',
    ch: 5,
    type: 'mod:12',
    preview: '{[0]₁₂, [1]₁₂, [2]₁₂, …, [11]₁₂}',
    list: keysOf(12, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    struct: '群',
    groupOp: '+',
    note: '(ℤ₁₂, +) 是群：加法转一圈还在钟面上，[0] 是单位元，[r] 的逆元是 [12 − r]。对 × 不是群：[2] 找不到能乘出 [1] 的卡。',
    desc: '整数除以 12 的余数，一共 12 张卡，像钟面上的 12 个刻度。',
    hint: '把整数 ℤ 整个对 12 取余。',
    has: v => v.n === 12,
    recipes: [
      ['d:Z', 'b:mod', 'c:12'],
      ['c:[1]12', 'm:closure', 'b:add'],
      ['d:N', 'b:mod', 'c:12'],
      ['d:U12', 'm:closure', 'b:add'],
    ],
  },
  {
    id: 'U12',
    short: 'ℤ₁₂ˣ',
    name: '时钟的单位',
    ch: 5,
    type: 'mod:12',
    preview: '{[1]₁₂, [5]₁₂, [7]₁₂, [11]₁₂}',
    list: keysOf(12, [1, 5, 7, 11]),
    struct: '群',
    groupOp: '×',
    note: '(ℤ₁₂ˣ, ×) 是群：和 12 互素的余数才有逆元，它们相乘还是互素。这四张卡每张自己乘自己都是 [1]，叫克莱因四元群。对 + 不封闭：[1] + [1] = [2] 跑出去了。',
    desc: '钟面上能"除"的卡：和 12 没有公因数的余数。',
    hint: '让 ℤ₁₂ 里每张卡都做 1/x，没有倒数的卡会被跳过。',
    has: inSet(12, [1, 5, 7, 11]),
    recipes: [
      ['d:Z12', 'u:recip', null],
      ['c:[1]12', 'b:div', 'd:Z12'],
    ],
  },
  {
    id: 'Sub3',
    short: '⟨3⟩₁₂',
    name: '钟面四等分',
    ch: 5,
    type: 'mod:12',
    preview: '{[0]₁₂, [3]₁₂, [6]₁₂, [9]₁₂}',
    list: keysOf(12, [0, 3, 6, 9]),
    struct: '群',
    groupOp: '+',
    note: '(⟨3⟩₁₂, +) 是群，是 ℤ₁₂ 的子群：3 的倍数相加还是 3 的倍数，[0] 是单位元，[3] 和 [9] 互为逆元。',
    desc: '从 [3] 出发一直加 3，转一圈只停在 4 个刻度上：12 点、3 点、6 点、9 点。',
    hint: '从 [3]₁₂ 出发，用加法封闭。',
    has: inSet(12, [0, 3, 6, 9]),
    recipes: [
      ['c:[3]12', 'm:closure', 'b:add'],
      ['d:Z12', 'b:mul', 'c:[3]12'],
      ['d:Z12', 'b:mul', 'c:3'],
    ],
  },
  {
    id: 'Sub2',
    short: '⟨2⟩₁₂',
    name: '偶数刻度',
    ch: 5,
    type: 'mod:12',
    preview: '{[0]₁₂, [2]₁₂, [4]₁₂, [6]₁₂, [8]₁₂, [10]₁₂}',
    list: keysOf(12, [0, 2, 4, 6, 8, 10]),
    struct: '群',
    groupOp: '+',
    note: '(⟨2⟩₁₂, +) 是群，是 ℤ₁₂ 的子群：偶数加偶数还是偶数，[0] 是单位元。它只有 6 张卡，和 ℤ₆ 长得一样。',
    desc: '偶数对 12 取余，剩下的 6 张卡。',
    hint: '把偶数整个对 12 取余，或者让 ℤ₁₂ 里每张卡都翻倍。',
    has: inSet(12, [0, 2, 4, 6, 8, 10]),
    recipes: [
      ['d:Even', 'b:mod', 'c:12'],
      ['d:Z12', 'u:dbl', null],
      ['c:[2]12', 'm:closure', 'b:add'],
    ],
  },
  {
    id: 'Sub6',
    short: '⟨6⟩₁₂',
    name: '半圈',
    ch: 5,
    type: 'mod:12',
    preview: '{[0]₁₂, [6]₁₂}',
    list: keysOf(12, [0, 6]),
    struct: '群',
    groupOp: '+',
    note: '(⟨6⟩₁₂, +) 是只有两张卡的群：[6] + [6] = [12] = [0]，所以 [6] 的逆元是它自己。它和 {±1}、ℤ₂ 结构一样。',
    desc: '12 点和 6 点，走半圈又回来。',
    hint: '偶数刻度和钟面四等分都有的卡只有两张。',
    has: inSet(12, [0, 6]),
    recipes: [
      ['d:Sub2', 'm:inter', 'd:Sub3'],
      ['c:[6]12', 'm:closure', 'b:add'],
      ['d:Z12', 'b:mul', 'c:6'],
      ['d:Sub3', 'u:dbl', null],
    ],
  },
  {
    id: 'Z7',
    short: 'ℤ₇',
    name: '一周',
    ch: 5,
    type: 'mod:7',
    preview: '{[0]₇, [1]₇, [2]₇, …, [6]₇}',
    list: keysOf(7, [0, 1, 2, 3, 4, 5, 6]),
    struct: '群',
    groupOp: '+',
    note: '(ℤ₇, +) 是群，和 ℤ₁₂ 一样。不一样的是 7 是素数：去掉 [0] 之后，每张卡都能除，所以 ℤ₇ 还是一个"域"。',
    desc: '整数除以 7 的余数，像一周的七天。',
    hint: '把整数 ℤ 整个对 7 取余。',
    has: v => v.n === 7,
    recipes: [
      ['d:Z', 'b:mod', 'c:7'],
      ['c:[1]7', 'm:closure', 'b:add'],
      ['d:U7', 'm:union', 'c:[0]7'],
      ['d:N', 'b:mod', 'c:7'],
    ],
  },
  {
    id: 'U7',
    short: 'ℤ₇ˣ',
    name: '一周的单位',
    ch: 5,
    type: 'mod:7',
    preview: '{[1]₇, [2]₇, [3]₇, [4]₇, [5]₇, [6]₇}',
    list: keysOf(7, [1, 2, 3, 4, 5, 6]),
    struct: '群',
    groupOp: '×',
    note: '(ℤ₇ˣ, ×) 是群：7 是素数，除了 [0] 每张卡都有逆元，[3] 和 [5]、[2] 和 [4] 互逆。从 [3] 出发反复乘 3 能走遍全部 6 张卡，所以它是循环群。',
    desc: 'ℤ₇ 去掉 [0]，剩下的 6 张卡对乘法是群。',
    hint: '让 ℤ₇ 里每张卡都做 1/x；或者从 [3]₇ 出发用乘法封闭。',
    has: inSet(7, [1, 2, 3, 4, 5, 6]),
    recipes: [
      ['d:Z7', 'u:recip', null],
      ['c:[3]7', 'm:closure', 'b:mul'],
      ['c:[1]7', 'b:div', 'd:Z7'],
    ],
  },
  {
    id: 'QR7',
    short: '(ℤ₇ˣ)²',
    name: '模 7 的非零平方数',
    ch: 5,
    type: 'mod:7',
    preview: '{[1]₇, [2]₇, [4]₇}',
    list: keysOf(7, [1, 2, 4]),
    struct: '群',
    groupOp: '×',
    note: '((ℤ₇ˣ)², ×) 是群，是 ℤ₇ˣ 的子群：平方乘平方还是平方，[1] 是单位元，[2] 和 [4] 互为逆元。ℤ₇ˣ 的 6 张卡里恰好一半是平方数。',
    desc: '在模 7 的世界里，除了 [0]（0² = 0），1、2、4 也都是平方数：3² = 9 = [2]，2² = [4]。这里只收 ℤ₇ˣ 里的非零平方数，[0] 不算。',
    hint: '让 ℤ₇ˣ（不含 [0]）里每张卡都做平方；ℤ₇ 整个平方会多出 [0]。',
    has: inSet(7, [1, 2, 4]),
    recipes: [
      ['d:U7', 'u:sq', null],
      ['c:[2]7', 'm:closure', 'b:mul'],
      ['c:[1]7', 'm:extend', 'u:dbl'],
    ],
  },
  {
    id: 'Z2',
    short: 'ℤ₂',
    name: '奇偶',
    ch: 5,
    type: 'mod:2',
    preview: '{[0]₂, [1]₂}',
    list: keysOf(2, [0, 1]),
    struct: '群',
    groupOp: '+',
    note: '(ℤ₂, +) 是最小的钟面：[1] + [1] = [0]，奇数加奇数是偶数。对 × 不是群：[0] 没有逆元。',
    desc: '整数对 2 取余，只剩"偶"和"奇"两张卡。',
    hint: '把整数 ℤ 对 2 取余。ℤ₁₂ 对 2 取余也行：2 整除 12。',
    has: v => v.n === 2,
    recipes: [
      ['d:Z', 'b:mod', 'c:2'],
      ['d:Z12', 'b:mod', 'c:2'],
      ['c:[1]2', 'm:closure', 'b:add'],
    ],
  },
];

export const QUESTS = [
  {
    id: 'mod1',
    ch: 5,
    title: '第一个钟面',
    text: '左边放整数 ℤ，中间放「取余」，右边放 12。整数会按余数缩成 12 张卡。',
    done: has => has('d:Z12'),
  },
  {
    id: 'mod2',
    ch: 5,
    title: '谁能被除',
    text: '让 ℤ₁₂ 里每张卡都做 1/x。没有倒数的卡会被跳过，剩下的就是能"除"的卡。',
    done: has => has('d:U12'),
  },
  {
    id: 'mod3',
    ch: 5,
    title: '集齐钟面',
    text: '打开图鉴，把第五章的卡组都造出来。试试 7 和 2 的钟面，看看和 12 有什么不同。',
    done: has => CATALOG.every(c => has(`d:${c.id}`)),
  },
];

// 从"集齐初等篇 + 本章赠卡（取余、12、7）"出发，集齐本章全部卡组
export const WALKTHROUGH = [
  ['d:Z', 'b:mod', 'c:12', 'd:Z12'],
  ['c:2', 'b:add', 'c:1', 'c:3'],
  ['c:3', 'b:mod', 'c:12', 'c:[3]12'],
  ['c:[3]12', 'm:closure', 'b:add', 'd:Sub3'],
  ['d:Z12', 'u:pow(-1)', null, 'd:U12'],
  ['d:Z12', 'u:aff(2,0)', null, 'd:Sub2'],
  ['d:Sub2', 'm:inter', 'd:Sub3', 'd:Sub6'],
  ['d:Z', 'b:mod', 'c:7', 'd:Z7'],
  ['d:Z7', 'u:pow(-1)', null, 'd:U7'],
  ['d:U7', 'u:pow(2)', null, 'd:QR7'],
  ['d:Z12', 'b:mod', 'c:2', 'd:Z2'],
];
