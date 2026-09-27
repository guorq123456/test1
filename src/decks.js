// 卡组：用"成员判断" has(x) 表示的集合。
//
// 每个卡组有：
//   type    成员的类型：'q'、'mod:12'、'poly'、'vec'、'mat'、'qty'……混合时是 'set'
//   list    有限卡组的成员列表（有的话）
//   elems   在视野里算出来的成员（近似卡组，approx = true）
//   has(x)  true / false / null（超出范围判断不了）
//
// 像"封闭"这种没法精确推算的操作，会在类型的视野（window）里真的算一遍。

import { R, isR, rkey, cmp, height, eq, eqR, isInt, toNum, sub, div, ipow, ONE, OVER, uniqR } from './math.js';
import {
  isV,
  vkey,
  fmtV,
  uniqV,
  cmpV,
  sizeV,
  subtypeOf,
  windowFor,
  binV,
  WINDOW,
  WIN_H,
  sizeCapFor,
  opBudgetFor,
  eqV,
  TYPES,
  baseType,
  MSG_OVER,
  classify,
} from './values.js';
import { applyU, preU, invertU, isQStructural } from './unary.js';

// 三值逻辑的"或"和"且"：null 表示不知道
const or3 = (a, b) => (a === true || b === true ? true : a === null || b === null ? null : false);
const and3 = (a, b) => (a === false || b === false ? false : a === null || b === null ? null : true);

// 展示有理数卡组内容时从这里挑"最简单"的几个数
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
    type: 'set',
    ...extra,
    has(x) {
      if (!isV(x)) return false;
      const k = vkey(x);
      if (cache.has(k)) return cache.get(k);
      const r = has(x);
      const v = r === null ? null : !!r;
      cache.set(k, v);
      return v;
    },
  };
}

function sameType(xs) {
  const t = subtypeOf(xs[0]);
  return xs.every(x => subtypeOf(x) === t) ? t : 'set';
}

export function finiteDeck(xs, name) {
  const list = uniqV(xs).sort(cmpV);
  const keys = new Set(list.map(vkey));
  const type = list.length ? sameType(list) : 'q';
  return mkDeck('finite', x => keys.has(vkey(x)), { list, name, type });
}

// 视野里算出来的卡组。如果结果类型的视野就是全部成员（比如模 12 的余数只有 12 个），那它其实是精确的有限卡组。
function approxDeck(elems, name, type) {
  const list = uniqV(elems).sort(cmpV);
  const t = type ?? (list.length ? sameType(list) : 'set');
  if (list.length && t !== 'set' && exhaustiveType(t)) return finiteDeck(list, name);
  const m = new Map(list.map(x => [vkey(x), x]));
  return mkDeck('approx', x => m.has(vkey(x)), { name, approx: true, elems: list, type: t });
}

function exhaustiveType(sub) {
  const d = TYPES.get(baseType(sub));
  return !!(d && d.exhaustive && d.exhaustive(sub));
}

// 卡组的代表性成员：有限卡组是全部，其他的是视野里的成员
export function sampleOf(D) {
  if (D.list) return D.list;
  if (D.elems) return D.elems;
  if (D.sample) return D.sample();
  return windowFor(D.type).filter(x => D.has(x) === true);
}

// 对卡组里的每张卡做一元算子 f
export function imageDeck(D, f, name) {
  if (D.list) {
    const raw = D.list.map(x => applyU(f, x));
    const outs = raw.filter(isV);
    if (!raw.some(y => y === OVER)) return finiteDeck(outs, name);
    if (!outs.length) {
      const E = finiteDeck([], name);
      E.err = MSG_OVER;
      return E;
    }
    // 有成员算出来太大表示不了：只能当近似卡组，而且比看到的更多（incomplete）
    const P = approxDeck(outs, name);
    P.incomplete = true;
    return P;
  }
  if (D.type === 'q' && isQStructural(f)) {
    // 常数算子、(−1)ˣ 这类原像无穷多的情况，在原卡组的代表成员和视野里找一个原像；找不到只能说"不知道"
    let cands = null;
    return mkDeck(
      'image',
      y => {
        if (!isR(y)) return false;
        const p = preU(f, y);
        if (p.pred) {
          if (!cands) cands = uniqV([...(D.seq ?? []), ...sampleOf(D), ...WINDOW]);
          return cands.some(x => p.pred(x) && D.has(x) === true) ? true : null;
        }
        const hits = p.list.map(x => D.has(x));
        if (hits.includes(true)) return true;
        return p.unknown || hits.includes(null) ? null : false;
      },
      { name, type: 'q', approx: D.approx, src: D, f, sample: () => uniqV(sampleOf(D).map(x => applyU(f, x))) },
    );
  }
  const sample = sampleOf(D);
  const raw = sample.map(x => applyU(f, x));
  const outs = uniqV(raw);
  if (!outs.length) {
    const E = finiteDeck([], name);
    E.err = firstErr(raw);
    return E;
  }
  const type = sameType(outs);
  // f 可逆时可以精确判断：y 在像里 ⇔ f⁻¹(y) 在 D 里
  const g = invertU(f);
  const roundTrips =
    g &&
    !D.approx &&
    sample.every(x => {
      const y = applyU(f, x);
      return !isV(y) || eqV(applyU(g, y), x);
    });
  if (roundTrips) {
    return mkDeck(
      'image',
      y => {
        const x = applyU(g, y);
        return isV(x) && eqV(applyU(f, x), y) ? D.has(x) : false;
      },
      { name, type, src: D, f, sample: () => uniqV(sampleOf(D).map(x => applyU(f, x))) },
    );
  }
  return approxDeck(outs, name, type);
}

// 见证值：这个卡组"边界"上的值。图鉴比对除了固定探针，还会在这些值上比对，
// 这样从 −1025 出发的轨道就不会被当成 ℤ，ℤ + 1/13 也不会被当成空集。
export function witnessesOf(D, depth = 0) {
  if (D.wit) return D.wit;
  let w = [];
  if (D.list) w = D.list;
  else if (D.elems) w = D.elems;
  else if (D.orbit) {
    // 起点、开头几步，以及起点的前一步（它不在轨道里）
    w = [...(D.seq ?? [])];
    const g = invertU(D.orbit.f);
    if (g) {
      const p = applyU(g, D.orbit.c);
      if (isV(p)) w.push(p);
    }
  } else if (D.src) {
    const srcs = Array.isArray(D.src) ? D.src : [D.src];
    const base = srcs.flatMap(S => [...(depth < 3 ? witnessesOf(S, depth + 1) : []), ...sampleOf(S).slice(0, 40)]);
    w = D.f ? base.map(x => applyU(D.f, x)).filter(isV) : base;
  }
  D.wit = uniqV(w).slice(0, 200);
  return D.wit;
}

// 一批运算结果里第一条带解释的错误
function firstErr(results) {
  for (const r of results) if (r && typeof r === 'object' && r.err) return r.err;
  return null;
}

export function unionDeck(A, B, name) {
  if (A.list && B.list) return finiteDeck([...A.list, ...B.list], name);
  const type = A.type === B.type ? A.type : 'set';
  return mkDeck('union', x => or3(A.has(x), B.has(x)), {
    name,
    type,
    approx: A.approx || B.approx,
    src: [A, B],
    sample: () => uniqV([...sampleOf(A), ...sampleOf(B)]),
  });
}

export function interDeck(A, B, name) {
  if (A.list) return finiteDeck(A.list.filter(x => B.has(x) === true), name);
  if (B.list) return finiteDeck(B.list.filter(x => A.has(x) === true), name);
  // 两个不同类型的卡组（数和余数、长度和时间……）没有共同的卡
  if (A.type !== B.type && A.type !== 'set' && B.type !== 'set') return finiteDeck([], name);
  const type = A.type === B.type ? A.type : 'set';
  return mkDeck('inter', x => and3(A.has(x), B.has(x)), {
    name,
    type,
    approx: A.approx || B.approx,
    src: [A, B],
    sample: () => sampleOf(A).filter(x => B.has(x) === true),
  });
}

// a·x + b 的轨道 {c, f(c), f(f(c)), …} 的精确成员判断（有理数）
function affOrbitHas(c, f, y) {
  if (!isR(y)) return false;
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
// W 是底板上的世界（可选）：走出 W 就停下，跑出去的那一步记在 escaped 里
export function orbitDeck(c, f, name, W = null) {
  if (W && W.has(c) === false) {
    const E = finiteDeck([], name);
    E.escaped = [c];
    return E;
  }
  const seq = [c];
  const seen = new Set([vkey(c)]);
  let x = c;
  let open = true;
  let overflow = false;
  let fail = null; // 走到没有定义 / 表示不了的地方：{ kind, x }
  let escaped = null;
  for (let i = 0; i < ORBIT_STEPS; i++) {
    const y = applyU(f, x);
    if (!isV(y)) {
      open = false;
      overflow = y === OVER;
      const kind = classify(y);
      if (!overflow && (kind === 'undefined' || kind === 'unrepresentable')) fail = { kind, x };
      break;
    }
    if (W && W.has(y) === false) {
      open = false;
      escaped = [y];
      break;
    }
    const k = vkey(y);
    if (seen.has(k)) {
      open = false;
      break;
    }
    seen.add(k);
    seq.push(y);
    x = y;
  }
  // 走进了循环，或者走到没有定义的地方停下：有限卡组
  if (!open && !overflow) {
    const F = finiteDeck(seq, name);
    if (fail) F.fail = fail;
    if (escaped) F.escaped = escaped;
    return F;
  }
  const type = sameType(seq);
  const extra = { name, seq: seq.slice(0, 6), type, orbit: { c, f } };
  if (isR(c) && f.t === 'aff' && type === 'q') {
    // 因为太大而停下的轨道，能表示的成员都已经走过了，直接查表，免得公式里的中间量先溢出
    if (overflow) return mkDeck('orbit', y => isR(y) && seen.has(vkey(y)), extra);
    return mkDeck('orbit', y => affOrbitHas(c, f, y), extra);
  }
  // 其他算子：记下走过的每一步。走满步数还没停就标成近似。
  return mkDeck('orbit', y => seen.has(vkey(y)), { ...extra, approx: open, elems: seq });
}

// 封闭：从 D 出发，用 b 反复组合（在视野里算）。
// opts.world：底板上的世界，跑出去的结果不参与组合，记在 escaped 里；
// opts.onFail(kind, x, y)：某一对算不出（没有定义 / 表示不了）时回调
export function closureDeck(D, b, name, opts = {}) {
  const W = opts.world ?? null;
  const fin = !!D.list;
  const seeds0 = sampleOf(D);
  const escaped = new Map();
  const seeds = W ? seeds0.filter(x => W.has(x) !== false) : seeds0;
  if (W) for (const x of seeds0) if (W.has(x) === false && escaped.size < 64) escaped.set(vkey(x), x);
  const cap = sizeCapFor(D.type);
  const budget = opBudgetFor(D.type);
  const hmax = fin ? Math.min(2000, Math.max(cap, 2 * Math.max(1, ...seeds.map(sizeV)))) : cap;
  const all = new Map(seeds.map(x => [vkey(x), x]));
  let frontier = [...all.values()];
  let dropped = false;
  const lost = []; // 算得出但太大、没收进来的结果，比对图鉴时要看一眼
  let ops = 0;
  let rounds = 0;
  let stop = false;
  while (frontier.length && rounds < 12 && !stop) {
    rounds++;
    const cur = [...all.values()];
    const fresh = [];
    const tryAdd = (z, x, y) => {
      if (!isV(z)) {
        if (z === OVER) dropped = true;
        else if (opts.onFail) {
          const kind = classify(z);
          if (kind === 'undefined' || kind === 'unrepresentable') opts.onFail(kind, x, y);
        }
        return;
      }
      if (W && W.has(z) === false) {
        if (escaped.size < 64) escaped.set(vkey(z), z);
        return;
      }
      if (sizeV(z) > hmax) {
        dropped = true;
        if (lost.length < 64) lost.push(z);
        return;
      }
      const k = vkey(z);
      if (!all.has(k)) {
        all.set(k, z);
        fresh.push(z);
      }
    };
    for (const x of frontier) {
      for (const y of cur) {
        tryAdd(binV(b.id, x, y), x, y);
        if (!b.comm) tryAdd(binV(b.id, y, x), y, x);
      }
      ops += cur.length * 2;
      if (ops > budget || all.size > 4000) {
        dropped = true;
        stop = true;
        break;
      }
    }
    frontier = fresh;
  }
  if (frontier.length) dropped = true;
  let out;
  if (fin && !dropped) out = finiteDeck([...all.values()], name);
  else {
    out = approxDeck([...all.values()], name);
    if (dropped) {
      out.truncated = true; // 有些结果因为太大没算进来，"直到得不到新卡"并不成立
      if (lost.length) out.lost = lost;
    }
  }
  if (escaped.size) out.escaped = [...escaped.values()];
  return out;
}

// 两个卡组两两运算：{a ∘ b | a ∈ A, b ∈ B}。onFail(kind, x, y) 在某一对算不出时回调
export function pairwiseDeck(A, b, B, name, onFail = null) {
  // 有一边是空集，结果一定是空集
  if ((A.list && !A.list.length) || (B.list && !B.list.length)) return finiteDeck([], name);
  const fin = !!(A.list && B.list);
  const sa = sampleOf(A);
  const sb = sampleOf(B);
  const out = new Map();
  const lost = [];
  let cap = null;
  let err = null;
  let over = false;
  let dropped = 0;
  for (const x of sa) {
    for (const y of sb) {
      const z = binV(b.id, x, y);
      if (!isV(z)) {
        if (z === OVER) over = true;
        else {
          if (!err && z && typeof z === 'object' && z.err) err = z.err;
          if (onFail) {
            const kind = classify(z);
            if (kind === 'undefined' || kind === 'unrepresentable') onFail(kind, x, y);
          }
        }
        continue;
      }
      if (!fin) {
        if (cap === null) cap = sizeCapFor(subtypeOf(z));
        if (sizeV(z) > cap) {
          dropped++;
          if (lost.length < 64) lost.push(z);
          continue;
        }
      }
      out.set(vkey(z), z);
    }
  }
  // 有结果太大表示不了时，即使两边都有限，也只能当近似卡组
  const D = fin && !over ? finiteDeck([...out.values()], name) : approxDeck([...out.values()], name);
  if (over) D.incomplete = true;
  if (lost.length) D.lost = lost;
  if (!out.size) {
    // 一张都没留下：要么全都算不出（带解释），要么算得出但都超出了视野的大小
    D.err = err ?? (over ? MSG_OVER : null);
    D.dropped = dropped > 0;
  }
  return D;
}

export function sigOf(D, probes) {
  return probes.map(x => ({ true: '1', false: '0', null: '?' })[D.has(x)]).join('');
}

// 卡组内容预览，比如 "{0, 2, 4, 6, 8, …}"
export function previewDeck(D, max = 6) {
  if (D.list) {
    const xs = D.list;
    if (!xs.length) return '{ }';
    if (xs.length <= max + 1) return `{${xs.map(fmtV).join(', ')}}`;
    return `{${xs.slice(0, max).map(fmtV).join(', ')}, …}`;
  }
  if (D.seq && D.seq.length >= 2) return `{${D.seq.slice(0, 5).map(fmtV).join(', ')}, …}`;
  if (D.type !== 'q') {
    const pool = D.elems ?? (D.sample ? uniqV(D.sample()) : [...windowFor(D.type)]).sort((x, y) => sizeV(x) - sizeV(y) || cmpV(x, y));
    const members = [];
    let more = false;
    for (const x of pool) {
      if (D.has(x) !== true) continue;
      if (members.length >= max) {
        more = true;
        break;
      }
      members.push(x);
    }
    if (!members.length) return D.approx ? '{ …（视野外） }' : '{ }';
    return `{${members.map(fmtV).join(', ')}${more || D.truncated ? ', …' : ''}}`;
  }
  // 候选：常见的数，再加上这个卡组自己的代表成员（像 ℤ + 1/13 这种，成员多半不在常见数里）
  const own = D.sample ? D.sample().filter(isR) : [];
  const pool = own.length ? uniqR([...DISPLAY_POOL, ...own]).sort((x, y) => height(x) - height(y) || cmp(x, y)) : DISPLAY_POOL;
  const members = [];
  for (const x of pool) {
    if (D.has(x)) {
      members.push(x);
      if (members.length >= max) break;
    }
  }
  if (!members.length) return D.approx ? '{ …（范围外） }' : '{ }';
  members.sort(cmp);
  const lo = members[0];
  const hi = members[members.length - 1];
  const moreLo = pool.some(x => cmp(x, lo) < 0 && D.has(x));
  const moreHi = D.truncated || pool.some(x => cmp(x, hi) > 0 && D.has(x));
  // 相邻两个成员之间还有没显示的成员时，在中间加省略号（比如 ℤ 经 1/x）
  const parts = [];
  members.forEach((x, i) => {
    if (i > 0 && pool.some(y => cmp(y, members[i - 1]) > 0 && cmp(y, x) < 0 && D.has(y))) parts.push('…');
    parts.push(fmtV(x));
  });
  return `{${moreLo ? '…, ' : ''}${parts.join(', ')}${moreHi ? ', …' : ''}}`;
}

// 有限卡组在 + 和 × 下是不是群（封闭、单位元、逆元）。太大或无限时返回 null。
export function groupInfo(D, ops = ['add', 'mul']) {
  if (!D.list || D.list.length === 0 || D.list.length > 64) return null;
  const xs = D.list;
  const keys = new Set(xs.map(vkey));
  const out = {};
  for (const op of ops) {
    const table = new Map();
    let closed = true;
    for (const a of xs) {
      for (const b of xs) {
        const z = binV(op, a, b);
        if (!isV(z) || !keys.has(vkey(z))) {
          closed = false;
          break;
        }
        table.set(`${vkey(a)}|${vkey(b)}`, vkey(z));
      }
      if (!closed) break;
    }
    let identity = null;
    if (closed) {
      identity =
        xs.find(e => xs.every(a => table.get(`${vkey(e)}|${vkey(a)}`) === vkey(a) && table.get(`${vkey(a)}|${vkey(e)}`) === vkey(a))) ??
        null;
    }
    let inverses = false;
    if (identity) {
      const ek = vkey(identity);
      inverses = xs.every(a => xs.some(b => table.get(`${vkey(a)}|${vkey(b)}`) === ek && table.get(`${vkey(b)}|${vkey(a)}`) === ek));
    }
    out[op] = { closed, identity, inverses, group: closed && !!identity && inverses };
  }
  return out;
}

// ───────────────────────── 分岔：得到 + 缺口 ─────────────────────────
// 每个 *Partition 返回 { got, holes }：got 是成立的那部分（卡组），
// holes 是 [{ kind, where, side? }]，kind ∈ 'undefined' | 'unrepresentable' | 'outside'，where 是卡组。
// 太大（OVER）不算缺口，仍走原来的 incomplete / truncated 提示。

// A ∖ B
export function diffDeck(A, B, name) {
  if (A.list) return finiteDeck(A.list.filter(x => B.has(x) === false), name);
  return mkDeck(
    'diff',
    x => {
      const a = A.has(x);
      if (a === false) return false;
      const b = B.has(x);
      if (b === true) return false;
      return a === null || b === null ? null : true;
    },
    { name, type: A.type, approx: A.approx || B.approx, src: [A, B], sample: () => sampleOf(A).filter(x => B.has(x) === false) },
  );
}

// 看起来一张卡都没有（有限且空，或者代表成员为空）
export function isBlank(D) {
  if (D.list) return D.list.length === 0;
  if (D.elems) return D.elems.length === 0;
  return sampleOf(D).length === 0;
}

// 把结果限制在底板世界里：{ got: D ∩ W, outside: D ∖ W }；没有底板就原样返回
export function restrictToWorld(D, W, name) {
  if (!W) return { got: D, outside: null };
  const got = interDeck(D, W, name);
  got.truncated = D.truncated;
  got.lost = D.lost;
  const outside = diffDeck(D, W, `${name} ∖ ${W.name}`);
  return { got, outside: isBlank(outside) ? null : outside };
}

// 一批走不通的输入做成"卡在哪里"的卡组
function whereDeck(vals, D) {
  if (D.list) return finiteDeck(vals, '');
  const m = new Map(vals.map(x => [vkey(x), x]));
  const list = [...m.values()].sort(cmpV);
  return mkDeck('hole', x => m.has(vkey(x)), { approx: true, elems: list, type: D.type });
}

// 卡组 D 里的每张卡做 f
export function imagePartition(D, f, name, W = null) {
  const got0 = imageDeck(D, f, name);
  const bad = { undefined: [], unrepresentable: [] };
  for (const x of sampleOf(D)) {
    const r = applyU(f, x);
    if (r === OVER) continue;
    const k = classify(r);
    if (k === 'undefined' || k === 'unrepresentable') bad[k].push(x);
  }
  const holes = [];
  for (const k of ['undefined', 'unrepresentable']) {
    if (!bad[k].length) continue;
    const where = D.list
      ? finiteDeck(bad[k], '')
      : mkDeck(
          'hole',
          x => {
            const h = D.has(x);
            if (h !== true) return h;
            const r = applyU(f, x);
            return r !== OVER && classify(r) === k;
          },
          { type: D.type, approx: D.approx, sample: () => bad[k] },
        );
    holes.push({ kind: k, where });
  }
  const { got, outside } = restrictToWorld(got0, W, name);
  if (outside) holes.push({ kind: 'outside', where: outside });
  return { got, holes };
}

// 收集两两运算里算不出的那些对：记在失败值更集中的那一边
function collectFails() {
  const bad = { undefined: { l: new Map(), r: new Map() }, unrepresentable: { l: new Map(), r: new Map() } };
  const onFail = (k, x, y) => {
    bad[k].l.set(vkey(x), x);
    bad[k].r.set(vkey(y), y);
  };
  const holesOf = (A, B) => {
    const holes = [];
    for (const k of ['undefined', 'unrepresentable']) {
      const { l, r } = bad[k];
      if (!l.size) continue;
      const side = r.size <= l.size ? 'r' : 'l';
      const vals = [...(side === 'r' ? r : l).values()];
      holes.push({ kind: k, where: whereDeck(vals, side === 'r' ? B : A), side });
    }
    return holes;
  };
  return { onFail, holesOf };
}

// A 和 B 两两做 b
export function pairwisePartition(A, b, B, name, W = null) {
  const { onFail, holesOf } = collectFails();
  const got0 = pairwiseDeck(A, b, B, name, onFail);
  const holes = holesOf(A, B);
  const { got, outside } = restrictToWorld(got0, W, name);
  if (outside) holes.push({ kind: 'outside', where: outside });
  got.err = got0.err;
  got.dropped = got0.dropped;
  return { got, holes };
}

// 从 D 出发在 b 下封闭（有底板时在底板里进行）
export function closurePartition(D, b, name, W = null) {
  const { onFail, holesOf } = collectFails();
  const got = closureDeck(D, b, name, { world: W, onFail });
  const holes = holesOf(D, D);
  if (got.escaped?.length) holes.push({ kind: 'outside', where: whereDeck(got.escaped, D) });
  return { got, holes };
}

// 从 c 出发反复做 f（有底板时走出底板就停）
export function orbitPartition(c, f, name, W = null) {
  const got = orbitDeck(c, f, name, W);
  const holes = [];
  if (got.fail) holes.push({ kind: got.fail.kind, where: finiteDeck([got.fail.x], '') });
  if (got.escaped?.length) holes.push({ kind: 'outside', where: finiteDeck(got.escaped, '') });
  return { got, holes };
}

// ───────────────────────── 反推与封闭性 ─────────────────────────

// 原像落在哪个类型里：在各类型的视野里试 f，结果落进 T 最多的那个类型（相同时优先 T 的类型）
function domainTypeOf(f, T) {
  const hint = T.type;
  const hits = t => windowFor(t).slice(0, 80).filter(x => T.has(applyU(f, x)) === true).length;
  let best = hint;
  let bestN = hits(hint);
  for (const t of TYPES.keys()) {
    if (t === baseType(hint)) continue;
    const n = hits(t);
    if (n > bestN) {
      best = t;
      bestN = n;
    }
  }
  return { type: best, any: bestN > 0 };
}

// 反推：{ x | f(x) ∈ T }
export function preimageDeck(f, T, name) {
  // 有理数上的结构化算子、有限目标：用原像公式算出精确的有限卡组
  if (T.list && T.type === 'q' && isQStructural(f)) {
    const xs = [];
    let pred = false;
    for (const y of T.list) {
      const p = preU(f, y);
      if (p.pred) {
        pred = true;
        break;
      }
      xs.push(...p.list);
    }
    if (!pred) return finiteDeck(xs, name);
  }
  const { type, any } = domainTypeOf(f, T);
  if (!any && T.list) return finiteDeck([], name);
  const D = mkDeck(
    'preimage',
    x => {
      const y = applyU(f, x);
      if (y === OVER) return null; // 太大算不出，不知道
      return isV(y) ? T.has(y) : false;
    },
    { name, type, approx: T.approx, sample: () => windowFor(type).filter(x => D.has(x) === true) },
  );
  return D;
}

// 法在卡组 K 上封不封闭：law = { t: 'un', f } 或 { t: 'bin', b }
// 返回 { escaped: 跑出 K 的结果, unrep: 有写不出来的结果 }
export function lawClosedOn(K, law, limit = 40) {
  const s = sampleOf(K).slice(0, limit);
  const escaped = new Map();
  let unrep = false;
  const cap = K.approx ? sizeCapFor(K.type) : Infinity;
  const check = z => {
    const c = classify(z);
    if (c === 'unrepresentable' && z !== OVER) unrep = true;
    if (c === 'ok' && sizeV(z) <= cap && K.has(z) === false && escaped.size < 64) escaped.set(vkey(z), z);
  };
  if (law.t === 'un') for (const x of s) check(applyU(law.f, x));
  else {
    const s2 = s.slice(0, 24);
    for (const x of s2) for (const y of s2) check(binV(law.b.id, x, y));
  }
  return { escaped: [...escaped.values()], unrep };
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

export { WIN_H, WINDOW };
